#!/usr/bin/env python3
"""Regression tests for the kit's hooks (stdlib only). Run: python3 tests/hooks_test.py
Each hook runs as a subprocess with a throwaway HOME, so nothing touches your real ~/.claude."""
import json, os, shutil, subprocess, sys, tempfile, traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOKS = ROOT / "hooks"
FIX = ROOT / "tests" / "fixtures"
sys.path.insert(0, str(HOOKS))
# Same config the hooks see under run_hook: none of your own CLAUDE_* settings.
for _k in [k for k in os.environ if k.startswith("CLAUDE_")]:
    del os.environ[_k]


def tmp_home():
    return Path(tempfile.mkdtemp(prefix="autosave-test-"))


def run_hook(name, payload, home, env=None):
    e = {k: v for k, v in os.environ.items() if not k.startswith("CLAUDE_")}
    e["HOME"] = str(home)
    e.update(env or {})
    data = payload if isinstance(payload, str) else json.dumps(payload)
    return subprocess.run([sys.executable, str(HOOKS / name)], input=data, capture_output=True,
                          text=True, env=e, cwd=str(home))


# --- A1: bash_output_cap reaches Claude ---

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


# --- B2: count each assistant message once; include subagents ---
import usage_guard as ug


def test_session_stats_counts_each_message_once():
    cost, _, _ = ug.session_stats(FIX / "transcript_dup.jsonl")
    # 3 distinct messages x 1M input @ $3 = 9.00; outputs: m1 last=200 @ $15/M
    assert abs(cost - (9.0 + 0.003)) < 1e-9, cost


def test_session_stats_includes_subagents():
    d = tmp_home(); t = d / "s1.jsonl"; shutil.copy(FIX / "transcript_dup.jsonl", t)
    shutil.copytree(FIX / "subagents", d / "s1" / "subagents", dirs_exist_ok=True)
    base, ctx, model = ug.session_stats(FIX / "transcript_dup.jsonl")
    total, ctx2, model2 = ug.session_stats(t)
    # agent-a.jsonl adds $3.00; agent-a.meta.json is not a transcript and must be ignored
    assert abs(total - (base + 3.0)) < 1e-9, (base, total)
    assert (ctx2, model2) == (ctx, model)


# --- B3: atomic ledger, corrupt ledger recovers instead of erroring every turn ---
QUIET = {"CLAUDE_MONTHLY_BUDGET_USD": "1000000", "CLAUDE_CONTEXT_WARN_TOKENS": "1000000000"}


def _guard_run(home, ledger_text=None):
    led = home / ".claude/usage/ledger.json"
    if ledger_text is not None:
        led.parent.mkdir(parents=True, exist_ok=True); led.write_text(ledger_text)
    tp = home / "s.jsonl"; shutil.copy(FIX / "transcript_dup.jsonl", tp)
    return run_hook("usage_guard.py", {"session_id": "s", "transcript_path": str(tp)}, home, env=QUIET), led


def test_corrupt_ledger_recovers_once():
    h = tmp_home()
    r, led = _guard_run(h, "{not json")
    assert "error" not in r.stdout, r.stdout
    assert len(list(led.parent.glob("ledger.json.corrupt-*"))) == 1
    assert json.loads(led.read_text())["sessions"]["s"] > 0
    r2, _ = _guard_run(h)
    assert "error" not in r2.stdout and len(list(led.parent.glob("ledger.json.corrupt-*"))) == 1


def test_empty_ledger_is_corrupt_not_crash():
    r, led = _guard_run(tmp_home(), "")
    assert "error" not in r.stdout, r.stdout
    assert json.loads(led.read_text())["sessions"]["s"] > 0


def test_ledger_write_leaves_no_tmp():
    r, led = _guard_run(tmp_home())
    assert r.returncode == 0 and led.exists() and not list(led.parent.glob("ledger.json.tmp*"))


# --- B1: statusline uses Claude Code's own session cost and context % ---

def test_statusline_uses_native_cost_and_pct():
    inp = json.loads((FIX / "statusline_input.json").read_text())
    inp["transcript_path"] = str(FIX / "transcript_dup.jsonl")   # the estimate would be ~$9
    out = run_hook("usage_statusline.py", inp, tmp_home(), env={"CLAUDE_MONTHLY_BUDGET_USD": "100"}).stdout
    assert "$1/$100" in out and "ctx 42%" in out, out


