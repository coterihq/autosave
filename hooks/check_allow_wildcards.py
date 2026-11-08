#!/usr/bin/env python3
"""Scheduled check (e.g. nightly cron, see QUICKSTART). Flags Bash allow rules
with a '*' before the end of the command - Claude Code treats it as a wildcard,
so extra options at that spot are auto-approved. Flag only; never edits settings.
Loose rules -> writes ~/.claude/LOOSE_ALLOW_RULES.md and exits 1. Clean -> removes
the flag, exits 0."""
import glob, json, os, re, sys

HOME = os.path.expanduser("~")
FLAG = f"{HOME}/.claude/LOOSE_ALLOW_RULES.md"
# Project settings are read from CLAUDE_PROJECTS_DIR (default: PROJECTS_DIR from kit.conf).
PROJECTS = os.path.expanduser(os.getenv("CLAUDE_PROJECTS_DIR", "{{PROJECTS_DIR}}"))
files = sorted(set(
    glob.glob(f"{HOME}/.claude/settings*.json")
    + glob.glob(f"{PROJECTS}/*/.claude/settings*.json")
    + glob.glob(f"{PROJECTS}/*/*/.claude/settings*.json")))

def loose(rule):
    m = re.match(r"Bash\((.*)\)$", rule, re.S)
    return bool(m) and "*" in re.sub(r"(:\*| \*|\*)$", "", m.group(1))

hits = []
for f in files:
    try:
        allow = json.load(open(f)).get("permissions", {}).get("allow", [])
    except Exception as e:
        hits.append((f, f"UNREADABLE JSON: {e}"))
        continue
    hits += [(f, r) for r in allow if loose(r)]

if not hits:
    if os.path.exists(FLAG):
        os.remove(FLAG)
    print(f"allow rules clean ({len(files)} files)")
    sys.exit(0)

lines = [f"- `{f.replace(HOME, '~')}`: {r[:160]}" for f, r in hits]
open(FLAG, "w").write(
    "# LOOSE ALLOW RULES (detected by check_allow_wildcards.py)\n\n"
    f"{len(hits)} Bash allow rule(s) have a '*' mid-command, so extra options "
    "there are auto-approved. Usually stale one-off approvals; remove them "
    "(keep a .bak) or replace '*' with the exact value.\n\n" + "\n".join(lines) + "\n")
print(f"LOOSE — {len(hits)} rule(s); flag written to {FLAG}", file=sys.stderr)
sys.exit(1)
