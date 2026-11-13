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
    assert learn.redact("no, email jo@x.org re MRN 12345678, call 555-123-4567") == \
        "no, email [pii] re MRN [pii], call [pii]"
    assert learn.redact("no, use port 8080 and v1.2") == "no, use port 8080 and v1.2"


def test_learn_unchanged_mutate_does_not_rewrite():
    home = tmp_home()
    with _home(home):
        assert learn.mutate(lambda s: (False, "r")) == "r"
        assert not learn.paths()[0].exists()


def test_learn_redact_word_boundary():
    assert learn.redact("no, use task-specific-config-file") == "no, use task-specific-config-file"
    assert learn.redact("no, the key is sk-abcdefghijklmnopqrstuv") == "[redacted]"


def test_learn_detector_phrases():
    for t in ["no, not that", "Nope", "wrong", "undo that", "revert it", "not that one", "that's not it",
              # v2: anywhere in the prompt, not just its first word (real misses from an unseen sample)
              "didnt work", "still unclickable", "draft it. but i actually meant specifically for NET",
              "i thought we created a force recheck button?", "no thts a different project",
              "for any and all options recommendations id like a confidence level",
              "at this point forward treat the two accounts as one", "whoops wrong window"]:
        assert learn.is_correction(t), t
    for t in ["no problem", "No worries!", "nothing yet", "note this", "know what", "wrongly named but fine",
              "redo the inbox and then the handoff",  # an instruction, not a correction (v1 false positive)
              "merge it and deploy to prod", "check your work", "do step 2 and commit",
              "didnt work " + "x" * 300, "<pasted_content>still broken</pasted_content>"]:
        assert not learn.is_correction(t), t


def test_learn_dismiss_keeps_no_copy():
    st = dict(learn.EMPTY, corrections=[{"key": "k", "state": "pending", "text": "no, the MRN", "prev_reply": "r"}],
              rules=[], active_days=[])
    assert learn.dismiss(st, "k")[0]
    assert st["corrections"][0]["text"] == st["corrections"][0]["prev_reply"] == ""


def test_learn_recorder_keeps_typed_turns_only():
    turns = learn.user_turns(FIX / "learn_transcript.jsonl")
    assert [t["key"] for t in turns] == ["p1", "p2", "p3", "p4"]
    st = dict(learn.EMPTY, corrections=[], active_days=[])
    assert learn.record(st, "s1", "/proj", turns, set(), "2026-11-10")
    assert [(c["key"], c["source"]) for c in st["corrections"]] == [("p1", "detector"), ("p2", "bad"), ("p4", "detector")]
    assert st["corrections"][0]["prev_reply"] and st["corrections"][1]["text"] == "too long"
    assert st["active_days"] == ["2026-11-10"]


def test_learn_record_twice_adds_nothing():
    turns = learn.user_turns(FIX / "learn_transcript.jsonl")
    st = dict(learn.EMPTY, corrections=[], active_days=[])
    learn.record(st, "s1", "/proj", turns, set(), "2026-11-10")
    n = len(st["corrections"])
    assert not learn.record(st, "s1", "/proj", turns, set(), "2026-11-10")
    assert len(st["corrections"]) == n


def test_learn_consumed_answer_not_recorded():
    turns = learn.user_turns(FIX / "learn_transcript.jsonl")
    st = dict(learn.EMPTY, corrections=[], active_days=[])
    learn.record(st, "s1", "/proj", turns, {"p1"}, "2026-11-10")
    assert "p1" not in [c["key"] for c in st["corrections"]]


def test_learn_missing_transcript_is_empty_not_crash():
    assert learn.user_turns(Path("/nonexistent/x.jsonl")) == []

def test_learn_user_turns_bad_path_is_empty():
    assert learn.user_turns(None) == []


def test_learn_sidechain_reply_not_used_as_prev():
    f = Path(tempfile.mkdtemp(prefix="autosave-test-")) / "t.jsonl"
    rows = [{"type": "assistant", "message": {"content": [{"type": "text", "text": "MAIN"}]}},
            {"type": "assistant", "isSidechain": True, "message": {"content": [{"type": "text", "text": "SIDE"}]}},
            {"type": "user", "sessionId": "s", "promptId": "q1", "origin": {"kind": "human"}, "message": {"content": "no, redo"}}]
    f.write_text("\n".join(json.dumps(r) for r in rows))
    assert learn.user_turns(f)[0]["prev_reply"] == "MAIN"