def test_statusline_falls_back_without_native_fields():
    inp = {"session_id": "s", "transcript_path": str(FIX / "transcript_dup.jsonl"), "model": {"display_name": "Sonnet"}}
    out = run_hook("usage_statusline.py", inp, tmp_home(), env={"CLAUDE_MONTHLY_BUDGET_USD": "100"}).stdout
    assert "$9/$100" in out and "ctx " in out and "err" not in out, out


def test_statusline_never_quarantines_ledger():
    h = tmp_home(); led = h / ".claude/usage/ledger.json"; led.parent.mkdir(parents=True); led.write_text("{bad")
    inp = json.loads((FIX / "statusline_input.json").read_text()); inp["transcript_path"] = ""
    out = run_hook("usage_statusline.py", inp, h, env={"CLAUDE_MONTHLY_BUDGET_USD": "100"}).stdout
    assert "err" not in out and led.read_text() == "{bad" and not list(led.parent.glob("*.corrupt-*")), out


# --- B: per-model list prices (Claude Code's native cost uses list price) ---

def test_price_rows_current_models():
    u = {"input_tokens": 1_000_000, "output_tokens": 1_000_000, "cache_read_input_tokens": 1_000_000}
    assert abs(ug._price("claude-sonnet-5-5", u) - (2 + 10 + 0.20)) < 1e-9
    assert abs(ug._price("claude-opus-5-5", u) - (4 + 20 + 0.20)) < 1e-9
    assert abs(ug._price("claude-fable-5-1", u) - (10 + 50 + 0.25)) < 1e-9
    assert abs(ug._price("claude-opus-4-6", u) - (5 + 25 + 0.50)) < 1e-9     # older rows unchanged
    assert abs(ug._price("claude-sonnet-4-6", u) - (3 + 15 + 0.30)) < 1e-9
    assert ug.tier("claude-sonnet-5-5") == "sonnet"


# --- final review fixes ---

def test_statusline_resumed_session_keeps_ledger_cost():
    # --resume: native cost restarts low while the ledger holds the full-history estimate
    import datetime as dt
    h = tmp_home(); led = h / ".claude/usage/ledger.json"; led.parent.mkdir(parents=True)
    start, _ = ug.cycle_bounds(dt.date.today(), 1)
    led.write_text(json.dumps({"cycle_start": start.isoformat(), "sessions": {"s": 50.0}}))
    inp = json.loads((FIX / "statusline_input.json").read_text()); inp["transcript_path"] = ""
    out = run_hook("usage_statusline.py", inp, h, env={"CLAUDE_MONTHLY_BUDGET_USD": "100"}).stdout
    assert "$50/$100" in out, out


def test_ledger_with_non_numeric_values_recovers():
    import datetime as dt
    start, _ = ug.cycle_bounds(dt.date.today(), 1)
    r, led = _guard_run(tmp_home(), json.dumps({"cycle_start": start.isoformat(), "sessions": {"a": "1"}}))
    r2, _ = _guard_run(led.parent.parent.parent)
    assert "error" not in r.stdout + r2.stdout, r.stdout + r2.stdout


# --- Learn ---
import contextlib
import learn


@contextlib.contextmanager
def _home(home):
    old = os.environ.get("HOME"); os.environ["HOME"] = str(home)
    try:
        yield
    finally:
        if old is None: os.environ.pop("HOME", None)
        else: os.environ["HOME"] = old


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
    assert len(learn.redact("x" * 300)) == 200


def test_learn_unchanged_mutate_does_not_rewrite():
    home = tmp_home()
    with _home(home):
        assert learn.mutate(lambda s: (False, "r")) == "r"
        assert not learn.paths()[0].exists()


if __name__ == "__main__":
    tests = [(n, f) for n, f in list(globals().items()) if n.startswith("test_") and callable(f)]
    bad = 0
    for n, f in tests:
        try:
            f()
            print(f"OK  {n}")
        except Exception as ex:
            bad += 1
            print(f"BAD {n}: {type(ex).__name__}: {ex}")
            if os.getenv("HOOKS_TEST_TRACE"):
                traceback.print_exc()
    print(f"\n{len(tests) - bad}/{len(tests)} pass")
    raise SystemExit(1 if bad else 0)
