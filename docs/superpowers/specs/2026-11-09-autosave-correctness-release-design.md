# Autosave correctness release — design spec

Date: 2026-11-09 · Status: design approved by Phil (ship-flow stage 1) · Path: architectural
Target repo: Phil's local Autosave source (the folder that builds `autosave.zip`). Commit this spec on the stage-4 worktree branch at `docs/superpowers/specs/2026-11-09-autosave-correctness-release-design.md`.

## Goal
Every claim Autosave makes about itself is true and tested, so the free kit can be the credible front door for Code Red ($9) and Quick Save ($5).

## Success condition (observable)
- Worked: `python3 hooks/guard_tests.py`, `bash tests/upgrade_test.sh`, `python3 tests/hooks_test.py`, `python3 tests/claims_test.py` all pass on macOS/zsh; spend estimate for one real session within ±10% of the statusline's `cost.total_cost_usd` for that session.
- Did not work: any suite fails, or a README/rules claim is disproved by `grep`/`ls`.

## Baseline (capture at stage 4 before editing)
- README says 27 skills (actual 25) and 20 guard cases (actual 41).
- `bash_output_cap.py` emits `systemMessage` only.
- Spend estimate vs native cost for one existing session (record both numbers).

## Scope
### A. Hook output channels
1. `hooks/bash_output_cap.py`: emit `{"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": "<msg>"}}` so Claude receives it. Keep never-blocking behavior.
2. `hooks/precompact_dump.py`: keep the breadcrumb write; remove the preservation-prompt stdout and its claim (README L38). Docs: PreCompact stdout is not added to Claude's context.
3. `hooks/session_inject.py`: on the `compact` source, print the preservation checklist (objective + criteria, files, commands + results, decisions/invariants incl. `CLAUDE_KIT_INVARIANTS`, next action) before the session-critical body. Print the checklist even if no session-critical file exists.
4. `rules/standing-rules.md` cost-pressure line: "usage_guard.py warns you" instead of "Enforced by".

### B. Usage accuracy
1. `hooks/usage_statusline.py`: use input `cost.total_cost_usd` for the live session and `context_window.used_percentage` (fall back to transcript parse if absent).
2. `hooks/usage_guard.py::session_stats`: count each assistant message once, keyed by `message.id` + `requestId` (keep last). Include subagent transcripts if present in the session's folder (path confirmed at 3b).
3. Ledger: write via temp file + `os.replace`. Unreadable ledger: rename to `ledger.json.corrupt-<ts>` and start fresh; never error every turn.

### C. Tests
1. `hooks/guard_tests.py`: support `tool_name`/`tool_input` per case; add Write/Edit/MultiEdit on `.env` (block), `.env.example` (allow), `mcp__supabase__apply_migration` (block).
2. New `tests/hooks_test.py` (stdlib only): output-cap JSON shape; dedupe on a fixture transcript with a repeated message; ledger corruption recovery; statusline from fixture input; session_inject compact output contains the checklist.
3. New `tests/claims_test.py`: count `skills/*/SKILL.md` and guard cases; assert README numbers match; assert no `migration-auditor` string remains.

### D. Docs and claims
- README: 25 skills; guard case count; "blocks common forms (pattern-based, not a sandbox)" replaces "cannot talk its way past"; footer rule "when enabled (off by default)".
- `standing-rules.md` L13–14 footer line: "(Optional: hooks/footer_check.py, off by default.)"
- Replace `migration-auditor` with `/preflight` in guard.py L218–221 and 4 skills.
- QUICKSTART L32–35: note `rules/standing-rules.md` and `rules/workflow.md` never auto-update; newer versions land as `.kit-new`.
- Cross-links (one line each): Code Red in `skills/change-control` L35–36 and README; Quick Save in `skills/evidence-gate` and `skills/outcome-validation` where "served SHA" is mentioned.

### E. Release
- Version bump + CHANGELOG entry listing each fix.
- Rebuild `autosave.zip` (exclude kit.conf, caches).
- Phil uploads to Gumroad manually (publish = irreversible; not automated).

## Grill decisions (stage 2, Phil 2026-11-09)
Repo facts (14:30 PT): source `~/PROJECTS/claude-ops-starter-kit` = main, clean, no remote, 27 skills, README says 27 / "20 cases" (actual 41). Free tree = `~/PROJECTS/claude-code-ops-kit-public` (`coterihq/autosave`), main = origin, 25 skills, README already 25 / 41; untracked `release/` (build_free.py zips THIS repo from `release/free-files.txt`, 64 entries). `allow_auto_merge` = false on coterihq/autosave. `migration-auditor` in guard.py + 4 skills (source).
1. Where: branch + PR on `coterihq/autosave`; same diff applied to source via `git apply` on a local source branch. Commit `release/` in the PR. (Q1a/Q7a)
2. Auto-merge: Phil enables "Allow auto-merge" on coterihq/autosave before stage 8. (Q2a)
3. Claims test runs against the free tree; counts skills from the manifest; fails if any file under skills/, hooks/, tests/ is missing from `free-files.txt`. (Q3a/Q8a)
4. Release: v1.2, file `autosave.zip` (stable name); new `VERSION` + `CHANGELOG.md`; both + new tests + fixtures added to the manifest. (Q4a/Q8a)
5. Phil's live `~/.claude/hooks`: out of scope; follow-up after stage 9 if 3b confirms the dedupe bug (pace baseline may be inflated). (Q5a)
6. Spend check: headless `claude -p "<small task, spawns a subagent>" --output-format json` → `total_cost_usd` vs `session_stats` on that transcript, ±10%; plus structural check: no duplicate `message.id` usage counted. No live settings.json edits. (Q6a+c/Q9a)
Baseline correction: the "README says 27 / 20" items apply to the source repo; the free tree already reads 25 / 41.

## Stage 3b results (2026-11-09)
- #1 Verified (docs). #2 Verified: 28 usage lines / 9 distinct messages in a local transcript (~3.1x overcount). #3 Verified: `<session>/subagents/agent-*.jsonl`, no id overlap with main. #4 fields Verified; subagent inclusion in native cost undocumented (Task 9 measures both).
- A2/A3 DROPPED (Phil): docs say PreCompact stdout "becomes instructions for the compaction summary", so README L38 is true.

## Out of scope
New guards, secret scanning, plugin packaging, Linux/Windows support, Code Red/Quick Save code changes.

## Assumptions to test at stage 3b
| # | Claim | Wasted if false | Cheapest check |
|---|---|---|---|
| 1 | PreToolUse supports `hookSpecificOutput.additionalContext` | A1 | Read PreToolUse section of code.claude.com/docs/en/hooks; one live run |
| 2 | Transcripts repeat usage across lines for one message | B2 dedupe | Count duplicate `message.id` in one local transcript |
| 3 | Subagent transcripts live under the session folder | B2 subagents | `ls ~/.claude/projects/*/<session>/` |
| 4 | Statusline input includes `cost.total_cost_usd` (verified in docs 2026-11-09) | B1 | One live statusline dump |

## Error handling
All hooks keep fail-open behavior: parse or I/O errors exit 0 and never block a session.

## Risks
- Dedupe key wrong → undercount. Mitigation: B success check vs native cost.
- additionalContext adds tokens per Bash call. Mitigation: message ≤ 1 line; only on uncapped big commands.
