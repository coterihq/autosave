# Changelog

## 1.2.1 — 2026-11-09

- `guard.py`: the live-mode block now catches quoted values (`DRY_RUN="false"`, `TESTNET='0'`), prefixed names (`BOT_DRY_RUN=false`), and `--live` followed by `;`, `&`, `|`, `)` or `=1`. `--live=false`, `DRY_RUN="true"` and quoted mentions still pass. A config file changed with an editor tool is still not covered.
- `guard_tests.py`: 58 cases (12 new for the above).

## 1.2.0 — 2026-11-09

Correctness release: every claim the kit makes about itself is now true and tested.

- `bash_output_cap.py`: the warning now reaches Claude (`additionalContext`); before, it only reached you.
- `usage_guard.py`: counts each assistant message once (Claude Code repeats a message's usage across transcript lines, which inflated spend about 3x).
- `usage_guard.py`: includes subagent transcripts in the session cost.
- `usage_guard.py`: per-model list prices (Sonnet 5.x, Opus 5.5, Fable/Mythos 5, Haiku 5.5) and 1-hour cache writes at 2x; measured within 4% of Claude Code's own session cost.
- `usage_guard.py`: ledger writes are atomic; a corrupt ledger is set aside once instead of erroring every turn.
- `usage_statusline.py`: shows Claude Code's own session cost and context %, with the transcript estimate as fallback.
- `guard_tests.py`: 46 cases, now covering Write/Edit/MultiEdit on `.env` and Supabase MCP `apply_migration`.
- New `tests/hooks_test.py` and `tests/claims_test.py`.
- Docs: the guard is described as pattern-based, not a sandbox; the footer check is marked optional; QUICKSTART notes that the two rules files never auto-update once yours differ; skills point to `/preflight` instead of an agent this kit doesn't ship.
- Standing rules: `usage_guard.py` warns, it does not enforce.

Earlier versions: see git history.
