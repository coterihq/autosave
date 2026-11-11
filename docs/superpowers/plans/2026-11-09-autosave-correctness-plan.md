# Autosave correctness release (v1.2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Every claim Autosave makes about itself is true and tested; ship it as v1.2 `autosave.zip`.

**Architecture:** Edit the free tree (`coterihq/autosave`, local clone `~/PROJECTS/claude-code-ops-kit-public`) on a worktree branch; one PR there. A stdlib test file per concern (`tests/hooks_test.py`, `tests/claims_test.py`) runs each hook as a subprocess with a fake `HOME`. The same diff is then applied to the source repo `~/PROJECTS/claude-ops-starter-kit` (local branch, no remote).

**Tech Stack:** Python 3 stdlib only, bash/zsh, `gh`, `release/build_free.py`.

**Spec:** `~/.claude/handoffs/2026-11-09-autosave-correctness-release-design.md` (incl. § Grill decisions). Copied into the repo at `docs/superpowers/specs/` in Task 0.

## Global Constraints

- Python stdlib only; no new dependencies. macOS + zsh is the target platform.
- All hooks fail open: parse or I/O errors exit 0 and never block a session.
- `bash_output_cap.py` never blocks; its message stays one line.
- Scope is fixes A–E only: no new guards, no secret scanning, no plugin packaging, no Linux/Windows work, no Code Red/Quick Save code.
- Every new shipped file is listed in `release/free-files.txt`.
- Version `1.2.0`; ZIP filename `autosave.zip` (no version in the name).
- Gumroad upload stays manual (maintainer). No step publishes anything.
- Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Never `git add -A`; stage named paths.

## Review Focus

1. Transcript with assistant lines that lack `message.id`/`requestId` (older Claude Code) → each line still counted once, never dropped. Test in Task 3.
2. Statusline input with `cost` but no `context_window` (or neither) → falls back to the transcript estimate, never prints `usage: err`. Test in Task 5.
3. Ledger file present but empty (0 bytes, e.g. a crash mid-write before this fix) → treated as corrupt, recovered, the hook still prints its normal output. Test in Task 4.
4. Subagent transcript folder holds non-transcript files (`agent-*.meta.json`, `.prefix.json`) → only `*.jsonl` is read. Test in Task 3 (fixture includes a `.meta.json`).
5. Two Stop hooks finishing at the same time → no half-written ledger (atomic `os.replace`). Covered by Task 4's write-path test (temp file never left behind).

---

### Task 0: Isolate and baseline (ship-flow stage 4)

**Files:**
- Create: `docs/superpowers/specs/2026-11-09-autosave-correctness-release-design.md` (copy of spec)
- Create: `docs/superpowers/plans/2026-11-09-autosave-correctness-plan.md` (copy of this plan)
- Add (already present, untracked): `release/build_free.py`, `release/free-files.txt`, `release/README.md`

- [ ] **Step 1:** `git -C ~/PROJECTS/claude-code-ops-kit-public fetch && git -C ~/PROJECTS/claude-code-ops-kit-public worktree add ../autosave-wt -b fix/correctness-v1.2 origin/main`. Move `release/` from the main checkout into the worktree (it is untracked there).
- [ ] **Step 2:** Baseline, record outputs in the PR body: `python3 hooks/guard_tests.py | tail -1` → `41/41 pass`; `bash tests/upgrade_test.sh` → `upgrade_test: pass`; `grep -c . release/free-files.txt` → `64`; `bash_output_cap.py` on `{"tool_input":{"command":"cat big.log"}}` → prints `systemMessage` JSON.
- [ ] **Step 3:** Commit `release/` + spec + plan: `git commit -m "release: track the free-build manifest; add correctness spec and plan"`.

### Task 1: Test harness + A1 output-cap channel

**Files:**
- Create: `tests/hooks_test.py`
- Modify: `hooks/bash_output_cap.py:13-15`

