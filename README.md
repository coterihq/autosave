# Autosave for Claude Code

A tested operating layer for Claude Code: safety hooks that block common forms of risky
commands (pattern-based, not a sandbox), compaction and handoff tooling so long sessions don't lose the plot, a
spend/pace guard, a standing-rules system that stays in sync with CLAUDE.md, slash
commands for routine ops, and 25 evidence-first engineering skills.

Everything installs into `~/.claude` with one command. Existing files are backed up
before they are touched, and re-running the installer changes nothing.

Autosave is an independent project. It is not affiliated with or endorsed by Anthropic.

- Install: see [QUICKSTART.md](QUICKSTART.md)
- Make it yours: see [CUSTOMIZE.md](CUSTOMIZE.md)

Requirements: Claude Code, Python 3.9+, bash. Tested on macOS (zsh). Linux should work but is untested.

## How the pieces fit

```
 you ──► Claude Code ──► PreToolUse ─► guard.py (block) / bash_output_cap.py (warn)
                │        PostToolUse ─► migration_check.py
                │        PreCompact ──► precompact_dump.py ─┐
                │        SessionStart ► session_inject.py ◄─┘ (state/session-critical.md)
                │        Stop ────────► footer_check.py, usage_guard.py ─► handoffs/
                │        statusLine ──► usage_statusline.py
                └── reads CLAUDE.md ◄── check_rule_sync.py ◄── rules/standing-rules.md
```

## Hooks (`hooks/`)

| Hook | Event | What it does | Why |
|---|---|---|---|
| `guard.py` | PreToolUse (Write/Edit, Bash, MCP `apply_migration`) | Blocks: edits or shell writes to `.env*` (examples/templates allowed); live-mode toggles (`DRY_RUN=false`, `*TESTNET=false`, `*DRY_RUN=false`, quoted values such as `DRY_RUN="false"`, and `--live` / `--live=1` followed by a space, `;`, `&`, `|`, `)` or the end; a config file changed with an editor tool is not covered); `supabase db reset/push` against a linked project, plus any project wrapper you list in `CLAUDE_GUARD_DB_WRAPPERS`; Supabase MCP `apply_migration`; `rm -rf` on `/`, `~`, `$HOME`, their `/*`, or `~/.claude`. Quoted text (a grep pattern, a commit message) is not treated as a use. Also blocks two self-fixable shell bugs: a wait loop that greps the process table and matches itself forever, and, when your shell is zsh, an unquoted multi-value `$var` (zsh does not word-split, so the command silently acts on nothing). The `DRY_RUN`/`TESTNET`/`--live` and Supabase rules only fire if you use those; they never get in the way otherwise. | An exit code 2 stops the call no matter what the model decides. Fails open on parse errors, and every hook command exits 0 if its file is missing, so a broken or deleted guard never blocks a session. |
| `guard_tests.py` | manual / installer | 58 regression cases for `guard.py`; each block must fail for the intended reason. | Run after editing the guard. |
| `bash_output_cap.py` | PreToolUse (Bash) | Warns (never blocks) when a likely-huge command (`cat`, `rg`, `git log`, `curl`...) has no `head`/`tail`/`wc`/`LIMIT`. | Every byte of output is re-read on each turn; this is the cheapest context saving there is. |
| `migration_check.py` | PostToolUse | After writing `supabase/migrations/*.sql`, flags any `CREATE TABLE/VIEW/FUNCTION` without a matching `GRANT`. | RLS alone does not expose objects to PostgREST; missing GRANTs cause 42501 errors in prod. Harmless if you don't use Supabase. |
| `precompact_dump.py` | PreCompact | Injects non-negotiable preservation instructions into the compaction prompt and logs the event. | Survival rules fire even when CLAUDE.md has been drowned out. |
| `session_inject.py` | SessionStart (compact, resume) | Re-injects `docs/ai/state/session-critical.md` (project) or `~/.claude/state/session-critical.md`, with a staleness warning past 24h. | Compaction silently drops objectives; this puts them back mechanically. |
| `footer_check.py` | Stop | When enabled (off by default; `FOOTER_DISABLE=0` turns it on). When on, substantive replies (>1200 chars) must include a "Tooling rec:" line; it nudges once and never loops. Each nudge costs one extra turn. | Surfaces the commands/skills you already own instead of letting them rot. |
| `usage_guard.py` | Stop | Estimates spend from local transcripts into `~/.claude/usage/ledger.json`, computes pace vs budget, warns at 0.8x, recommends dropping a model tier at 1.0x, and above 150k context writes one deterministic handoff to `~/.claude/handoffs/`. | Keeps you inside plan limits and turns long sessions into clean restarts. |
| `usage_statusline.py` | statusLine | `model · pace · $spent/$budget · ctx` | Live pace without asking. |
| `usage_digest.py` | cron (optional) | Weekly markdown digest: spend, pace, spend by tier, top 3 sessions. `--notes` also posts to Apple Notes on macOS. | Feeds `/claude-audit`. |
| `check_rule_sync.py` | manual / cron / installer | Compares `rules/standing-rules.md` with the generated block in `CLAUDE.md`; on drift writes `RULE_SYNC_DRIFT.md`; `--fix` regenerates the block. Prints a short sha256 you can pin elsewhere. | One source of truth for rules across surfaces. |
| `check_allow_wildcards.py` | cron (optional) | Flags Bash allow rules with a `*` before the end of the command in `~/.claude/settings*.json` and your projects' `.claude/settings*.json`; writes `LOOSE_ALLOW_RULES.md` and exits 1. Never edits settings. | A mid-command `*` silently auto-approves whatever options land there. |

