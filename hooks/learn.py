#!/usr/bin/env python3
"""Learn: locked JSON state for correction capture and learned rules (stdlib only).

State: ~/.claude/learn/learn.json (mode 600), lock: learn.lock, export: ~/.claude/rules/learned-rules.md.
"""
import fcntl, json, os, re, shutil, sys, datetime as dt
from pathlib import Path

EMPTY = {"corrections": [], "rules": [], "active_days": [], "last_nudge": "", "quarantined": 0}
# ponytail: pattern list, not entropy detection; extend when a miss is reported.
SECRET_RE = re.compile(
    r"sk-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|xox[baprs]-[A-Za-z0-9-]{10,}"
    r"|-----BEGIN [A-Z ]*PRIVATE KEY|(?i:(password|passwd|secret|api[_-]?key|token)\s*[:=]\s*\S{6,})")


def paths():
    """(state_file, lock_file, rules_file) under the current HOME."""
    h = Path.home()
    return h / ".claude/learn/learn.json", h / ".claude/learn/learn.lock", h / ".claude/rules/learned-rules.md"


def _fresh():
    return json.loads(json.dumps(EMPTY))


def load():
    """Read state; a missing file is empty, a corrupt one is renamed aside and reported via quarantined=1."""
    f = paths()[0]
    if not f.exists():
        return _fresh()
    try:
        st = json.loads(f.read_text())
        if not isinstance(st, dict) or not all(isinstance(st.get(k), list) for k in ("corrections", "rules", "active_days")):
            raise ValueError("bad shape")
        return {**_fresh(), **st}
    except (ValueError, OSError):
        f.rename(f.with_name("learn.json.corrupt-" + dt.datetime.now().strftime("%Y%m%d%H%M%S")))
        st = _fresh(); st["quarantined"] = 1
        return st


def export(state):
    """Write the rules file (filled in by a later task)."""


def mutate(fn):
    """Under an exclusive lock: load, run fn(state) -> (changed, result); save atomically if changed."""
    f, lock, _ = paths()
    f.parent.mkdir(parents=True, exist_ok=True)
    with open(lock, "a") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        st = load()
        changed, result = fn(st)
        if changed:
            if f.exists():
                shutil.copy2(f, f.with_name("learn.json.bak"))
            tmp = f.with_name("learn.json.tmp")
            tmp.write_text(json.dumps(st, indent=1))
            os.chmod(tmp, 0o600)
            os.replace(tmp, f)
            os.chmod(f, 0o600)
            export(st)
        return result


def redact(text):
    """'[redacted]' if text looks like it holds a secret, else its first 200 chars."""
    return "[redacted]" if SECRET_RE.search(text) else text[:200]
