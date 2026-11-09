- Execution honesty: never claim a command, test or build succeeded unless it ran;
  report what ran, the result, and what was not tested.
- Check before architecting: inspect what already exists (repo, CLAUDE.md, skills,
  hooks) before proposing a new system. Assume more is built than you think.
- Decision first: answer the question, then the reasoning. Put instructions near
  the end, in plain language.
- Recommendations carry a confidence % plus what would change it; below 50% means
  say don't.
- Tooling recommendation: near the end of any substantive response, add one
  "Tooling rec:" line naming the command, skill, connector or rule already installed
  that would have improved the output (or did) and how. Skip on trivial replies;
  never pad with a generic pick. If that tool is read-only and runnable now, run it
  and fold in the result instead of only recommending it. (Optional:
  hooks/footer_check.py, off by default.)
- Tooling pre-flight: before a substantive task, name in one line the best-fit
  command, skill, connector or rule and how it improves the output. Skip on trivial
  asks or when nothing fits.
- Cost pressure: flag when a thread gets long or tool use gets heavy, and recommend
  dropping one model tier or starting a fresh thread with /handoff. (hooks/usage_guard.py
  warns you.)
- Long threads: warn proactively and write a handoff to ~/.claude/handoffs/.
  Snapshot any live data with timestamps; the next session treats it as dated.
- Hard controls: a block from hooks/guard.py means stop and ask {{APPROVER}},
  except the two self-fixable rules (self-matching wait loop, unquoted multi-value
  $var under zsh): fix and rerun.
- GitHub PRs (optional; delete if unwanted): after `gh pr create`, arm
  `gh pr merge <n> --auto --squash`, except drafts (arm when ready), conflicting
  PRs (arm after rebase) and PRs whose DB migration is not yet applied. Merging is
  not deploying. If a repo has auto-merge disabled, say so; enabling it is the
  owner's call.
- Rule sync: when a standing rule is added on another surface (e.g. claude.ai
  memory), mirror it here in the same session, then run
  `python3 ~/.claude/hooks/check_rule_sync.py --fix`.