**Interfaces:**
- Produces: `run_hook(name: str, payload: dict | str, home: Path, env: dict | None = None) -> subprocess.CompletedProcess` in `tests/hooks_test.py` (runs `hooks/<name>` with `HOME=home`, `cwd=home`, every inherited `CLAUDE_*` var stripped, then `env` applied; payload JSON-encoded unless already str). Tests are plain `def test_*()` functions; `__main__` runs every `test_*` in file order, prints `OK`/`BAD <name>: <error>`, ends with `N/N pass`, exits 1 on any failure (same output style as `guard_tests.py`).

- [ ] **Step 1: Failing test**
```python
def test_output_cap_uses_additional_context():
    r = run_hook("bash_output_cap.py", {"tool_name": "Bash", "tool_input": {"command": "cat big.log"}}, tmp_home())
    out = json.loads(r.stdout)
    assert r.returncode == 0
    assert out["hookSpecificOutput"]["hookEventName"] == "PreToolUse"
    assert "[bash_output_cap]" in out["hookSpecificOutput"]["additionalContext"]
    assert "\n" not in out["hookSpecificOutput"]["additionalContext"]
    assert "systemMessage" not in out

def test_output_cap_silent_when_capped():
    r = run_hook("bash_output_cap.py", {"tool_name": "Bash", "tool_input": {"command": "cat big.log | head -50"}}, tmp_home())
    assert r.returncode == 0 and r.stdout.strip() == ""

def test_output_cap_garbage_stdin_fails_open():
    r = run_hook("bash_output_cap.py", "not json", tmp_home())
    assert r.returncode == 0
```
- [ ] **Step 2:** `python3 tests/hooks_test.py` → first test BAD (KeyError `hookSpecificOutput`).
- [ ] **Step 3:** In `bash_output_cap.py`, print `{"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": <same one-line message>}}`; no `permissionDecision` key (never blocks).
- [ ] **Step 4:** `python3 tests/hooks_test.py` → `3/3 pass`.
- [ ] **Step 5:** Commit `tests/hooks_test.py hooks/bash_output_cap.py`: `fix(hooks): bash_output_cap reaches Claude via additionalContext`.

### Task 2: A4 standing-rules wording (A2/A3 dropped at 3b)

3b found PreCompact stdout *does* reach the compaction summarizer (docs: "your stdout becomes instructions for the compaction summary"), so `precompact_dump.py`, `session_inject.py` and README L38 stay as they are (Phil, 2026-11-09).

**Files:**
- Modify: `rules/standing-rules.md:19-20` — "(hooks/usage_guard.py warns you.)" replaces "(Enforced by hooks/usage_guard.py.)"

- [ ] **Step 1:** Edit; `grep -n "Enforced by hooks/usage_guard" rules/standing-rules.md` → no output.
- [ ] **Step 2:** Commit: `docs(rules): usage_guard warns, it does not enforce`.

### Task 3: B2 dedupe + subagent transcripts

**Files:**
- Modify: `hooks/usage_guard.py::session_stats` (lines 26-46)
- Create: `tests/fixtures/transcript_dup.jsonl`, `tests/fixtures/subagents/agent-a.jsonl` + `tests/fixtures/subagents/agent-a.meta.json` (layout confirmed at 3b: `<session>/subagents/agent-*.jsonl`)
- Test: `tests/hooks_test.py`

**Interfaces:**
- Produces: `session_stats(transcript: Path | str) -> tuple[float, int, str]` (unchanged signature: cost USD, last context tokens, last model). Dedupe key = `(message.id, requestId)`; last line wins. Lines missing both fields are each counted. Subagent files: `<transcript.parent>/<transcript.stem>/subagents/*.jsonl`, cost added, context/model taken from the main transcript only.