def _st(*rules, corrections=(), days=(), quarantined=0):
    st = learn._fresh()
    st["rules"] = [dict({"id": i + 1, "text": "r%d" % (i + 1), "created": "2026-11-01", "state": "trial",
                         "trial_start": "2026-11-01", "receipts": [], "repeats": []}, **r) for i, r in enumerate(rules)]
    st["corrections"] = [dict({"key": "k", "ts": "", "session_id": "s", "project_path": "/p", "text": "t", "prev_reply": "",
                               "source": "detector", "state": "pending", "rule_id": None}, **c) for c in corrections]
    st["active_days"] = list(days); st["quarantined"] = quarantined
    return st


def _pend(*keys):
    return [{"key": k} for k in keys]


def test_learn_approve_writes_trial_rule():
    home = tmp_home()
    with _home(home):
        learn.mutate(lambda s: (True, s["corrections"].extend(_st(corrections=_pend("k1"))["corrections"])))
        ok, msg = learn.mutate(lambda s: (True, learn.approve(s, "k1", "Use tabs", "2026-11-10")))
        assert ok, msg
        txt = learn.paths()[2].read_text()
    assert "- Use tabs _(on trial since 2026-11-10)_" in txt


def test_learn_rule_text_rejected():
    st = _st(corrections=_pend("k1"))
    for bad in ["x" * 201, "@~/x.md", "# heading", "  "]:
        ok, msg = learn.approve(st, "k1", bad, "2026-11-10")
        assert not ok and "one line" in msg, bad
    ok, _ = learn.approve(st, "k1", "a\nb", "2026-11-10")
    assert ok and st["rules"][0]["text"] == "a b"
    assert not learn.approve(st, "nope", "ok", "2026-11-10")[0]


def test_learn_held_after_14_active_days():
    days = ["2026-11-%02d" % d for d in range(2, 15)]  # 13 later days
    st = _st({"trial_start": "2026-11-01"}, days=["2026-11-01"] + days)
    assert not learn.promote(st, "2026-11-14", 14) and st["rules"][0]["state"] == "trial"
    st["active_days"].append("2026-11-15")
    assert learn.promote(st, "2026-11-15", 14) and st["rules"][0]["state"] == "held"
    assert "no repeat seen since 2026-11-01" in learn.render_rules(st)


def test_learn_second_repeat_fails_rule():
    st = _st({}, corrections=_pend("a", "b"))
    learn.repeat(st, "a", 1); learn.repeat(st, "a", 1)
    assert st["rules"][0]["repeats"] == ["a"] and st["rules"][0]["state"] == "trial"
    assert "r1" in learn.render_rules(st)
    learn.repeat(st, "b", 1)
    assert st["rules"][0]["state"] == "failed" and "r1" not in learn.render_rules(st)


def test_learn_edit_resets_trial():
    st = _st({"state": "held"})
    ok, _ = learn.edit(st, 1, "new text", "2026-11-10")
    assert ok and st["rules"][0]["state"] == "trial" and st["rules"][0]["trial_start"] == "2026-11-10"
    assert st["rules"][0]["text"] == "new text"


def test_learn_cap_blocks_16th():
    st = _st(*[{} for _ in range(15)], corrections=_pend("k1"))
    ok, msg = learn.approve(st, "k1", "one more", "2026-11-10")
    assert not ok and "retire" in msg
    assert learn.retire(st, 3)[0]
    assert learn.approve(st, "k1", "one more", "2026-11-10")[0]


