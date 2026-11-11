#!/usr/bin/env python3
"""Learn: locked JSON state for correction capture and learned rules (stdlib only).

State: ~/.claude/learn/learn.json (mode 600), lock: learn.lock, export: ~/.claude/rules/learned-rules.md.
"""
import fcntl, hashlib, json, os, re, shutil, sys, datetime as dt
from pathlib import Path

EMPTY = {"corrections": [], "rules": [], "active_days": [], "last_nudge": "", "quarantined": 0}
# ponytail: pattern list, not entropy detection; extend when a miss is reported.
SECRET_RE = re.compile(
    r"\bsk-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|xox[baprs]-[A-Za-z0-9-]{10,}"
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


CORRECTION_RE = re.compile(
    r"\s*(?:no(?! problem| worries)|nope|wrong|undo|revert|redo|not that|that'?s not)\b", re.I)


def is_correction(text):
    return bool(CORRECTION_RE.match(text))


def _text(content):
    """First text of a message body; None for tool results or no text."""
    if isinstance(content, str):
        return content
    if isinstance(content, list) and not any(isinstance(b, dict) and b.get("type") == "tool_result" for b in content):
        return next((b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"), None)


def user_turns(transcript):
    """Typed human turns of a transcript as dicts; an unreadable file or bad line is skipped."""
    out, prev = [], ""
    try:
        lines = Path(transcript).read_text(errors="replace").splitlines()
    except OSError:
        return out
    for ln in lines:
        try:
            row = json.loads(ln)
            msg = row["message"]
            text = _text(msg["content"])
            if row["type"] == "assistant":
                prev = (_text(msg["content"]) or prev)[:200]  # tool-only rows keep the last text
                continue
            if row["type"] != "user" or text is None or (row.get("origin") or {}).get("kind") != "human" \
                    or row.get("isMeta") or row.get("isSidechain"):
                continue
            source = "detector"
            if "<command-name>/bad</command-name>" in text:
                m = re.search(r"<command-args>(.*?)</command-args>", text, re.S)
                source, text = "bad", (m.group(1).strip() if m else "") or "/bad"
            key = row.get("promptId") or hashlib.sha1((str(row.get("sessionId")) + text).encode()).hexdigest()
            out.append({"key": key, "ts": row.get("timestamp") or "", "text": text, "prev_reply": prev, "source": source})
        except (ValueError, KeyError, TypeError, AttributeError):
            continue
    return out


def record(state, session_id, project_path, turns, consumed, today):
    """Append pending corrections for new bad/detector turns; True if state changed."""
    seen = {c["key"] for c in state["corrections"]}
    n = len(state["corrections"])
    for t in turns:
        if t["key"] in consumed or t["key"] in seen or not (t["source"] == "bad" or is_correction(t["text"])):
            continue
        seen.add(t["key"])
        state["corrections"].append({"key": t["key"], "ts": t["ts"], "session_id": session_id, "project_path": project_path,
                                     "text": redact(t["text"]), "prev_reply": redact(t["prev_reply"]),
                                     "source": t["source"], "state": "pending", "rule_id": None})
    if turns and today not in state["active_days"]:
        state["active_days"].append(today)
        return True
    return len(state["corrections"]) > n