- [ ] **Step 1: Fixture.** `agent-a.jsonl`: 1 assistant line, msg `s1` req `rs1`, model `claude-sonnet-x`, `input_tokens` 1_000_000 (= +$3.00); `agent-a.meta.json`: `{}`. Dedupe is per file (a key reused across files is counted in each). `transcript_dup.jsonl`: 4 assistant lines, model `claude-sonnet-x`: msg `m1` req `r1` twice (second has `output_tokens` 200, first 100), msg `m2` req `r2` once, one line with no `id`/`requestId`. Each line `input_tokens` 1_000_000, other usage 0 except output.
- [ ] **Step 2: Failing tests**
```python
def test_session_stats_counts_each_message_once():
    cost, _, _ = ug.session_stats(FIX / "transcript_dup.jsonl")
    # 3 distinct messages x 1M input @ $3 = 9.00; outputs: m1 last=200, m2=0, no-id=0 → 200*15/1e6
    assert abs(cost - (9.0 + 0.003)) < 1e-9

def test_session_stats_includes_subagents():
    d = tmp_home(); t = d / "s1.jsonl"; shutil.copy(FIX / "transcript_dup.jsonl", t)
    (d / "s1/subagents").mkdir(parents=True); shutil.copytree(FIX / "subagents", d / "s1/subagents", dirs_exist_ok=True)
    base, ctx, model = ug.session_stats(FIX / "transcript_dup.jsonl")
    total, ctx2, model2 = ug.session_stats(t)
    assert abs(total - (base + 3.0)) < 1e-9 and (ctx2, model2) == (ctx, model)
```
(`ug` = `usage_guard` imported via `sys.path.insert(0, HOOKS)`.)
- [ ] **Step 3:** Run → BAD (cost 12.0x, no subagent cost).
- [ ] **Step 4:** Implement: price `usage.cache_creation.ephemeral_1h_input_tokens` at 2.0x input when present (rest of cache writes 1.25x); collect usage into a dict keyed by `(id, requestId)` (fallback key = line index), then price the values; loop the same parser over subagent files.
- [ ] **Step 5:** Run → pass. Commit: `fix(usage): count each assistant message once; include subagent transcripts`.

### Task 4: B3 atomic ledger + corruption recovery

**Files:**
- Modify: `hooks/usage_guard.py` (`load_ledger`, new `save_ledger`, `main` line 125)
- Test: `tests/hooks_test.py`

**Interfaces:**
- Produces: `load_ledger(start: date, quarantine: bool = True) -> dict` (statusline passes `quarantine=False` and just reads a fresh ledger; on JSON error or empty file: rename to `ledger.json.corrupt-<YYYYmmddHHMMSS>` and return a fresh ledger); `save_ledger(led: dict) -> None` (write `ledger.json.tmp` in the same dir, then `os.replace`). `LEDGER` is resolved from `Path.home()` at import, so tests run the hook as a subprocess with a temp `HOME`.

- [ ] **Step 1: Failing tests**
```python
def test_corrupt_ledger_recovers_once():
    h = tmp_home(); led = h / ".claude/usage/ledger.json"; led.parent.mkdir(parents=True); led.write_text("{not json")
    tp = h / "s.jsonl"; shutil.copy(FIX / "transcript_dup.jsonl", tp)
    r = run_hook("usage_guard.py", {"session_id": "s", "transcript_path": str(tp)}, h)
    assert "error" not in r.stdout
    assert list(led.parent.glob("ledger.json.corrupt-*")) and json.loads(led.read_text())["sessions"]["s"] > 0
    r2 = run_hook("usage_guard.py", {"session_id": "s", "transcript_path": str(tp)}, h)
    assert "error" not in r2.stdout and len(list(led.parent.glob("ledger.json.corrupt-*"))) == 1

def test_empty_ledger_is_corrupt_not_crash():   # Review Focus 3
    ...same as above with led.write_text("")...

def test_ledger_write_leaves_no_tmp():          # Review Focus 5
    ...after a normal run: not (led.parent / "ledger.json.tmp").exists()...
```
Set `CLAUDE_MONTHLY_BUDGET_USD=1000000` and `CLAUDE_CONTEXT_WARN_TOKENS=1000000000` in env so no pace warning or handoff fires.
- [ ] **Step 2:** Run → BAD (`[usage_guard] error: Expecting property name`).
- [ ] **Step 3:** Implement `load_ledger`/`save_ledger`; `main` calls `save_ledger(led)`.
- [ ] **Step 4:** Run → pass. Commit: `fix(usage): atomic ledger writes; quarantine a corrupt ledger instead of erroring every turn`.