def test_learn_concurrent_approve_at_cap():
    home = tmp_home()
    seed = _st(*[{} for _ in range(14)], corrections=_pend("k1", "k2"))
    with _home(home):
        learn.mutate(lambda s: (True, s.update(seed)))
    e = dict(os.environ, HOME=str(home))
    ps = [subprocess.Popen([sys.executable, str(HOOKS / "learn.py"), "approve", "--key", k, "--text", "t" + k],
                           stdout=subprocess.PIPE, text=True, env=e) for k in ("k1", "k2")]
    outs = [p.communicate()[0] for p in ps]
    with _home(home):
        st = learn.load()
    assert sum(r["state"] == "trial" for r in st["rules"]) == 15
    assert sum("retire" in o for o in outs) == 1 and all(p.returncode == 0 for p in ps)


def test_learn_kill_report():
    good = _st(*[{} for _ in range(5)],
               corrections=[{"key": "a", "state": "ruled"}, {"key": "b", "state": "dismissed"}, {"key": "c", "state": "repeat"}])
    with _home(tmp_home()):
        lines = [l for l in learn.status(good, "2026-11-10", kill=True).splitlines() if l.startswith(("PASS", "FAIL"))]
    assert len(lines) == 4 and all(l.startswith("PASS") for l in lines), lines
    bad = _st({}, corrections=[{"key": "a", "state": "ruled"}] + [{"key": "d%d" % i, "state": "dismissed"} for i in range(5)] + [{"key": "a"}],
              quarantined=1)
    with _home(tmp_home()):
        lines = [l for l in learn.status(bad, "2026-11-10", kill=True).splitlines() if l.startswith(("PASS", "FAIL"))]
    assert len(lines) == 4 and all(l.startswith("FAIL") for l in lines), lines


# The ban covers strings Learn authors; user-typed text is quoted verbatim as a receipt.
def test_learn_output_never_says_proven_or_works():
    import re
    st = _st({"state": "held", "receipts": ["k"]}, {"state": "failed", "repeats": ["a", "b"]},
             corrections=[{"key": "k", "text": "nope", "prev_reply": "done"}, {"key": "z", "state": "repeat", "rule_id": 1}],
             quarantined=1, days=["2026-11-02"])
    with _home(tmp_home()):
        out = "\n".join([learn.render_rules(st), learn.status(st, "2026-11-10", kill=True), learn.pending(st),
                         learn.approve(st, "k", "x" * 201, "2026-11-10")[1], learn.retire(st, 99)[1], learn.ANSWER_LINE, learn.OFFER_LINE])
    assert not re.search(r"\b(proven|works)\b", out, re.I), out


# --- Learn: hook mode ---
LON = {"CLAUDE_LEARN": "on"}


def _ups(pid, prompt, sid="s1", **kw):
    return dict({"hook_event_name": "UserPromptSubmit", "session_id": sid, "prompt_id": pid, "prompt": prompt, "cwd": "/p",
                 "transcript_path": "/none"}, **kw)


def _stop(pid, last, tp="/none", sid="s1"):
    return {"hook_event_name": "Stop", "session_id": sid, "prompt_id": pid, "last_assistant_message": last,
            "cwd": "/p", "transcript_path": str(tp), "stop_hook_active": False}


def _transcript(home, name, prompts):
    f = Path(home) / name
    rows = [{"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": "done"}]}}]
    for pid, text in prompts:
        rows.append({"type": "user", "sessionId": "s1", "timestamp": "2026-11-10T16:00:00.000Z", "isSidechain": False,
                     "origin": {"kind": "human"}, "message": {"role": "user", "content": text}, "promptId": pid})
    f.write_text("\n".join(json.dumps(r) for r in rows))
    return f


def _state(home):
    with _home(home):
        return learn.load()


def test_learn_off_by_default_is_silent():
    home = tmp_home()
    r = run_hook("learn.py", _ups("p1", "no, wrong"), home)
    assert r.returncode == 0 and r.stdout == "" and not (home / ".claude" / "learn").exists()


def _answer_ok(out):
    """The answer prompt gets the answer line, never a fresh offer."""
    assert "the user is answering your rule question" in out and "may be a correction" not in out, out


