---
name: skill-trigger-test
description: Use to check whether an already-installed skill fires on the right prompts and stays out of near-misses (recall and false-trigger rate), e.g. "does assumption-breaker trigger correctly", "test the skill's triggers". Not for new, uninstalled skills; use skill-creator's description loop for those.
---

# Skill Trigger Test

Runs each prompt through `claude -p` and records whether the first turn calls `Skill(<name>)`. Works on installed skills, where skill-creator's loop reports 0% (it looks for a temp copy and the real skill wins).

## Steps
1. Build or reuse an eval set: `[{"query": "...", "should_trigger": true|false}]`. About 10 positives and 10–20 near-miss negatives that share the skill's words but need something else. Store it in the skill's workspace.
2. Run in the background (it's slow and uses usage): `python3 ~/.claude/skills/skill-trigger-test/scripts/probe.py --skill <name> --eval-set <file> --runs 1 --workers 4 --out <workspace>/trigger-<date>`
3. Report recall and false triggers with n, then classify every miss by cause (plan or input not present, phrasing, another skill won, Claude answered directly).
4. Change a description only if the new version keeps false triggers at 0 on the same set; rerun all prompts, not just the failures. Keep any other installed copy (e.g. a claude.ai-synced one) in sync.

## Limits
- First turn only: a skill called after a Bash or ToolSearch step is not seen.
- Single runs are noisy. Use `--runs 3` before trusting a small difference.
- A duplicate copy with the same name counts as a hit (`name` or `*:name`).