### Task 5: B1 statusline uses native cost and context

**Files:**
- Modify: `hooks/usage_statusline.py`
- Create: `tests/fixtures/statusline_input.json` (`session_id`, `transcript_path` placeholder, `model.display_name` "Sonnet", `cost.total_cost_usd` 1.23, `context_window.used_percentage` 42.0)
- Test: `tests/hooks_test.py`

**Interfaces:**
- Consumes: `usage_guard.session_stats`, `load_ledger`, `cfg`, `cycle_bounds`, `pace_for`.
- Produces: output line `"{name} · {pace:.2f}x{flag} · ${spent:.0f}/${budget:.0f} · ctx {N}%"` when `context_window.used_percentage` is present, else the existing `ctx {k}k`. Live session cost = `cost.total_cost_usd` when present, else `session_stats` estimate.

- [ ] **Step 1: Failing tests**
```python
def test_statusline_uses_native_cost_and_pct():
    h = tmp_home(); inp = json.loads((FIX / "statusline_input.json").read_text())
    inp["transcript_path"] = str(FIX / "transcript_dup.jsonl")   # estimate would be ~$9
    out = run_hook("usage_statusline.py", inp, h, env={"CLAUDE_MONTHLY_BUDGET_USD": "100"}).stdout
    assert "$1/$100" in out and "ctx 42%" in out

def test_statusline_falls_back_without_native_fields():   # Review Focus 2
    inp = {"session_id": "s", "transcript_path": str(FIX / "transcript_dup.jsonl"), "model": {"display_name": "Sonnet"}}
    out = run_hook("usage_statusline.py", inp, tmp_home(), env={"CLAUDE_MONTHLY_BUDGET_USD": "100"}).stdout
    assert "$9/$100" in out and "ctx " in out and "err" not in out
```
- [ ] **Step 2:** Run → first BAD.
- [ ] **Step 3:** Implement per Interfaces.
- [ ] **Step 4:** Run → pass. Commit: `fix(statusline): use Claude Code's own session cost and context %`.

### Task 6: C1 guard tests for non-Bash tools + migration-auditor text

**Files:**
- Modify: `hooks/guard_tests.py` (case shape; `__main__` guard)
- Modify: `hooks/guard.py:2` (docstring: "pattern-based hard controls for common risky commands"), `hooks/guard.py:217-221` (`migration-auditor` → `/preflight` only)

**Interfaces:**
- Produces: `cases` list importable from `guard_tests` without running (move the run loop under `if __name__ == "__main__":`). A case's third element is either a Bash command `str` or a full payload `dict` (`{"tool_name": ..., "tool_input": ...}`) sent as-is. Task 7's claims test reads `len(guard_tests.cases)`.

