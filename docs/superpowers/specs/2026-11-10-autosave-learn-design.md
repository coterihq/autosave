# Autosave Learn: rules from corrections, with receipts

Status: design rev 2.1, 2026-11-10. Rev 1 was red-teamed by an independent
reviewer (verdict: Revise; 3 critical, 7 high). This revision applies those
fixes. No code yet.
Target: Autosave v1.3, free tier. Ships enabled only if the kill criterion
below passes.

## Purpose

When a user corrects Claude Code, offer to turn that correction into a standing
rule. Every rule keeps the corrections that created it (its receipts) and is
removed on its second confirmed repeat. No setup beyond the existing Autosave
install.

For: Claude Code users who already run Autosave. Not for claude.ai chat users.

## What it does not claim

It does not prove a rule works. One heavy user's last 30 days held 41
correction-opening messages in 10,363 user turns (0.4 per 100, about a third of
them not real corrections), so no single rule gets enough events to show a
falling rate. The design only disproves: a rule fails on its second confirmed
repeat. A rule that survives is labelled "no repeat seen in 14 active days".

In the Learn section of the README, the listing and all Learn output, the
words "proven" and "works" are not used about a rule.

For a user at a tenth of that volume, nearly every rule will end "held"
(chance of two repeats in 14 days is about 0.2%). For them Learn is a ledger of
corrections with receipts, not a verdict machine. The README says so.

## Non-goals

- No cron, no background model call, no API key, no network, no database.
- No code imported from agentmind. Only the method is reused.
- No per-project rules in v1 (each correction records its project path).
- No `/good` command: nothing would read it.
- English-only, opening-phrase detector in v1.

## Hook behaviour: checked 2026-11-10

Rev 1 got Claude Code's hook behaviour wrong from memory. Checked against
code.claude.com/docs/en/hooks and /memory, and against a real transcript:

| # | Claim | Result |
|---|---|---|
| 1 | UserPromptSubmit stdin has no message uuid | Confirmed. It does carry `prompt_id`, and transcript user rows carry the same value as `promptId` (42 of 42 rows in one session) |
| 2 | The transcript may lag | Confirmed: "written asynchronously and may lag" |
| 3 | UserPromptSubmit fires for non-typed prompts | Confirmed: scheduled tasks, background subagent reports, other sessions. Also fires for slash commands. Inside a subagent the input carries `agent_id` |
| 4 | SessionStart stdout goes to the model; `startup` matcher exists | Confirmed |
| 5 | `~/.claude/rules/*.md` loads with no import | Confirmed in practice (a session loaded three rules files, one in a subfolder, that no import names). Docs: loaded at launch. Reload after compaction: not stated |
| 6 | `/bad` is recognisable in the transcript | Confirmed: the row is a string holding `<command-name>/bad</command-name>` and `<command-args>`, with `origin.kind = human` |

Live tests run 2026-11-10 (Claude Code 2.1.322, throwaway hooks loaded with
`--settings`, headless `claude -p`):

- Hooks fire in headless runs: SessionStart (`source: startup`),
  UserPromptSubmit and Stop all ran. Stop's input also carries `prompt_id`
  (same value as UserPromptSubmit) and `last_assistant_message`. The headless
  prompt's transcript row has `origin: null` and `promptSource: sdk`, so the
  recorder's `origin.kind = human` filter excludes it.
- A Bash call to a script is denied without an allow rule (interactively: a
  permission prompt). With `Bash(python3 <path>/learn_stub.py:*)` it ran, but
  only when the command was typed with the path unquoted; the same command
  with the path in double quotes was still denied. So the injected line and
  `commands/learn.md` give the exact unquoted command to run, and the allow
  rule is optional: without it each approval shows one permission prompt.

Interactive check, 2026-11-10: a SessionStart hook that prints
`{"systemMessage": ...}` CAN be shown to the user, as
`SessionStart:startup says: <text>` (claude-mem's launcher does exactly this
and its line was displayed). Our own test hook ran in the same session
(logged) and printed the same JSON shape, but its line was not displayed.
Cause not established; the likeliest reading is that when several hooks send
a message at session start, not all are shown. So the batch nudge is
best-effort on a machine with other session-start messages. Batch mode is not
the default, `/learn` always shows the pending count, and the dogfood run
records whether the nudge was ever seen.

## Structure

One recorder, one offerer. The split in rev 1 (two hooks both storing
corrections) caused duplicates, a "no" loop and non-human captures.

