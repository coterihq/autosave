---
description: Mark your previous reply as wrong and offer to save a rule
---

The user says your previous reply was wrong. The argument, if any, says what should change.

1. If there is no argument, ask the user what should change. Otherwise use the argument.
2. Fix the previous reply accordingly.
3. Then ask exactly `Save this as a rule?` and quote one proposed rule: one line, at most 200 characters, not starting with `#`, no `@path`.
4. Wait for the answer. The user's answer is the only grade.
5. On yes: run `python3 ~/.claude/hooks/learn.py pending` (path unquoted), find this correction, then run `python3 ~/.claude/hooks/learn.py approve --key K --text "RULE"`. If the listing shows a live rule this correction breaks, ask exactly `Count as a repeat of rule N?` instead and on yes run `python3 ~/.claude/hooks/learn.py repeat --key K --rule N`.
6. On no: run `python3 ~/.claude/hooks/learn.py dismiss --key K`.