- [ ] **Step 1: Add cases**
```python
 # --- non-Bash tools ---
 (2, ".env", {"tool_name": "Write", "tool_input": {"file_path": "/p/.env", "content": "X=1"}}),
 (0, None,  {"tool_name": "Write", "tool_input": {"file_path": "/p/.env.example", "content": "X="}}),
 (2, ".env", {"tool_name": "Edit", "tool_input": {"file_path": "/p/.env.local", "old_string": "a", "new_string": "b"}}),
 (2, ".env", {"tool_name": "MultiEdit", "tool_input": {"file_path": "/p/.env", "edits": [{"old_string": "a", "new_string": "b"}]}}),
 (2, "apply_migration", {"tool_name": "mcp__supabase__apply_migration", "tool_input": {"name": "x", "query": "select 1"}}),
```
If `apply_migration`'s deny text lacks that substring, use `"linked (prod)"`.
- [ ] **Step 1b:** Runner: `payload = c if isinstance(c, dict) else {"tool_name": "Bash", "tool_input": {"command": c}}`; label = `(c if isinstance(c, str) else json.dumps(c))[:66]`.
- [ ] **Step 2:** `python3 hooks/guard_tests.py | tail -1` → expect `46/46 pass` (the guard already handles these; the cases lock it in). Any BAD = a real guard gap: stop and report, don't widen scope.
- [ ] **Step 3:** Edit guard comment + deny text to name `/preflight` only; rerun → `46/46 pass`.
- [ ] **Step 4:** Commit: `test(guard): cover Write/Edit/MultiEdit .env and MCP apply_migration`.

### Task 7: C3 claims test + D docs

**Files:**
- Create: `tests/claims_test.py`
- Modify: `README.md` (L3 wording, L35 count, L40 footer row, Code Red line; L38 PreCompact row stays — verified true at 3b), `rules/standing-rules.md:13-14`, `QUICKSTART.md` (after L35), `skills/{architecture-simplification,change-impact-recon,security-boundary-proof,cross-layer-contract-repair}/SKILL.md`, `skills/change-control/SKILL.md:35-36`, `skills/evidence-gate/SKILL.md:12`, `skills/outcome-validation/SKILL.md:17`

**Interfaces:**
- Consumes: `guard_tests.cases` (Task 6); `release/free-files.txt`.

- [ ] **Step 1: Failing tests** (same runner style as `hooks_test.py`)
```python
def test_readme_skill_count():      # count of skills/*/SKILL.md in manifest == N in "N evidence-first engineering skills"
def test_readme_guard_case_count(): # len(guard_tests.cases) == N in "N regression cases"
def test_no_retired_claims():       # manifest files except tests/ and CHANGELOG.md: no "migration-auditor", no "cannot talk"
def test_manifest_complete():       # skips with "SKIP (no release/ or .git)" when run from an unpacked ZIP       # every `git ls-files` path under skills/ hooks/ tests/ is in free-files.txt, and every manifest entry exists
def test_footer_marked_optional():  # standing-rules.md contains "footer_check.py, off by default"
```
- [ ] **Step 2:** Run → `test_readme_guard_case_count` (41 vs 46), `test_no_retired_claims`, `test_manifest_complete` (new tests not listed), `test_footer_marked_optional` BAD.
- [ ] **Step 3: Docs edits** (copy is fixed by the spec):
  - README L3: "safety hooks that block common forms of risky commands (pattern-based, not a sandbox)".
  - README L35: 46 cases. L40: begins "When enabled (off by default)".
  - `standing-rules.md` L13-14: "(Optional: hooks/footer_check.py, off by default.)"
  - QUICKSTART after L35: "`rules/standing-rules.md` and `rules/workflow.md` never auto-update; newer versions land beside yours as `.kit-new`."
  - 4 skills: `migration-auditor` → `/preflight`.
  - One-line cross-links, store URL `https://coterihq.gumroad.com` (product slugs unknown; the maintainer can swap in exact links before upload): Code Red in `change-control` L35-36 ("Code Red adds a reviewed parallel-agent coordination workflow") and in README; Quick Save in `evidence-gate` L12 and `outcome-validation` L17 ("Quick Save checks the served SHA for you").
  - Add to `release/free-files.txt`, one path per line (no globs; build_free.py rejects them): `tests/hooks_test.py`, `tests/claims_test.py`, `tests/fixtures/transcript_dup.jsonl`, `tests/fixtures/statusline_input.json`, `tests/fixtures/subagents/agent-a.jsonl`, `tests/fixtures/subagents/agent-a.meta.json`.
