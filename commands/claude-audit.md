---
description: Weekly usage audit; attribute burn, make one targeted change
---

1. Run /usage (and read the latest ~/.claude/usage/digest-*.md if present).
   Identify the top 3 consumers (skill / subagent / plugin / MCP server).
2. Classify each: high value keep | high value but verbose (isolate,
   compact, or narrow scope) | low value (remove/disable/replace).
3. Review hook hits this week: false positives (blocked good work)
   and misses (bug classes that got through with no hook or eval).
4. Propose EXACTLY ONE targeted change (measurement -> friction signal ->
   one change -> regression eval). Not zero, not three.
5. Run the eval suite in {{EVALS_DIR}} and `python3 ~/.claude/hooks/guard_tests.py`
   before AND after applying it.
6. Record the change + eval results in ~/.claude/state/audit-log.md
   (append, dated). The goal is completed work per unit of context, not
   lower usage.
