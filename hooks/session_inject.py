#!/usr/bin/env python3
"""SessionStart hook (matchers: compact, resume): re-inject session-critical
state so compaction never silently drops the objective/invariants.
Looks for project-local docs/ai/state/session-critical.md first (cwd),
falls back to ~/.claude/state/session-critical.md. Prints to stdout ->
Claude Code injects it as context. Silent no-op if neither exists."""
import os, sys, time

CANDIDATES = [
    os.path.join(os.getcwd(), "docs", "ai", "state", "session-critical.md"),
    os.path.expanduser("~/.claude/state/session-critical.md"),
]

for p in CANDIDATES:
    if os.path.isfile(p):
        try:
            body = open(p).read().strip()
        except Exception:
            continue
        if not body:
            continue
        age_h = (time.time() - os.path.getmtime(p)) / 3600
        stale = " [WARNING: >24h old — verify before trusting]" if age_h > 24 else ""
        print(f"## Re-injected session-critical state ({p}, "
              f"{age_h:.1f}h old){stale}\n\n{body}\n\n"
              "Re-read relevant path-scoped rules before continuing "
              "implementation. Confirm the objective and next action still hold.")
        sys.exit(0)
sys.exit(0)