Spend figures are API-equivalent estimates from a PRICES table in `usage_guard.py`.
The rates are list prices at release time: verify them against current Anthropic
pricing before trusting dollar amounts.

## Rules (`rules/`)

- `standing-rules.md`: the canonical list of always-on rules (execution honesty,
  decision-first answers, confidence %, tooling rec/pre-flight, cost pressure,
  handoffs, guard etiquette, optional GitHub auto-merge). Edit this file, never the
  generated block in CLAUDE.md.
- `workflow.md`: universal engineering workflow (honesty about execution, before
  editing, scope discipline, end-of-session review, context and compaction protocol,
  eval feedback loop, content neutrality).
- `templates/session-critical.template.md`: the state file the compaction hooks
  preserve. Copy into `docs/ai/state/session-critical.md` per project.
- `templates/content-policy.template.md`: a path-scoped rule for products that
  have an explicit content policy.

`CLAUDE.md.template` is installed only if you have no `~/.claude/CLAUDE.md`. If you
do, the installer appends just the standing-rules marker block.

## Commands (`commands/`)

| Command | What it does |
|---|---|
| `/handoff` | Writes a dense handoff (objective, decisions, validation state, next action, dated data) to `~/.claude/handoffs/` and prints it. |
| `/preflight` | Blast radius, invariants and rollback before a prod-adjacent change; reports risk -> mitigation -> done. |
| `/postmortem` | Turns an incident into a regression eval via the `incident-to-eval` skill. |
| `/claude-audit` | Weekly: attribute usage, review hook hits, make exactly one targeted change, measure before/after. |
| `/dormant` | Factual table of projects under your projects dir with last-touched dates. |
| `/make-chart`, `/make-doc`, `/make-deck`, `/make-diagram`, `/make-sheet` | Router commands: restate the deliverable, pick the right skill or format, ask at most 3 questions, verify by looking, save to your output dir. They mention optional skills (Anthropic document skills, Artifacts, dataviz); remove routes you don't have. |
| `/make-image` | Picks a route for an image: a local or connected image model, a designed layout, or hand-written SVG (always available); never generates charts of real data. |

## Skills (`skills/`)

Each skill has a contract (inputs, artifact, exit gate, verdict format), a fast path,
numbered steps, escalation and stop rules. Edits, migrations, deploys and external
writes start only after the approver records a go; findings alone never authorize change.

