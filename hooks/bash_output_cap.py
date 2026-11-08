#!/usr/bin/env python3
"""PreToolUse(Bash): warn (never block) when a likely-large-output command has no output cap."""
import json, re, sys

BIG = re.compile(r"(^|[\s;&|(])(cat|less|grep\s+-r|rg|find|git\s+(log|diff|show)|psql|sqlite3|"
                 r"curl|jq|ls\s+-R|tree|npm\s+(ls|test)|pytest|docker\s+logs|journalctl|tail\s+-f)\b")
CAP = re.compile(r"\|\s*(head|tail|wc|grep\s+-c|cut|sort\s+.*\|\s*head)|--max-count|-m\s*\d|"
                 r"\bLIMIT\s+\d|-n\s*\d|--oneline|--stat|--shortstat|>\s*\S|-q\b|--quiet")

try:
    cmd = (json.load(sys.stdin).get("tool_input") or {}).get("command", "")
    if BIG.search(cmd) and not CAP.search(cmd):
        print(json.dumps({"systemMessage":
            "[bash_output_cap] No output cap on a likely-large command. "
            "Add | head -50, | tail -50, | wc -l, or LIMIT — every byte stays in context and is re-read each turn."}))
except Exception:
    pass
