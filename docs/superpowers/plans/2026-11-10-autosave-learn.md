# Autosave Learn Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add "Learn" to Autosave: corrections of Claude become approved standing rules that keep their receipts and are removed on the second confirmed repeat.

**Architecture:** One stdlib file, `hooks/learn.py`. Run with no arguments it is a hook and dispatches on `hook_event_name` (Stop records, UserPromptSubmit offers, SessionStart nudges). Run with a subcommand it is the CLI Claude calls from `/learn`. All durable state is one locked JSON file; the rules file is regenerated from it.

**Tech Stack:** Python 3.9+ stdlib only (`json`, `fcntl`, `hashlib`, `re`, `argparse`, `pathlib`). Tests are plain functions in `tests/hooks_test.py`, run with `python3 tests/hooks_test.py`.

**Spec:** `docs/superpowers/specs/2026-11-10-autosave-learn-design.md` (rev 2.1). Read it first.

## Global Constraints

- No cron, no model call, no network, no third-party import.
- Every hook path exits 0 on any error and prints nothing on error.
- `CLAUDE_LEARN` unset or anything but `on` → every hook path exits at once, writes nothing.
- Environment names (the kit's settings `env` block uses the `CLAUDE_` prefix; tests strip `CLAUDE_*`): `CLAUDE_LEARN` (`on`/`off`, template default `off`), `CLAUDE_LEARN_MODE` (`moment` default, `batch`), `CLAUDE_LEARN_TRIAL_DAYS` (default `14`).
- Paths: `~/.claude/learn/learn.json` (mode 600), `~/.claude/learn/learn.lock`, `~/.claude/learn/offer-<session_id>.json`, `~/.claude/rules/learned-rules.md`. Resolve from `Path.home()` at call time so tests' throwaway `HOME` works.
- Stored text: first 200 characters. Rule text: one line, max 200 characters, must not start with `@` or `#`.
- Cap: 15 live rules (state `trial` or `held`). Nudge threshold: 3 pending. Fail on the 2nd confirmed repeat.
- Dates are local ISO dates passed in as `today: str`; no function calls `date.today()` except `main()`.
- The words "proven" and "works" never appear in Learn output, `commands/learn.md`, `commands/bad.md`, or the README's Learn section.
- Exact question strings Claude must use (the Stop handler looks for them): `Save this as a rule?` and `Count as a repeat of rule`.

## Review Focus

1. Claude was told to offer but did not ask (false detection). Expected: the offer closes at that turn's Stop, so the user's next real correction is still detected and recorded. Test in Task 4.
2. Transcript missing, unreadable or not yet flushed at Stop. Expected: exit 0, nothing lost; the next Stop records it. Test in Task 2.
3. A user turn whose content is a list (text blocks plus images). Expected: the first text block is what the detector and the 200-character snippet use. Test in Task 2.
4. Rule text containing newlines, or starting with `@` (would be read as an import) or `#`. Expected: newlines collapse to spaces; `@`/`#` starts are refused with a message. Test in Task 3.
5. Two sessions approving at once at 14 live rules. Expected: exactly one succeeds; the other gets the cap refusal. Test in Task 3.

---

### Task 0: Open check and baseline

**Files:** Modify `docs/superpowers/specs/2026-11-10-autosave-learn-design.md` (one row).

- [ ] **Step 1:** Run `python3 tests/hooks_test.py`, `python3 tests/claims_test.py`, `bash tests/upgrade_test.sh`. Record the pass counts in the PR description. Any failure: stop and report.
- [ ] **Step 2 (needs a person):** ask the human to start an interactive session whose settings include a SessionStart `startup` hook printing `{"systemMessage": "LEARN-TEST"}` and say whether `LEARN-TEST` is shown.
- [ ] **Step 3:** Shown → Task 4 uses SessionStart for the nudge. Not shown → Task 4's `nudge` runs from the Stop handler instead and prints the same JSON there; Task 5 then registers no SessionStart entry. Record the result in the spec's "Still open" paragraph and commit.

### Task 1: State file

**Files:** Create `hooks/learn.py`. Test: `tests/hooks_test.py` (new section `# --- Learn ---`, `import learn`).

**Interfaces (produced):**
- `paths() -> tuple[Path, Path, Path]` → `(state_file, lock_file, rules_file)` from `Path.home()`.
- `EMPTY = {"corrections": [], "rules": [], "active_days": [], "last_nudge": "", "quarantined": 0}`
- `load() -> dict` — missing file → copy of `EMPTY`. Unparseable or not a dict with those list keys → rename to `learn.json.corrupt-<YYYYmmddHHMMSS>`, return `EMPTY` with `quarantined` = 1.
- `mutate(fn: Callable[[dict], tuple[bool, Any]]) -> Any` — `fcntl.flock(LOCK_EX)` on the lock file; `load()`; call `fn(state)`; if it returned `changed=True`: copy current file to `learn.json.bak`, write temp, `os.replace`, `chmod 0o600`, then `export(state)` (Task 3; until then a no-op stub). Returns `fn`'s second value.
- `redact(text: str) -> str` — returns `"[redacted]"` when the text matches `SECRET_RE`, else `text[:200]`. `SECRET_RE` = `sk-[A-Za-z0-9_-]{16,}` | `gh[pousr]_[A-Za-z0-9]{20,}` | `AKIA[0-9A-Z]{16}` | `xox[baprs]-[A-Za-z0-9-]{10,}` | `-----BEGIN [A-Z ]*PRIVATE KEY` | `(?i)(password|passwd|secret|api[_-]?key|token)\s*[:=]\s*\S{6,}`. Add a `# ponytail:` comment: pattern list, not entropy detection; extend when a miss is reported.

- [ ] **Step 1: Write failing tests**

```python
def test_learn_corrupt_state_quarantined_and_reported():
    home = tmp_home(); d = home / ".claude" / "learn"; d.mkdir(parents=True)
    (d / "learn.json").write_text("{not json")
    with _home(home):
        st = learn.load()
    assert st["quarantined"] == 1 and st["rules"] == []
    assert [p for p in d.iterdir() if ".corrupt-" in p.name]

def test_learn_state_mode_600_and_redaction():
    home = tmp_home()
    with _home(home):
        learn.mutate(lambda s: (True, s["active_days"].append("2026-11-10")))
        f = learn.paths()[0]
    assert oct(f.stat().st_mode)[-3:] == "600"
    assert learn.redact("no, use api_key=abcd1234efgh") == "[redacted]"
    assert learn.redact("no, the other file") == "no, the other file"

def test_learn_unchanged_mutate_does_not_rewrite():
    # fn returns (False, None): file must not be created
```

`_home(home)` is a new context manager in the test file that sets and restores `os.environ["HOME"]`.

- [ ] **Step 2:** Run `python3 tests/hooks_test.py`; the three are `BAD` (no module `learn`).
- [ ] **Step 3:** Implement the interfaces above.
- [ ] **Step 4:** Run; all `OK`.
- [ ] **Step 5:** `git add hooks/learn.py tests/hooks_test.py && git commit -m "feat(learn): locked state file with quarantine and redaction"`

### Task 2: Recorder

**Files:** Modify `hooks/learn.py`. Create `tests/fixtures/learn_transcript.jsonl`. Test: `tests/hooks_test.py`.

**Interfaces:**
- Consumes: `redact`, `mutate`.
- Produces:
  - `CORRECTION_RE` — anchored, case-insensitive: `no` (not followed by ` problem`/` worries`), `nope`, `wrong`, `undo`, `revert`, `redo`, `not that`, `that's not` / `thats not`, each ending at a word boundary.
  - `is_correction(text: str) -> bool`
  - `user_turns(transcript: Path) -> list[dict]` — one dict per kept row: `{"key", "ts", "text", "prev_reply", "source"}`. Kept = `type == "user"`, `origin.kind == "human"`, not `isMeta`, not `isSidechain`, content is a string or a list whose blocks are not `tool_result` (use the first `text` block). `source` is `"bad"` when the text contains `<command-name>/bad</command-name>` (then `text` = the `<command-args>` body or `"/bad"`), else `"detector"`. `key` = row `promptId` or `sha1(sessionId + text)`. `prev_reply` = first 200 chars of the text of the nearest earlier `assistant` row, `""` if none. Unreadable file or bad line → skip, never raise.
  - `record(state: dict, session_id: str, project_path: str, turns: list[dict], consumed: set[str], today: str) -> bool` — appends a correction (`state: "pending"`, text and prev_reply through `redact`) for each turn that is `source == "bad"` or `is_correction(text)`, whose key is not in `consumed` and not already stored. Adds `today` to `active_days` if `turns` is non-empty and it is absent. Returns whether anything changed.

- [ ] **Step 1: Build the fixture** — rows in real transcript shape (see spec, "Hook behaviour"): a human turn `"No, still wrong"` (promptId `p1`) after an assistant text row; a human `/bad` row with `<command-args>too long</command-args>` (`p2`); a human turn `"no problem, thanks"` (`p3`); a `tool_result` row; an `isMeta` row; an `isSidechain` row opening `"No issues found"`; a row with `origin: null, promptSource: "sdk"` opening `"No"`; a human row whose content is a list `[image block, {"type":"text","text":"wrong file"}]` (`p4`); one line of invalid JSON.

- [ ] **Step 2: Write failing tests**

```python
def test_learn_detector_phrases():
    for t in ["no, not that", "Nope", "wrong", "undo that", "revert it", "redo", "not that one", "that's not it"]:
        assert learn.is_correction(t), t
    for t in ["no problem", "No worries!", "nothing yet", "note this", "know what", "wrongly named but fine"]:
        assert not learn.is_correction(t), t

def test_learn_recorder_keeps_typed_turns_only():
    turns = learn.user_turns(FIX / "learn_transcript.jsonl")
    assert [t["key"] for t in turns] == ["p1", "p2", "p3", "p4"]
    st = dict(learn.EMPTY, corrections=[], active_days=[])
    assert learn.record(st, "s1", "/proj", turns, set(), "2026-11-10")
    assert [(c["key"], c["source"]) for c in st["corrections"]] == [("p1", "detector"), ("p2", "bad"), ("p4", "detector")]
    assert st["corrections"][0]["prev_reply"] and st["corrections"][1]["text"] == "too long"
    assert st["active_days"] == ["2026-11-10"]

def test_learn_record_twice_adds_nothing():
    # second record() on the same turns returns False and len(corrections) is unchanged

def test_learn_consumed_answer_not_recorded():
    # consumed={"p1"} → p1 absent from corrections

def test_learn_missing_transcript_is_empty_not_crash():
    assert learn.user_turns(Path("/nonexistent/x.jsonl")) == []
```

- [ ] **Step 3:** Run; five `BAD`.
- [ ] **Step 4:** Implement.
- [ ] **Step 5:** Run; all `OK`. Commit `feat(learn): transcript recorder with typed-turn filter`.

### Task 3: Rule lifecycle and export

**Files:** Modify `hooks/learn.py`. Test: `tests/hooks_test.py`.

**Interfaces:**
- Consumes: state shape from Tasks 1–2.
- Produces (each mutates `state` in place and returns `(ok: bool, message: str)` unless noted):
  - `clean_rule(text: str) -> str | None` — collapse whitespace/newlines to single spaces, strip; `None` if empty, over 200 chars, or starting with `@` or `#`.
  - `approve(state, key: str, text: str, today: str)` — refuses unknown key, bad text (`"rule text must be one line, max 200 characters, not starting with @ or #"`), or 15 live rules (message lists live rules, oldest `held` first, and says to retire one). Else appends rule `{"id": next int, "text", "created": today, "state": "trial", "trial_start": today, "receipts": [key], "repeats": []}` and sets the correction `state: "ruled"`, `rule_id`.
  - `dismiss(state, key)` — correction → `dismissed`.
  - `repeat(state, key, rule_id: int)` — correction → `repeat` with `rule_id`; append key to the rule's `repeats`; when `len(repeats) == 2` the rule → `failed`. A key already in `repeats` is not counted twice.
  - `edit(state, rule_id, text, today)` — live rules only; new text through `clean_rule`; state → `trial`, `trial_start` = today.
  - `retire(state, rule_id)` — live rule → `retired`.
  - `promote(state, today: str, trial_days: int) -> bool` — each `trial` rule with `len(repeats) < 2` and at least `trial_days` entries of `active_days` that are `> trial_start` → `held`.
  - `render_rules(state) -> str` — header `# Learned rules` + a line saying the file is generated by Autosave Learn and hand edits are overwritten; then one bullet per live rule: `- <text> _(on trial since <date>)_` or `- <text> _(no repeat seen since <trial_start>)_`. No live rules → header only.
  - `export(state) -> None` — write `render_rules` to the rules file (replace the Task 1 stub).
  - `pending(state) -> str` — numbered pending corrections with key, date, text, prev_reply, plus the live rules with ids (so Claude can spot repeats). When `state["quarantined"]` is non-zero the first line says a damaged state file was set aside and a new one started. Offer files are tiny and are left in place (`# ponytail:` comment: sweep files older than 30 days if the folder ever matters).
  - `status(state, today, kill: bool = False) -> str` — per rule: id, text, state, days in state, quoted receipts, repeat count. With `kill=True` append the four kill lines from the spec, each `PASS`/`FAIL` with its number: rules approved (count of rules ever created) ≥ 5; acceptance = ruled / (ruled + dismissed) over detector-sourced corrections ≥ 0.30; corrections in state `repeat` ≥ 1; `quarantined == 0` and no duplicate correction keys.

- [ ] **Step 1: Write failing tests** (names and the assertion that matters)

```python
def test_learn_approve_writes_trial_rule():       # rules file contains "- Use tabs _(on trial since 2026-11-10)_"
def test_learn_rule_text_rejected():              # 201 chars, "@~/x.md", "# heading" → ok False; "a\nb" stored as "a b"
def test_learn_held_after_14_active_days():       # 13 later active days → trial; 14 → held; file line says "no repeat seen since"
def test_learn_second_repeat_fails_rule():        # 1 repeat → still in file; 2 → state failed, text absent from file; same key twice counts once
def test_learn_edit_resets_trial():               # held → trial, trial_start == today
def test_learn_cap_blocks_16th():                 # 15 live → ok False and message contains "retire"; after retire(…) → ok True
def test_learn_concurrent_approve_at_cap():       # 14 live; two subprocesses run `learn.py approve` for two keys → exactly 15 live rules, one exit message has "retire"
def test_learn_kill_report():                     # crafted state → 4 lines, PASS/FAIL as constructed
def test_learn_output_never_says_proven_or_works()# render_rules + status + pending on a full state; assert neither word (case-insensitive)
```

- [ ] **Step 2:** Run; nine `BAD`.
- [ ] **Step 3:** Implement. Add the CLI in `main()`: `pending`, `approve --key K --text T`, `dismiss --key K`, `repeat --key K --rule N`, `edit --rule N --text T`, `retire --rule N`, `export`, `status [--kill]`; each runs inside `mutate` and prints the message; exit code 0 always (a refusal is a printed message, not an error).
- [ ] **Step 4:** Run; all `OK`. Commit `feat(learn): rule lifecycle, cap, export and status`.

### Task 4: Hook mode

**Files:** Modify `hooks/learn.py`. Test: `tests/hooks_test.py` via the existing `run_hook("learn.py", payload, home, env)`.

**Interfaces:**
- Consumes: everything above.
- Produces: `hook(payload: dict, today: str) -> str` (text to print, `""` for nothing); `main()` with no argv reads stdin JSON, calls `hook`, prints, exits 0; any exception → exit 0 silently.
- Offer file `offer-<session_id>.json`: `{"open": prompt_id | None, "consumed": [prompt_id, ...]}`.

Behaviour by `hook_event_name` (all return `""` unless `CLAUDE_LEARN == "on"`):
- **UserPromptSubmit** — return `""` if `CLAUDE_LEARN_MODE == "batch"` or payload has `agent_id`. If the offer file has `open`: append this `prompt_id` to `consumed`, clear `open`, return `""`. Else if `is_correction(payload["prompt"])`: set `open = prompt_id`, return `OFFER_LINE`.
- **Stop** — if the offer file's `open == payload["prompt_id"]` and `payload.get("last_assistant_message", "")` contains neither `Save this as a rule?` nor `Count as a repeat of rule`: clear `open` (Claude did not ask). Then `mutate`: `record(state, session_id, cwd, user_turns(transcript_path), consumed, today)` and `promote(state, today, trial_days)`.
- **SessionStart** (or Stop, per Task 0) — in batch mode only: if pending count ≥ 3 and `last_nudge != today`, set `last_nudge` and return `json.dumps({"systemMessage": f"Autosave Learn: {n} corrections to review, run /learn"})`.

`OFFER_LINE` (exact copy; `{py}` is the unquoted absolute path of `learn.py`):

```
Autosave Learn: the user's message may be a correction. Fix the issue first. Then, only if it corrected your own work: run `python3 {py} pending`; if it breaks a listed rule ask exactly "Count as a repeat of rule N?", otherwise ask exactly "Save this as a rule?" and quote one proposed rule (one line, max 200 characters). On yes run `python3 {py} repeat --key K --rule N` or `python3 {py} approve --key K --text "..."`; on no run `python3 {py} dismiss --key K`. Type the path unquoted. If it was not a correction of your work, do not mention rules.
```

- [ ] **Step 1: Write failing tests**

```python
def test_learn_off_by_default_is_silent():        # no CLAUDE_LEARN: UserPromptSubmit "no, wrong" → stdout "", no ~/.claude/learn dir
def test_learn_offer_then_no_is_consumed():       # on: prompt p1 "no, wrong" → stdout has "Save this as a rule?"; Stop(p1, last msg contains the question);
                                                  # prompt p2 "no" → stdout ""; Stop(p2) with a transcript holding p1+p2 → corrections keys == ["p1"]
def test_learn_offer_not_asked_closes():          # prompt p1 → offer; Stop(p1, last msg "Fixed.") ; prompt p2 "no, still wrong" → stdout has the offer again
def test_learn_batch_mode_no_injection():         # CLAUDE_LEARN_MODE=batch → "" for a correction prompt
def test_learn_subagent_prompt_ignored():         # payload with agent_id → ""
def test_learn_nudge_at_three_once_a_day():       # batch: 2 pending → ""; 3 → JSON with systemMessage; second call same day → ""
def test_learn_hook_garbage_stdin_fails_open():   # input "{{{" → returncode 0, stdout ""
def test_learn_two_sessions_record_concurrently():# two Stop hooks as subprocesses, different sessions/transcripts → both corrections present
```

- [ ] **Step 2:** Run; eight `BAD`.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Run; all `OK`. Commit `feat(learn): hook mode with offer, answer consumption and nudge`.

### Task 5: Commands, installer, release files, docs

**Files:**
- Create: `commands/learn.md`, `commands/bad.md`
- Modify: `settings.template.json`, `install.sh`, `config.example`, `release/free-files.txt`, `README.md`, `CUSTOMIZE.md`, `CHANGELOG.md`, `tests/upgrade_test.sh`

- [ ] **Step 1: `commands/learn.md`** — instructs Claude: run `python3 ~/.claude/hooks/learn.py pending` (path unquoted); group pending corrections; propose at most 3 rules, each quoting its corrections; list candidate repeats; ask the user about each; run `approve` / `repeat` / `dismiss` per answer; if the argument is `status` run `status` and show it verbatim; if a quarantine is reported, say so. `commands/bad.md` — the previous reply was wrong; ask what should change (use the argument if given), fix it, then ask exactly `Save this as a rule?`.
- [ ] **Step 2: `settings.template.json`** — add env `"CLAUDE_LEARN": "{{LEARN}}"`, `"CLAUDE_LEARN_MODE": "{{LEARN_MODE}}"`, `"CLAUDE_LEARN_TRIAL_DAYS": "{{LEARN_TRIAL_DAYS}}"`; add hook entries in the kit's existing command form (`f="$HOME/.claude/hooks/learn.py"; [ -f "$f" ] || exit 0; python3 "$f"`, timeout 10) under `UserPromptSubmit`, `Stop`, and `SessionStart` matcher `startup` (omit the last if Task 0 said not shown).
- [ ] **Step 3: `install.sh`** — add `LEARN`, `LEARN_MODE`, `LEARN_TRIAL_DAYS` to `KEYS`; after the settings merge, if `~/.claude/learn/learn.json` exists run `learn.py export`. `config.example`: `LEARN="off"`, `LEARN_MODE="moment"`, `LEARN_TRIAL_DAYS="14"` with one comment line each.
- [ ] **Step 4: `tests/upgrade_test.sh`** — add: install into a temp `CLAUDE_DIR`, write a `learn.json` with one held rule and a matching `learned-rules.md`, reinstall, assert both files are byte-identical and `settings.json` holds exactly one `learn.py` entry per event.
- [ ] **Step 5: Docs** — README "Learn" section: what it does, the three switches, moment vs batch, `/learn`, `/learn status`, `/bad`; the limits from the spec (light users see mostly "no repeat seen"; English-only; overlap with built-in memory; other open sessions see changes after restart); the optional allow rule `Bash(python3 <absolute path>/.claude/hooks/learn.py:*)` and that without it each approval asks permission; manual uninstall (remove the three hook entries, delete `~/.claude/rules/learned-rules.md` and `~/.claude/learn/`). Add the hook row to the README hooks table. Add `hooks/learn.py`, `commands/learn.md`, `commands/bad.md`, `tests/fixtures/learn_transcript.jsonl` to `release/free-files.txt`. `CHANGELOG.md`: unreleased entry, "Learn (off by default)".
- [ ] **Step 6:** Run `python3 tests/hooks_test.py && python3 tests/claims_test.py && bash tests/upgrade_test.sh && ./install.sh --dry-run`. All pass; dry run lists the three new files. If `claims_test` fails on a README count, update the count it names.
- [ ] **Step 7:** Commit `feat(learn): commands, installer wiring and docs`.

### Task 6: Dogfood start (hand-off, not code)

- [ ] **Step 1:** Open the PR. Do not flip any default: `LEARN` stays `"off"` in `config.example`.
- [ ] **Step 2:** Tell the human the two things only they do: merge and reinstall, then set `LEARN="on"` in their `kit.conf` and reinstall. Record the start date in the PR.
- [ ] **Step 3:** 30 days later: `python3 ~/.claude/hooks/learn.py status --kill`. Four `PASS` → a follow-up PR sets the default to `on` and adds Learn to the listing. Any `FAIL` → Learn stays off and out of the v1.3 listing.
