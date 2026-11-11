---
description: Review corrections Autosave Learn has captured and turn them into rules
---

Review the corrections that Autosave Learn has captured.

If the argument is `status`: run `python3 ~/.claude/hooks/learn.py status`, show the output verbatim, and stop.

Otherwise:

1. Run `python3 ~/.claude/hooks/learn.py pending`. Type the path exactly as written, unquoted.
   If it reports a damaged state file that was set aside, tell the user that first.
2. If nothing is pending, say so and stop.
3. Group pending corrections that are about the same thing. Propose at most 3 rules.
   Each rule is one line, at most 200 characters, does not start with `#`, and contains no `@path`.
   Quote the correction or corrections behind each rule.
4. If a pending correction repeats a live rule, list it as a candidate repeat and name the rule.
5. Ask the user about each proposal, one at a time:
   - New rule: ask exactly `Save this as a rule?`
   - Candidate repeat: ask exactly `Count as a repeat of rule N?` (N is the rule id)
6. Act on each answer, with the key shown in the listing:
   - Yes to a new rule: `python3 ~/.claude/hooks/learn.py approve --key K --text 'RULE'`
   - Yes to a repeat: `python3 ~/.claude/hooks/learn.py repeat --key K --rule N`
   - No: `python3 ~/.claude/hooks/learn.py dismiss --key K`
   Relay the command output. If a command refuses (for example the 15-rule cap), show its message and let the user decide.
7. Put the rule text in single quotes; write a single quote inside it as `'\''`. Never use double quotes: the shell would run backticks inside them.
8. If `pending` lists failed rules, offer one rewrite for each. On yes, approve the rewrite as a new rule with the key shown for that failed rule (`approve --key K --text 'RULE'`).
9. A rule that covers several corrections is approved against one key. Dismiss or repeat the other keys explicitly, only if the user says so.

Never edit `~/.claude/learn/` or `~/.claude/rules/learned-rules.md` by hand.