def test_learn_offer_then_no_is_consumed():
    home = tmp_home()
    tp = _transcript(home, "t.jsonl", [("p1", "no, wrong")])
    r = run_hook("learn.py", _ups("p1", "no, wrong"), home, LON)
    assert "Save this as a rule?" in r.stdout and "~/.claude/hooks/learn.py" in r.stdout
    run_hook("learn.py", _stop("p1", "Save this as a rule? Proposed: use tabs", tp), home, LON)
    _answer_ok(run_hook("learn.py", _ups("p2", "no"), home, LON).stdout)
    _transcript(home, "t.jsonl", [("p1", "no, wrong"), ("p2", "no")])
    run_hook("learn.py", _stop("p2", "ok", tp), home, LON)
    assert [c["key"] for c in _state(home)["corrections"]] == ["p1"]


def test_learn_offer_not_asked_closes():
    home = tmp_home()
    tp = _transcript(home, "t.jsonl", [("p1", "no, wrong")])
    assert "Save this as a rule?" in run_hook("learn.py", _ups("p1", "no, wrong"), home, LON).stdout
    run_hook("learn.py", _stop("p1", "Fixed.", tp), home, LON)
    assert "Save this as a rule?" in run_hook("learn.py", _ups("p2", "no, still wrong"), home, LON).stdout
    c = _state(home)["corrections"]
    assert [(x["key"], x["state"]) for x in c] == [("p1", "pending")]


def test_learn_interrupted_turn_does_not_swallow_next_correction():
    home = tmp_home()
    assert "Save this as a rule?" in run_hook("learn.py", _ups("p1", "no, wrong"), home, LON).stdout
    # no Stop for p1: the user interrupted
    assert "Save this as a rule?" in run_hook("learn.py", _ups("p2", "no, still wrong"), home, LON).stdout
    tp = _transcript(home, "t.jsonl", [("p1", "no, wrong"), ("p2", "no, still wrong")])
    run_hook("learn.py", _stop("p2", "Fixed.", tp), home, LON)
    assert sorted(c["key"] for c in _state(home)["corrections"]) == ["p1", "p2"]


def test_learn_missing_prompt_id_skips_offer():
    home = tmp_home()
    p = _ups("p1", "no, wrong"); del p["prompt_id"]
    r = run_hook("learn.py", p, home, LON)
    assert r.returncode == 0 and r.stdout == "" and not list((home / ".claude").glob("learn/offer-*"))


def test_learn_missing_session_id_is_silent():
    home = tmp_home()
    p = _ups("p1", "no, wrong"); del p["session_id"]
    r = run_hook("learn.py", p, home, LON)
    assert r.returncode == 0 and r.stdout == "" and not (home / ".claude" / "learn").exists()


def _asked_without_offer(env):
    home = tmp_home()
    run_hook("learn.py", _stop("p1", "Fixed. Save this as a rule? Proposed: use tabs"), home, env)
    out = run_hook("learn.py", _ups("p2", "no"), home, env).stdout
    tp = _transcript(home, "t.jsonl", [("p1", "make it shorter"), ("p2", "no")])
    run_hook("learn.py", _stop("p2", "ok", tp), home, env)
    return out, [c["key"] for c in _state(home)["corrections"]]


def test_learn_question_without_offer_then_no_is_consumed():
    out, keys = _asked_without_offer(LON)
    _answer_ok(out); assert "p2" not in keys, keys


def test_learn_batch_mode_answer_is_consumed():
    out, keys = _asked_without_offer(dict(LON, CLAUDE_LEARN_MODE="batch"))
    _answer_ok(out); assert "p2" not in keys, keys


def test_learn_double_stop_keeps_offer():
    home = tmp_home()
    assert "Save this as a rule?" in run_hook("learn.py", _ups("p1", "no, wrong"), home, LON).stdout
    run_hook("learn.py", _stop("p1", "Fixed."), home, LON)
    run_hook("learn.py", _stop("p1", "Save this as a rule? Proposed: use tabs"), home, LON)
    _answer_ok(run_hook("learn.py", _ups("p2", "no"), home, LON).stdout)
    tp = _transcript(home, "t.jsonl", [("p1", "no, wrong"), ("p2", "no")])
    run_hook("learn.py", _stop("p2", "ok", tp), home, LON)
    assert [c["key"] for c in _state(home)["corrections"]] == ["p1"]


