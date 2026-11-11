# Customize

## The rule system in one minute

- **Standing rules** (always on, short): edit `~/.claude/rules/standing-rules.md`,
  then run `python3 ~/.claude/hooks/check_rule_sync.py --fix` to regenerate the
  block in `~/.claude/CLAUDE.md`. Never edit the generated block directly; the
  nightly check flags drift in `~/.claude/RULE_SYNC_DRIFT.md`.
- **Area rules** (only for some files): put them in `<project>/.claude/rules/<area>.md`
  with a `paths:` front-matter list, like `rules/templates/content-policy.template.md`.
- **Hard controls** (must never happen): a rule Claude can ignore is advice. If
  breaking it would be costly, add a check to `hooks/guard.py`, add a test case to
  `hooks/guard_tests.py`, and run it.
- **Repeatable workflows**: a skill in `~/.claude/skills/<name>/SKILL.md` or a
  command in `~/.claude/commands/<name>.md`.

Good rules are specific, checkable and say what to do instead. One line each.

## Example 1: a standing rule (behavior)

Add to `rules/standing-rules.md`:

```markdown
- Tests first for bug fixes: before changing code for a reported bug, write a
  failing test that reproduces it and show it failing; then fix and show it passing.
  If the bug cannot be reproduced in a test, say why before editing.
```

Then: `python3 ~/.claude/hooks/check_rule_sync.py --fix`

## Example 2: an area rule (scoped to some paths)

Create `<project>/.claude/rules/api.md`:

```markdown
---
paths:
  - "src/api/**"
  - "app/api/**"
---
# API rules
- Every new endpoint validates input with the shared schema module (src/lib/schema.ts);
  never hand-parse request bodies.
- Error responses use { error: { code, message } }; never leak stack traces.
- Any endpoint that writes data needs an auth check test that calls it as an
  unauthorized user and expects 401/403.
```

It loads only when Claude works on matching files, so it costs nothing elsewhere.

## Example 3: a hard control (hook-enforced)

Block force-pushes to main. In `hooks/guard.py`, inside the `if tool == "Bash":`
block, after rule 4:

```python
    # 4b. Force-push to a protected branch
    if re.search(r"\bgit\s+push\b[^|;&\n]*(--force\b|--force-with-lease\b|\s-f\b)", cmd) and \
       re.search(r"\b(main|master|production)\b", cmd):
        deny("force-push to a protected branch.")
```

Add test cases to `cases` in `hooks/guard_tests.py`:

```python
 (2, "force-push", 'git push --force origin main'),
 (0, None, 'git push origin feature/x'),
```

Run `python3 ~/.claude/hooks/guard_tests.py` and expect all cases to pass. Mirror
the rule in `standing-rules.md` so Claude knows why it is blocked.

## Other knobs

| Want | Change |
|---|---|
| Different approver name in block messages | `CLAUDE_KIT_APPROVER` in `settings.json` env |
| Budget, weekly cycle, context threshold | `CLAUDE_MONTHLY_BUDGET_USD`, `CLAUDE_CYCLE`, `CLAUDE_CONTEXT_WARN_TOKENS` |
| Prices for the spend estimate | `PRICES` table at the top of `hooks/usage_guard.py` |
| Footer line (off by default) | `CLAUDE_FOOTER_DISABLE=0` to turn it on; `CLAUDE_FOOTER_MARKER`, `CLAUDE_FOOTER_MIN_CHARS` |
| Learn (off by default) | `CLAUDE_LEARN=on`, `CLAUDE_LEARN_MODE` (`moment` or `batch`), `CLAUDE_LEARN_TRIAL_DAYS` in `settings.json` env; see the README Learn section |
| Extra invariants kept through compaction | `CLAUDE_KIT_INVARIANTS` (one line) |
| Your own prod-DB wrapper scripts blocked | `CLAUDE_GUARD_DB_WRAPPERS` (regex) |
| Turn a hook off | remove its entry from `~/.claude/settings.json` (or run `/hooks`) |

After any change to rules, hooks or skills, run `/claude-audit` style before/after
checks: changes should be measured, not felt.
