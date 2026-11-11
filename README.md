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
| `learn.py` | UserPromptSubmit, Stop, SessionStart (startup) | Off by default. Records messages that open with a correction phrase, offers to save one as a rule, and writes approved rules to `~/.claude/rules/learned-rules.md`. See the Learn section. | Keeps your corrections from being lost between sessions. |
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
| `/learn` | Lists captured corrections, proposes up to 3 rules, and saves, counts or dismisses each one only on your answer. `/learn status` shows every rule with its receipts. Needs Learn switched on. |
| `/bad` | Marks the previous reply as wrong, fixes it, and asks `Save this as a rule?`. |
| `/make-chart`, `/make-doc`, `/make-deck`, `/make-diagram`, `/make-sheet` | Router commands: restate the deliverable, pick the right skill or format, ask at most 3 questions, verify by looking, save to your output dir. They mention optional skills (Anthropic document skills, Artifacts, dataviz); remove routes you don't have. |
| `/make-image` | Picks a route for an image: a local or connected image model, a designed layout, or hand-written SVG (always available); never generates charts of real data. |

## Learn (off by default)

Learn keeps your corrections. When a message of yours opens with a correction phrase ("no", "wrong", "undo", "revert", "not that"), Learn records it with the reply it answered. You decide whether it becomes a rule. Approved rules go into `~/.claude/rules/learned-rules.md`, which Claude Code loads at session start. Every rule keeps the corrections it came from as receipts.

Learn is OFF by default. Three switches in `kit.conf`:

- `LEARN="on"` turns it on (`CLAUDE_LEARN` in `settings.json`).
- `LEARN_MODE` is `moment` (the default) or `batch` (`CLAUDE_LEARN_MODE`). In moment mode Claude fixes the issue and then asks `Save this as a rule?`, or `Count as a repeat of rule N?` if the correction breaks a listed rule. In batch mode nothing is asked mid-session; corrections pile up and you review them with `/learn`. Batch mode shows a one-line reminder at session start once 3 or more are waiting, at most once a day. That reminder is best effort: another tool's startup message can displace it. `/learn` always lists everything pending.
- `LEARN_TRIAL_DAYS` (default 14) is how many active days a new rule stays on trial before it is labelled held (`CLAUDE_LEARN_TRIAL_DAYS`).

`kit.conf` is read when you run `install.sh`, and the installer only adds missing keys to an existing `~/.claude/settings.json`. If you installed before and later set `LEARN="on"` in `kit.conf`, rerunning the installer will not change the value already in `settings.json`. Set `"CLAUDE_LEARN": "on"` in the `env` block of `~/.claude/settings.json` yourself, then restart Claude Code. The same goes for the other two switches.

Commands: `/learn` reviews pending corrections and proposes at most 3 rules, each quoting its corrections. `/learn status` lists every rule with its state, days in that state, repeats and receipts. `/bad` marks the previous reply as wrong, has Claude fix it, and asks `Save this as a rule?`. Your yes or no is the only grade.

A rule is one line of at most 200 characters, cannot start with `#`, and cannot contain an `@path` (Claude Code would read it as a file import). There is a cap of 15 live rules. A rule that you confirm as repeated twice is marked failed and removed from the rules file. A rule with fewer than two repeats after the trial days is labelled "no repeat seen since <date>". That label is all Learn claims: it does not say the rule helped.

Limits:

- If you rarely correct Claude, nearly every rule will end as "no repeat seen", because there are too few events for a repeat to show. For you Learn is a ledger of corrections with receipts.
- Detection looks only at how a message opens, in English. Corrections phrased differently are not seen, and some messages that open with "no" are not corrections.
- Claude Code's built-in memory may save the same correction on its own, so a rule can overlap with it.
- Rules load at session start. Other sessions that are already open pick up a rule change after they restart or compact.
- The model that made the mistake also suggests whether it was one and whether a repeat matches. Check what it proposes before you say yes.

Each approval runs `python3 ~/.claude/hooks/learn.py`, which shows a permission prompt unless you allow it. To skip the prompt, add this to the `permissions.allow` list in `~/.claude/settings.json`, with your own home directory:

```
Bash(python3 /Users/you/.claude/hooks/learn.py:*)
```

Privacy: for each correction Learn stores the first 200 characters of your message and of Claude's reply before it. Text that looks like a credential (common key, token and password shapes) is replaced by `[redacted]`; this is a pattern list, not a guarantee. Everything stays on your machine in `~/.claude/learn/learn.json` (mode 600), with a copy in `learn.json.bak`.

To remove Learn by hand: delete the three `learn.py` entries from `UserPromptSubmit`, `Stop` and `SessionStart` in `~/.claude/settings.json`, delete `~/.claude/rules/learned-rules.md` and the `~/.claude/learn/` folder, and optionally remove the `CLAUDE_LEARN*` keys from the `env` block. Setting `CLAUDE_LEARN` to anything but `on` also stops all recording and offers.

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
`~/.claude/learn/` and `~/.claude/rules/learned-rules.md` (only when Learn is on),
`~/.claude/RULE_SYNC_DRIFT.md` (only on drift), `~/.claude/backups/autosave-*`
(installer backups).

## Uninstall

1. Restore `settings.json` and `CLAUDE.md` from the newest
   `~/.claude/backups/autosave-*` folder (it mirrors `~/.claude` paths), or remove
   the kit's hook entries from `~/.claude/settings.json` by hand.
2. Delete the files listed in `~/.claude/.autosave-manifest.json`, then the
   manifest itself. Skills and commands keep loading until you do.
3. If you used Learn, also delete `~/.claude/rules/learned-rules.md` and `~/.claude/learn/`
   (the manifest does not list them).

Either order is safe: a hook whose file is gone exits 0 and lets the call through.

## More from Coteri

Code Red ($9) adds plan red-teaming and a reviewed parallel-agent coordination workflow; Quick Save ($5) checks that the served build contains the commit you shipped. Both at https://coterihq.gumroad.com.

## License

MIT, © 2026 Coteri. Free to use, modify and share. See [LICENSE](LICENSE) and [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md).