def test_learn_batch_mode_no_injection():
    r = run_hook("learn.py", _ups("p1", "no, wrong"), tmp_home(), dict(LON, CLAUDE_LEARN_MODE="batch"))
    assert r.returncode == 0 and r.stdout == ""


def test_learn_subagent_prompt_ignored():
    r = run_hook("learn.py", _ups("p1", "no, wrong", agent_id="a1"), tmp_home(), LON)
    assert r.returncode == 0 and r.stdout == ""


def test_learn_nudge_at_three_once_a_day():
    home = tmp_home(); env = dict(LON, CLAUDE_LEARN_MODE="batch")
    ss = {"hook_event_name": "SessionStart", "session_id": "s9", "source": "startup", "cwd": "/p", "transcript_path": "/none"}
    def seed(n):
        with _home(home):
            learn.mutate(lambda s: (True, s["corrections"].extend(_st(corrections=_pend(*["k%d" % i for i in range(n)]))["corrections"])))
    seed(2)
    assert run_hook("learn.py", ss, home, env).stdout == ""
    with _home(home):
        learn.mutate(lambda s: (True, s["corrections"].extend(_st(corrections=_pend("k9"))["corrections"])))
    out = json.loads(run_hook("learn.py", ss, home, env).stdout)
    assert "3 corrections" in out["systemMessage"] and "/learn" in out["systemMessage"]
    assert run_hook("learn.py", ss, home, env).stdout == ""


def test_learn_hook_garbage_stdin_fails_open():
    r = run_hook("learn.py", "{{{", tmp_home(), LON)
    assert r.returncode == 0 and r.stdout == ""


def test_learn_two_sessions_record_concurrently():
    home = tmp_home()
    t1 = _transcript(home, "a.jsonl", [("a1", "no, wrong")]); t2 = _transcript(home, "b.jsonl", [("b1", "undo that")])
    e = {k: v for k, v in os.environ.items() if not k.startswith("CLAUDE_")}
    e.update(HOME=str(home), CLAUDE_LEARN="on")
    ps = [subprocess.Popen([sys.executable, str(HOOKS / "learn.py")], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, env=e)
          for _ in range(2)]
    for p, (sid, pid, tp) in zip(ps, [("sa", "a1", t1), ("sb", "b1", t2)]):
        p.stdin.write(json.dumps(_stop(pid, "ok", tp, sid))); p.stdin.close()
    assert [p.wait() for p in ps] == [0, 0]
    assert sorted(c["key"] for c in _state(home)["corrections"]) == ["a1", "b1"]


# --- Learn: carried fixes from Task 3 review ---
def test_learn_approve_twice_creates_one_rule():
    st = _st(corrections=_pend("k1"))
    assert learn.approve(st, "k1", "one", "2026-11-10")[0]
    ok, msg = learn.approve(st, "k1", "two", "2026-11-10")
    assert not ok and msg and len(st["rules"]) == 1


def test_learn_repeat_of_own_receipt_refused():
    st = _st(corrections=_pend("k1"))
    learn.approve(st, "k1", "one", "2026-11-10")
    st["corrections"][0]["state"] = "pending"  # even if state were reset, the receipt key cannot count as a repeat
    ok, _ = learn.repeat(st, "k1", 1)
    assert not ok and st["rules"][0]["repeats"] == []


def test_learn_dismiss_ruled_key_refused():
    st = _st(corrections=_pend("k1"))
    learn.approve(st, "k1", "one", "2026-11-10")
    ok, _ = learn.dismiss(st, "k1")
    assert not ok and st["corrections"][0]["state"] == "ruled"


def test_learn_rule_text_rejects_at_path_anywhere():
    st = _st(corrections=_pend("k1"))
    ok, msg = learn.approve(st, "k1", "always read @~/notes.md first", "2026-11-10")
    assert not ok and msg == "rule text must be one line, max 200 characters, not starting with # and with no @path and no credentials"
    assert learn.clean_rule("mail a@b.com") == "mail a@b.com" and learn.clean_rule("@x") is None


def test_learn_export_leaves_no_temp_file():
    home = tmp_home()
    with _home(home):
        learn.export(learn._fresh())
        names = [p.name for p in learn.paths()[2].parent.iterdir()]
    assert names == ["learned-rules.md"], names