- [ ] **Step 4:** `python3 tests/claims_test.py` → `5/5 pass`.
- [ ] **Step 5:** Commit: `docs: make every README/rules claim true; add claims test`.

### Task 8: Spend accuracy check (before release)

- [ ] **Step 1:** Headless reference run (decision Q9a): `claude -p "Use a subagent to count the .py files under hooks/, then reply with the number" --output-format json > $SCRATCH/run.json`. Read `total_cost_usd` and `session_id`; find the transcript under `~/.claude/projects/*/<session_id>.jsonl`; `python3 -c 'import sys; sys.path.insert(0,"hooks"); import usage_guard as u; print(u.session_stats(sys.argv[1]))' <path>` → compute the estimate twice, main transcript only and with subagent files; record which matches `total_cost_usd` within ±10% (docs don't say whether native cost includes subagents). If only main-only matches, note in the PR that B1 (native) and the Stop hook (with subagents) measure different scopes. Also confirm no duplicate `(message.id, requestId)` contributes twice. Record both numbers in the PR body. A miss = stop, `systematic-debugging` (likely the price table or cache multipliers), not a widened tolerance. Record the model the run used and confirm it maps to the right `PRICES` row.

### Task 9: E release build + install check

**Files:**
- Create: `VERSION` (`1.2.0`), `CHANGELOG.md` (`## 1.2.0 — 2026-11-09` + one bullet per fix A1, A4, B1–B3, C1–C3, D; one line "Earlier versions: see git history.")
- Modify: `release/free-files.txt` (+`VERSION`, `CHANGELOG.md`), `release/README.md` (build command → `python3 release/build_free.py ../autosave.zip`)

- [ ] **Step 1:** Rerun `claims_test.py` → pass (manifest completeness covers the new files).
- [ ] **Step 2:** Build: `python3 release/build_free.py ../autosave.zip`; `unzip -l ../autosave.zip | tail -1` → file count = `grep -c . release/free-files.txt`; no `kit.conf`, no `__pycache__`.
- [ ] **Step 3: Install check** (stage-9 rehearsal): `T=$(mktemp -d); unzip -q ../autosave.zip -d $T; CLAUDE_DIR=$T/claude HOME=$T/home bash $T/autosave/install.sh --no-settings`; then from `$T/autosave`: `guard_tests.py`, `hooks_test.py`, `upgrade_test.sh` print pass, and `claims_test.py` prints its non-manifest tests pass + `SKIP (no release/ or .git)`. Full `claims_test.py` passes in the worktree.
- [ ] **Step 4:** Commit: `release: v1.2.0`.

### Task 10: Source mirror, PR

- [ ] **Step 1:** Mirror: `git -C <worktree> diff origin/main...HEAD -- . ':!docs' ':!release' ':!README.md' ':!skills/change-control' ':!tests/claims_test.py' > $SCRATCH/v12.patch`; in `~/PROJECTS/claude-ops-starter-kit`: `git switch -c fix/correctness-v1.2 && git apply $SCRATCH/v12.patch` (plain apply: the repos share no blobs, so --3way buys nothing; all other touched files are byte-identical). Hand-edit source README L3, L35 (46 cases), L40; leave source change-control alone (it ships the paid workflows, no Code Red upsell).. Source README keeps its own skill count (27); run `guard_tests.py`, `hooks_test.py`, `upgrade_test.sh` there (claims_test is free-tree-only by decision Q3a). Commit.
- [ ] **Step 2: PR.** `git push -u origin fix/correctness-v1.2`; `gh pr create --repo coterihq/autosave` with baseline + spend numbers in the body. Auto-merge: `gh pr merge <n> --auto --squash` only after The maintainer enables "Allow auto-merge" (currently off); otherwise say so and stop.
- [ ] **Rollback:** nothing is published by this plan. Don't upload `autosave.zip`; `gh pr close` or revert the squash commit; `git -C ~/PROJECTS/claude-ops-starter-kit switch main` (fix branch is local only).
