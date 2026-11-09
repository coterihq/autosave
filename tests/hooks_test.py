#!/usr/bin/env python3
"""Regression tests for the kit's hooks (stdlib only). Run: python3 tests/hooks_test.py
Each hook runs as a subprocess with a throwaway HOME, so nothing touches your real ~/.claude."""
import json, os, shutil, subprocess, sys, tempfile, traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOKS = ROOT / "hooks"
FIX = ROOT / "tests" / "fixtures"
sys.path.insert(0, str(HOOKS))


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