| Piece | Job |
|---|---|
| Stop hook → `learn.py record` | The only writer of corrections. Reads the session's transcript rows |
| UserPromptSubmit hook → `learn.py offer` | Injects the offer line in moment mode. Never writes the ledger |
| SessionStart (`startup`) hook → `learn.py nudge` | Batch-mode reminder as a `systemMessage` |
| `commands/learn.md` | `/learn` review; `/learn status` |
| `commands/bad.md` | `/bad [note]` |

`learn.py` subcommands (11): `record`, `offer`, `nudge`, `pending`, `approve`,
`dismiss`, `repeat`, `edit`, `retire`, `export`, `status`.

Generated, never shipped in the kit and never in the install manifest (a
shipped copy would be overwritten on every reinstall):
- `~/.claude/rules/learned-rules.md`, written whole by `export`. Loads
  automatically; no import line is added to `CLAUDE.md`.
- `~/.claude/learn/learn.json`, mode 600. All durable state.
- `~/.claude/learn/offer-<session_id>.json`. Per-session offer state, so the
  prompt hook never contends for the main file.

Rev 2.1 corrections, found when reading the code for the plan:
- Nothing is imported from `usage_guard.py`: its load and save are tied to its
  own file and schema, and it has no typed-turn filter. `learn.py` carries its
  own small load, quarantine and save, following the same pattern.
- `guard.py` has no credential-shape check to reuse; `learn.py` has its own
  short pattern list.
- The kit registers a hook as one script with no arguments, so `learn.py` run
  without arguments dispatches on `hook_event_name`. `record`, `offer` and
  `nudge` are internal handlers, not subcommands; the CLI has the other eight.
- Switch names carry the kit's prefix: `CLAUDE_LEARN`, `CLAUDE_LEARN_MODE`,
  `CLAUDE_LEARN_TRIAL_DAYS`, set from `LEARN*` keys in `kit.conf`.
- The Stop handler closes an open offer when Claude's reply did not contain
  the exact question, so a false detection cannot swallow the next real
  correction.

## Data (`learn.json`)

```
corrections[]: key, ts, session_id, project_path, text (first 200 chars),
               prev_reply (first 200 chars of the assistant message before it),
               source (detector | bad),
               state (pending | ruled | repeat | dismissed), rule_id?
rules[]:       id, text (max 200 chars), created,
               state (trial | held | failed | retired),
               trial_start, receipts [keys], repeats [keys]
active_days[]: ISO dates with at least one real user turn
last_nudge:    ISO date
```

- `key` is the transcript row's `promptId` (the hook's `prompt_id`), or
  sha1(session_id + text) when a row has none.
- Text matching `learn.py`'s credential patterns is stored as `[redacted]`.

## Recorder (`record`, on Stop, both modes)

1. Read the current session's transcript rows. Keep real user turns only:
   `origin.kind` is `human`, not meta, not sidechain, not tool results, not
   injected text.
