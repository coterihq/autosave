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
