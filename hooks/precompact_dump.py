#!/usr/bin/env python3
"""PreCompact hook: mechanically inject preservation instructions into the
compaction prompt (stdout -> summarizer) and breadcrumb the event. Removes
instruction-dependence: survival rules fire even if CLAUDE.md was drowned.
Add your own invariants with CLAUDE_KIT_INVARIANTS (one line, in settings.json env)."""
import json, os, sys, time

try:
    data = json.load(sys.stdin)
except Exception:
    data = {}

extra = os.getenv("CLAUDE_KIT_INVARIANTS", "").strip()
print("""COMPACTION PRESERVATION REQUIREMENTS (mechanical, non-negotiable):
Preserve verbatim in the summary:
- The complete current objective and acceptance criteria.
- Every file modified this session (paths) and uncommitted work.
- Commands run, their outcomes, and unresolved failures/blockers.
- Decisions made, assumptions, and active invariants""" + (f" ({extra})" if extra else "") + """.
- The exact next concrete action.
After compaction, re-read docs/ai/state/session-critical.md (or
~/.claude/state/session-critical.md) before continuing implementation.""")

bc = os.path.expanduser("~/.claude/state/last_compaction.txt")
os.makedirs(os.path.dirname(bc), exist_ok=True)
with open(bc, "w") as f:
    f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} cwd={os.getcwd()} "
            f"session={data.get('session_id','?')}\n")
sys.exit(0)