2. A kept turn is a correction when it opens with: no (not "no problem" / "no
   worries"), nope, wrong, undo, revert, redo, not that, that's not; or when
   it is a `/bad` invocation (source `bad`).
3. Skip any turn whose `promptId` is in this session's offer file as a
   consumed answer.
4. Insert corrections whose `key` is new. Re-running on the same transcript
   adds nothing. A row the transcript had not flushed yet is picked up by the
   next Stop.
5. Add today to `active_days` if a kept turn exists and today is absent.
6. Promote any trial rule with `LEARN_TRIAL_DAYS` (default 14) active days
   since `trial_start` and fewer than two repeats to held, then `export`.

All of 4 to 6 happen inside one `fcntl.flock` on `learn.lock` (read, change,
atomic replace, one `.bak`). The file is only rewritten when something changed.

## Offerer (`offer`, on UserPromptSubmit, moment mode only)

- Input carries `agent_id` (a subagent): exit, inject nothing.
- Offer file says an offer is open: record this prompt's `prompt_id` as a
  consumed answer, close the offer, inject nothing. This is what stops a "no"
  answer from being detected as a new correction.
- Otherwise, if the prompt opens with a detector phrase: mark an offer open and
  inject one line. The line says: fix the issue first; then, only if this
  message corrected your own work, either ask once whether to save a rule
  (quoting the correction) or, if it breaks a live rule, ask once "count as a
  repeat of rule N?"; if it was not a correction of your work, say nothing
  about rules.
- The hook also fires on non-typed prompts. A false injection costs one line
  of context and records nothing, because only the recorder stores and it
  filters by origin.

On the user's answer Claude runs `learn.py approve --key K --text "..."`,
`learn.py repeat --key K --rule N`, or `learn.py dismiss --key K`.

## Batch mode (`LEARN_MODE=batch`)

No injection. `nudge` runs on session start and, when 3 or more corrections are
pending and `last_nudge` is not today, emits a `systemMessage`: "N corrections
to review, run /learn".

## `/learn` and `/bad`

- `/learn`: Claude reads `pending` (each with its `prev_reply`), proposes up to
  3 rules with quoted receipts, lists candidate repeats of live rules, and asks
  the user to approve, skip or confirm each. A rule may come from a single
  correction; approval is the gate.
- `/learn status`: per rule: text, state, days in state, receipts, repeats.
- `/bad [note]`: tells Claude the previous reply was wrong, to ask what should
  change, and then to offer a rule. The recorder stores it from the transcript;
  no subcommand is needed.
- `edit` changes a rule's text and resets its trial. `retire` removes a live
  rule at the user's request.

## Verdicts and cap

- trial → held: step 6 of the recorder.
- trial or held → failed: second confirmed repeat. Removed from
  `learned-rules.md`, receipts kept, `/learn` offers one rewrite as a new rule.
- At most 15 live rules (trial + held). `approve` refuses a 16th and prints the
  live list, oldest held first. Nothing is evicted automatically.

## Switches

`LEARN` (default off until the kill criterion passes, then on), `LEARN_MODE`
(`moment` default, or `batch`), `LEARN_TRIAL_DAYS` (14; a guess, hence a knob).
Read from the environment, documented in `config.example` beside the existing
Autosave variables. `LEARN=off` makes every Learn hook exit at once.

## Installer and release bookkeeping

- Add `hooks/learn.py`, `commands/learn.md`, `commands/bad.md` to the manifest
  and three hook entries to `settings.template.json`.
- Run `learn.py export` at the end of install when `learn.json` exists.
- README: Learn section, the overlap with built-in memory, an optional exact
  allow rule for `learn.py` (without it each approval shows a permission
  prompt), and manual uninstall steps (remove the three hook entries, delete
  `~/.claude/rules/learned-rules.md` and `~/.claude/learn/`).
- Update `release/free-files.txt`, the counts checked by
  `tests/claims_test.py`, and `CHANGELOG.md`.

## Failure handling

- Every Learn hook exits 0 on any error.
- A `learn.json` that fails to parse is quarantined (renamed aside), a new
  one is started, and `/learn` reports it.
- `learned-rules.md` is regenerated whole on every state change; its header
  says hand edits are overwritten.

## Tests (`tests/hooks_test.py`, tmp dirs, dates passed in, no sleeping)

1. Detector: each phrase matches; "no problem", "no worries" do not.
2. Recorder keeps typed user turns only: a fixture with tool results, meta,
   sidechain, scheduled and agent-report rows (one opening "No issues")
   yields zero corrections and zero active days from those rows.
3. `record` twice on the same transcript adds nothing the second time.
4. `/bad` row is stored with source `bad` and the preceding reply snippet.
5. Offer: detector prompt opens an offer and emits the line; the next prompt
   "no" is consumed, emits nothing, and `record` does not store it.
6. `LEARN=off`: every subcommand run as a hook emits nothing and writes
   nothing. Batch mode: `offer` emits nothing.
7. Nudge: silent at 2 pending, `systemMessage` at 3, silent again that day.
8. `approve` writes the rule on trial; text over 200 chars is refused.
9. 14 active days and under two repeats gives held; 13 does not.
10. First repeat keeps the rule; second sets failed and removes its line.
11. `edit` on a held rule resets it to trial.
12. Cap: 16th approval refused; succeeds after `retire`.
13. Two processes calling `record` on different sessions at once lose no
    correction.
14. Credential-shaped text is stored as `[redacted]`; file mode is 600.
15. Corrupt `learn.json` is quarantined and reported.
16. Reinstall leaves `learned-rules.md` and `learn.json` unchanged;
    `tests/upgrade_test.sh` and `tests/claims_test.py` pass.

Not unit-testable: whether Claude obeys the injected line and asks once. Only
the dogfood run measures it.

## Kill criterion (30 days on the author's machine, `LEARN=on`)

All four, read from `learn.json` by `learn.py status --kill`:

1. At least 5 rules approved.
2. Offer acceptance at least 30%: ruled / (ruled + dismissed) among
   detector-sourced corrections.
3. At least 1 confirmed repeat recorded (the disproving path was used).
4. Zero quarantined ledgers and zero duplicate correction keys.

Any miss: Learn stays off by default and is cut from the v1.3 listing.

## Known limits

- The model that erred also suggests whether it erred and whether a repeat
  matches. The user's yes or no is the only grade.
- Rules load at session start, so an approval or removal reaches other running
  sessions only after they restart or compact.
- Built-in Claude Code memory may save the same correction as a feedback note.
- A clean active day says little if the rule was never relevant that day.
- 15 rules of up to 200 characters cost roughly 400 to 600 tokens per session.