| Router skills | Routes to |
|---|---|
| `system-correctness` | A wrong or untrusted number, behavior or permission -> one specialist below. |
| `change-control` | A consequential change (multi-agent, rollout, drift, unproven plan) -> one specialist. |
| `journey-quality` | A user journey that feels wrong -> one of the UX specialists. |

| Specialist | Use when |
|---|---|
| `assumption-breaker` | About to build a plausible but unproven solution: rank assumptions by blast radius, run the smallest discriminating test. |
| `change-impact-recon` | Editing shared logic/schemas: consumer impact map, invariants, focused regression set. |
| `context-loss-recovery` | After compaction/drift/handoff: invalidate stale plans, cold-start check. |
| `release-and-recovery-rehearsal` | Consequential rollout: success signals, rehearsed recovery on non-prod, bounded release. |
| `incident-to-immunity` | Bug fixed: sibling scan for the same mechanism, one narrow prevention rule or "no rule". |
| `incident-to-eval` | Turn a real mistake into a regression eval case. |
| `outcome-validation` | After shipping: did the objective actually happen (not just "merged")? |
| `evidence-gate` | Go/no-go: each criterion -> pass/fail/unknown with evidence, one verdict. |
| `evidence-conflict-resolution` | Code, runtime, docs or agents disagree: contradiction table, resolved findings. |
| `cross-layer-contract-repair` | Each layer passes alone but the system fails between them. |
| `truth-to-screen-trace` | A displayed value may not match its source: provenance and discrepancy table. |
| `state-machine-hardening` | Happy path works; retries, interruptions, partial states don't. |
| `security-boundary-proof` | Identity, permissions, private data or external actions: authority matrix, abuse cases, denial tests. |
| `performance-bottleneck-proof` | Slow: baseline, critical path, one isolated intervention, before/after. |
| `architecture-simplification` | Every change touches too many places: one seam from real change history, or "don't abstract yet". |
| `simplify-or-delete` | Redundant tools/settings/nav: a subtraction plan. |
| `decision-flow-surgery` | The app has the information but shows it in the wrong order. |
| `buried-capability-recovery` | Powerful features exist but users don't meet them when needed. |
| `session-handoff` | Write or consume a handoff block across sessions or surfaces. |
| `prior-work` | Before planning or building: find existing plans, specs, handoffs, decisions and rejected approaches, so nothing is rebuilt. |
| `status` | Factual status of the current repo: where things stand, what's open, what's stale. |
| `skill-trigger-test` | Check that an installed skill fires on the right prompts and stays quiet on near-misses (recall and false-trigger rate). |

Some skills mention other public skills (e.g. `superpowers:*`, `engineering:*`) in
their "Not for" lines; those are pointers, not dependencies.

## Files the kit creates at runtime

`~/.claude/handoffs/` (handoffs), `~/.claude/state/` (session-critical fallback,
compaction breadcrumb, audit log), `~/.claude/usage/` (ledger, digests),
`~/.claude/RULE_SYNC_DRIFT.md` (only on drift), `~/.claude/backups/autosave-*`
(installer backups).

## Uninstall

1. Restore `settings.json` and `CLAUDE.md` from the newest
   `~/.claude/backups/autosave-*` folder (it mirrors `~/.claude` paths), or remove
   the kit's hook entries from `~/.claude/settings.json` by hand.
2. Delete the files listed in `~/.claude/.autosave-manifest.json`, then the
   manifest itself. Skills and commands keep loading until you do.

Either order is safe: a hook whose file is gone exits 0 and lets the call through.

## More from Coteri

Code Red ($9) adds plan red-teaming and a reviewed parallel-agent coordination workflow; Quick Save ($5) checks that the served build contains the commit you shipped. Both at https://coterihq.gumroad.com.

## License

MIT, © 2026 Coteri. Free to use, modify and share. See [LICENSE](LICENSE) and [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md).
