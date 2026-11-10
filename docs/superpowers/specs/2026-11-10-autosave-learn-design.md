# Autosave Learn: rules from corrections, with receipts

Status: design approved in brainstorm + grill 2026-11-10. No code yet.
Target: Autosave v1.3, free tier. Ships only if the kill criterion below passes.

## Purpose

When a user corrects Claude Code, offer to turn that correction into a standing
rule. Every rule keeps the corrections that created it (its receipts) and is
removed when the same correction happens again. Zero setup beyond the existing
Autosave install.

For: Claude Code users who already run Autosave. Not for claude.ai chat users.

## What it does not claim

It does not prove a rule works. One heavy user's last 30 days held 41
correction-opening messages in 10,363 user turns (0.4 per 100), so no single
rule gets enough events to show a falling rate. The design therefore only
disproves: a rule fails on its second confirmed repeat. A rule that survives is
labelled "no repeat seen in 14 active days". The words "proven" and "works" do
not appear in the UI, README or listing.

## Non-goals

- No cron, no background model call, no API key, no network, no database.
- No code imported from agentmind. Only the method is reused (versioned rules,
  a gate, receipts).
- No per-project rules in v1 (each correction records its project path so a
  split can be added later).
- No `/good` command: nothing would read it.
- English-only detector in v1 (stated in README).

## Files

| File | Job |
|---|---|
| `hooks/learn.py` | One stdlib Python file. Subcommands: `prompt`, `scan`, `pending`, `approve`, `repeat`, `bad`, `retire`, `export`, `status` |
| `commands/learn.md` | `/learn`: review pending corrections and candidate repeats; `/learn status` prints the ledger |
| `commands/bad.md` | `/bad [note]`: record the previous assistant reply as corrected, whatever the detector saw |
| `rules/learned-rules.md` | Generated from the ledger by `learn.py export`. Never hand-edited |
| `~/.claude/learn/ledger.json` | All state: corrections and rules |

Installer changes: register three hook entries in `settings.template.json`
(UserPromptSubmit `prompt`, Stop `scan`, SessionStart nudge), add one
`@~/.claude/rules/learned-rules.md` import line to `CLAUDE.md` (idempotent),
add the files to the manifest. Uninstall removes the import line and the hooks
and keeps the ledger.

## Data

```
correction: id (message uuid), ts, session_id, project_path, text (first 200 chars),
            source (detector | bad), state (pending | ruled | repeat | dismissed), rule_id?
rule:       id, text, created, state (trial | held | failed | retired),
            trial_start, receipts [correction ids], repeats [correction ids]
```

A rule's text may be edited at approval. Editing it later resets `trial_start`.

## Detector

A user turn is a candidate correction when it opens with one of: no (not "no
problem" / "no worries"), nope, wrong, undo, revert, redo, not that, that's not.
Tool results, meta turns and injected text are not user turns. About a third of
matches are the user answering a question or changing direction, so a detector
match never creates or fails a rule by itself: a person confirms every step.

## Flow

Two capture modes, `LEARN_MODE=moment` (default) or `batch`. `LEARN=off`
disables every Learn hook.

**Moment mode.** A UserPromptSubmit hook runs `learn.py prompt`. On a detector
match it stores the correction and injects one line of context: fix the issue
first; then, only if this message corrected your own work, either (a) ask once
whether to save a rule, quoting the correction, or (b) if it breaks a live
rule, ask once "count as a repeat of rule N?". Claude calls `learn.py approve`
or `learn.py repeat` on a yes, and marks the correction dismissed on a no.

**Batch mode.** A Stop hook runs `learn.py scan` on the current transcript and
stores new corrections (deduplicated by message uuid). At session start, when 3
or more are pending, one line is printed: "N corrections to review, run
/learn". At most once per day.

**`/learn` (both modes).** Claude reads `learn.py pending`, proposes up to 3
rules with their quoted corrections, lists candidate repeats of live rules, and
asks the user to approve, skip or confirm each. A rule may be offered from a
single correction; the user's approval is the gate.

**Verdicts.**
- trial → held: 14 active days since `trial_start` with no confirmed repeat.
  An active day is a calendar day with at least one real user turn in any
  session. The UserPromptSubmit hook runs on every prompt in both modes and
  records today's date in the ledger's `active_days`, so no transcript scan is
  needed. `LEARN_TRIAL_DAYS` (default 14) is a knob because 14 is a guess.
- trial or held → failed: second confirmed repeat. The rule is removed from
  `learned-rules.md`; its receipts stay in the ledger; `/learn` offers one
  rewrite, which starts a new rule with a new trial.

**Cap.** At most 15 live rules (trial + held). A 16th approval is blocked and
`/learn` shows the live list, oldest held first, so the user retires one.
Nothing is evicted automatically.

**`/learn status`.** One block per rule: text, state, days in state, receipts
(quoted), repeat count.

## Failure handling

- Every Learn hook exits 0 on any error, like every other Autosave hook.
- Ledger writes go to a temp file then `os.replace`, keeping one `.bak`.
- A ledger that fails to parse is renamed `ledger.corrupt-<ts>.json`, a new
  empty one is started, and `/learn` says so. It is never silently reset.
- `learned-rules.md` is regenerated whole on every state change, so a hand
  edit is overwritten; the file header says this.

## Tests (added to `tests/hooks_test.py`, tmp dirs only)

1. Detector: each opening phrase matches; "no problem", "no worries", tool
   results and meta turns do not.
2. `prompt` on a match stores one correction and emits the context line; on a
   non-match emits nothing; `LEARN=off` emits nothing.
3. `scan` twice on the same transcript adds nothing the second time.
4. Batch nudge: silent at 2 pending, one line at 3, silent again the same day.
5. `approve` writes the rule to `learned-rules.md` marked on trial.
6. 14 active days with no repeat gives held; 13 does not; days with no user
   turn do not count.
7. First repeat keeps the rule; second sets failed and removes its line.
8. Editing a held rule's text resets it to trial.
9. Cap: the 16th approval is refused; after `retire`, it succeeds.
10. Corrupt ledger is moved aside and reported.
11. Installer adds the import line once; a second run changes nothing;
    `tests/upgrade_test.sh` still passes.

## Kill criterion

The code merges with `LEARN` defaulting to off; the author sets `LEARN=on` and
runs it for 30 days. v1.3 flips the default to on only if at least 5 rules were approved and at
least 1 reached a verdict (held or failed). Otherwise remove it from v1.3.

## Known limits

- Built-in Claude Code memory may save the same correction as a feedback note.
  Accepted; README says the two can overlap.
- A clean active day says little if the rule was never relevant that day.
  "No repeat seen" is the strongest statement the data supports.
- Repeat matching is Claude's suggestion plus the user's yes or no. Nothing
  matches automatically.