def test_learn_cli_argument_error_exits_zero():
    r = subprocess.run(
        [sys.executable, str(HOOKS / "learn.py"), "retire", "--rule", "notanumber"], capture_output=True, text=True,
        env=dict(os.environ, HOME=str(tmp_home())))
    assert r.returncode == 0 and "usage" in r.stdout.lower(), (r.returncode, r.stdout, r.stderr)


# --- Learn: final review fix wave ---
def _cli(home, *args):
    return subprocess.run([sys.executable, str(HOOKS / "learn.py"), *args], capture_output=True, text=True,
                          env=dict(os.environ, HOME=str(home)))


def test_learn_offer_carries_key_and_forbids_approve():
    out = run_hook("learn.py", _ups("p1", "no, wrong"), tmp_home(), LON).stdout
    assert "key p1" in out and "approve --key" not in out and "~/.claude/hooks/learn.py" in out, out


def test_learn_approve_on_answer_turn_full_flow():
    home = tmp_home()
    tp = _transcript(home, "t.jsonl", [("p1", "no, wrong")])
    run_hook("learn.py", _ups("p1", "no, wrong"), home, LON)
    run_hook("learn.py", _stop("p1", "Fixed. Save this as a rule? Proposed: Use tabs", tp), home, LON)
    out = run_hook("learn.py", _ups("p2", "yes"), home, LON).stdout
    assert "approve --key p1" in out, out
    r = _cli(home, "approve", "--key", "p1", "--text", "Use tabs")
    assert r.returncode == 0, r
    tp = _transcript(home, "t.jsonl", [("p1", "no, wrong"), ("p2", "yes")])
    run_hook("learn.py", _stop("p2", "ok", tp), home, LON)
    st = _state(home)
    assert len(st["rules"]) == 1 and st["rules"][0]["receipts"] == ["p1"]
    assert [c["key"] for c in st["corrections"]] == ["p1"]


def test_learn_unknown_key_says_not_recorded_yet():
    home = tmp_home()
    for args in (("approve", "--key", "nope", "--text", "x"), ("dismiss", "--key", "nope"), ("repeat", "--key", "nope", "--rule", "1")):
        r = _cli(home, *args)
        assert "is recorded yet" in r.stdout and "answer again after your next reply" in r.stdout, r.stdout
    assert _state(home)["rules"] == []


def test_learn_quarantine_survives_read_and_fails_kill_check():
    home = tmp_home(); d = home / ".claude" / "learn"; d.mkdir(parents=True)
    (d / "learn.json").write_text("{not json")
    assert "damaged state file" in _cli(home, "pending").stdout
    assert "damaged state file" in _cli(home, "pending").stdout
    line = [l for l in _cli(home, "status", "--kill").stdout.splitlines() if l.startswith(("PASS", "FAIL")) and "state intact" in l]
    assert line and line[0].startswith("FAIL"), line


def test_learn_rule_text_with_credential_refused():
    st = _st(corrections=_pend("k1"))
    ok, msg = learn.approve(st, "k1", "use api_key=abcd1234efgh in calls", "2026-11-10")
    assert not ok and "no credentials" in msg and st["rules"] == []


def test_learn_state_dir_mode_700():
    home = tmp_home()
    with _home(home):
        learn.mutate(lambda s: (True, s["active_days"].append("2026-11-10")))
    assert (home / ".claude" / "learn").stat().st_mode & 0o777 == 0o700


def test_learn_failed_rule_rewrite_via_repeat_key():
    st = _st({}, corrections=_pend("a", "b"))
    learn.repeat(st, "a", 1); learn.repeat(st, "b", 1)
    assert st["rules"][0]["state"] == "failed"
    out = learn.pending(st)
    assert "Failed rules (offer one rewrite each)" in out and "key=b" in out and "r1" in out
    ok, _ = learn.approve(st, "b", "better rewrite", "2026-11-10")
    assert ok and st["rules"][0]["state"] == "failed" and st["rules"][1]["state"] == "trial"
    assert st["rules"][1]["receipts"] == ["b"] and st["corrections"][1]["state"] == "ruled"
    assert "Failed rules" not in learn.pending(st)


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
