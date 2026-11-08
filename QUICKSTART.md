# Quickstart (5 minutes)

## 1. Configure

```bash
cd claude-ops-starter-kit   # from the zip; a git clone is claude-code-ops-kit
cp config.example kit.conf
```

Open `kit.conf` and set at least:

- `USER_NAME` and `APPROVER`: your name (who Claude asks before risky actions).
- `PROJECTS_DIR`, `EVALS_DIR`, `OUTPUT_DIR`: where your projects, evals and
  generated files live.
- `MONTHLY_BUDGET_USD` and `CYCLE`: your spend budget per cycle (API-equivalent
  dollars). If you are on a subscription plan, set it to roughly the estimated
  spend at which you last hit your limit.

Skipping this step is fine: defaults are used ("the user", ~/projects, $200/month).

## 2. Preview, then install

```bash
./install.sh --dry-run   # shows every file it would add or change; writes nothing
./install.sh             # installs into ~/.claude
```

What happens:

- Hooks, commands, skills and rules are copied into `~/.claude`. Any existing
  file that differs is first copied to `~/.claude/backups/starter-kit-<time>/`.
- Your own files are never replaced: if you already have a hook, command, skill or
  rule file with the same name as one of the kit's, yours is kept and the kit version
  is written beside it as `*.kit-new`. Files the kit installed earlier are updated
  in place (after a backup).
- `CLAUDE.md` is created from the template if you have none; otherwise only a
  standing-rules block is appended (after a backup).
- `settings.json` is merged, never replaced: missing env keys, hook entries and
  the status line are added; your existing settings stay.
- The guard self-test runs and should print `N/N pass`.

Re-running `./install.sh` is safe; with nothing changed it reports "0 new, 0 updated".
Use `--no-settings` to wire hooks yourself. Set `CLAUDE_DIR=/path` to install
somewhere other than `~/.claude` (handy for a trial run in a temp folder).

## 3. Restart Claude Code and check

- Run `/hooks` and confirm the PreToolUse, PostToolUse, PreCompact, SessionStart
  and Stop entries are listed.
- The status line shows `model · pace · $spent/$budget · ctx`.
- Ask Claude to run `echo X=1 >> .env`. It should be blocked by guard.py.
- Type `/handoff` to save a handoff to `~/.claude/handoffs/`.

## 4. Optional extras

- Weekly digest (cron, Sundays 18:05):
  `5 18 * * 0 python3 ~/.claude/hooks/usage_digest.py`
- Nightly rule-sync check: `0 3 * * * python3 ~/.claude/hooks/check_rule_sync.py`
- Nightly loose-permission check: `25 3 * * * python3 ~/.claude/hooks/check_allow_wildcards.py`
  (flags Bash allow rules with a `*` mid-command; reads `CLAUDE_PROJECTS_DIR`)
- Per project: copy `~/.claude/rules/templates/session-critical.template.md` to
  `docs/ai/state/session-critical.md` and keep it current before `/compact`.

Next: [CUSTOMIZE.md](CUSTOMIZE.md).
