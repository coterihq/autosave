#!/usr/bin/env python3
"""Learn: locked JSON state for correction capture and learned rules (stdlib only).

State: ~/.claude/learn/learn.json (mode 600), lock: learn.lock, export: ~/.claude/rules/learned-rules.md.
"""
import argparse, fcntl, hashlib, json, os, re, shutil, sys, datetime as dt
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
    """Write the generated rules file, creating ~/.claude/rules/ if needed."""
    f = paths()[2]
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(render_rules(state))


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
    except (OSError, ValueError, TypeError):
        return out
    for ln in lines:
        try:
            row = json.loads(ln)
            msg = row["message"]
            text = _text(msg["content"])
            if row["type"] == "assistant":
                if row.get("isSidechain"):
                    continue
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


LIVE = ("trial", "held")
CAP = 15
BAD_TEXT = "rule text must be one line, max 200 characters, not starting with @ or #"


def clean_rule(text):
    """Single-line rule text, or None if empty, over 200 chars, or starting with @ or #."""
    t = " ".join(str(text).split())
    return t if t and len(t) <= 200 and t[0] not in "@#" else None


def _live(state):
    return [r for r in state["rules"] if r["state"] in LIVE]


def _rule(state, rule_id):
    return next((r for r in state["rules"] if r["id"] == rule_id), None)


def _corr(state, key):
    return next((c for c in state["corrections"] if c["key"] == key), None)


def approve(state, key, text, today):
    c = _corr(state, key)
    if c is None:
        return False, "no correction with key %s" % key
    t = clean_rule(text)
    if t is None:
        return False, BAD_TEXT
    live = _live(state)
    if len(live) >= CAP:
        order = sorted(live, key=lambda r: (r["state"] != "held", r["id"]))
        lst = "; ".join("%d (%s): %s" % (r["id"], r["state"], r["text"]) for r in order)
        return False, "%d live rules is the cap. Please retire one first. Live rules, oldest held first: %s" % (CAP, lst)
    rid = max([r["id"] for r in state["rules"]] + [0]) + 1
    state["rules"].append({"id": rid, "text": t, "created": today, "state": "trial", "trial_start": today,
                           "receipts": [key], "repeats": []})
    c["state"], c["rule_id"] = "ruled", rid
    return True, "rule %d added on trial: %s" % (rid, t)


def dismiss(state, key):
    c = _corr(state, key)
    if c is None:
        return False, "no correction with key %s" % key
    c["state"] = "dismissed"
    return True, "dismissed %s" % key


def repeat(state, key, rule_id):
    c, r = _corr(state, key), _rule(state, rule_id)
    if c is None or r is None or r["state"] not in LIVE:
        return False, "need a known correction key and a live rule id"
    c["state"], c["rule_id"] = "repeat", rule_id
    if key not in r["repeats"]:
        r["repeats"].append(key)
    if len(r["repeats"]) >= 2:
        r["state"] = "failed"
        return True, "rule %d failed: repeated twice, removed from the rules file" % rule_id
    return True, "repeat noted on rule %d (%d of 2)" % (rule_id, len(r["repeats"]))


def edit(state, rule_id, text, today):
    r = _rule(state, rule_id)
    if r is None or r["state"] not in LIVE:
        return False, "no live rule %s" % rule_id
    t = clean_rule(text)
    if t is None:
        return False, BAD_TEXT
    r["text"], r["state"], r["trial_start"] = t, "trial", today
    return True, "rule %d edited, trial restarted %s" % (rule_id, today)


def retire(state, rule_id):
    r = _rule(state, rule_id)
    if r is None or r["state"] not in LIVE:
        return False, "no live rule %s" % rule_id
    r["state"] = "retired"
    return True, "rule %d retired" % rule_id


def _days(state, r):
    return sum(d > r["trial_start"] for d in state["active_days"])


def promote(state, today, trial_days):
    """Trial rules with under 2 repeats and enough active days since trial_start become held."""
    moved = False
    for r in state["rules"]:
        if r["state"] == "trial" and len(r["repeats"]) < 2 and _days(state, r) >= trial_days:
            r["state"], moved = "held", True
    return moved


def render_rules(state):
    out = ["# Learned rules", "", "Generated by Autosave Learn. Hand edits are overwritten."]
    live = _live(state)
    if live:
        out.append("")
    for r in live:
        note = "on trial since %s" % r["trial_start"] if r["state"] == "trial" else "no repeat seen since %s" % r["trial_start"]
        out.append("- %s _(%s)_" % (r["text"], note))
    return "\n".join(out) + "\n"


def _live_lines(state):
    return ["  rule %d (%s): %s" % (r["id"], r["state"], r["text"]) for r in _live(state)] or ["  none"]


def pending(state):
    out = []
    if state.get("quarantined"):
        out.append("A damaged state file was set aside and a new one started.")
    todo = [c for c in state["corrections"] if c["state"] == "pending"]
    out.append("Pending corrections: %d" % len(todo))
    # ponytail: offer files are left in place; sweep files older than 30 days if the folder ever matters.
    for i, c in enumerate(todo, 1):
        out.append("%d. key=%s date=%s\n   user: %s\n   reply before: %s" % (i, c["key"], c["ts"][:10], c["text"], c["prev_reply"]))
    out.append("Live rules:")
    return "\n".join(out + _live_lines(state))


def status(state, today, kill=False):
    out = []
    for r in state["rules"]:
        out.append("rule %d [%s] %d days in state, %d repeats: %s" % (r["id"], r["state"], _days(state, r), len(r["repeats"]), r["text"]))
        out += ['  receipt: "%s"' % (_corr(state, k) or {}).get("text", k) for k in r["receipts"]]
    if not out:
        out = ["no rules yet"]
    if kill:
        det = [c for c in state["corrections"] if c["source"] == "detector"]
        ruled, dism = sum(c["state"] == "ruled" for c in det), sum(c["state"] == "dismissed" for c in det)
        acc = ruled / (ruled + dism) if ruled + dism else 0.0
        keys = [c["key"] for c in state["corrections"]]
        lk = lambda ok, msg: "%s %s" % ("PASS" if ok else "FAIL", msg)
        out += [lk(len(state["rules"]) >= 5, "rules approved: %d (need 5)" % len(state["rules"])),
                lk(acc >= 0.30, "acceptance %.2f (need 0.30)" % acc),
                lk(any(c["state"] == "repeat" for c in state["corrections"]), "corrections marked repeat: %d (need 1)" %
                   sum(c["state"] == "repeat" for c in state["corrections"])),
                lk(not state["quarantined"] and len(keys) == len(set(keys)), "state intact: quarantined %d, duplicate keys %d" %
                   (state["quarantined"], len(keys) - len(set(keys))))]
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="learn.py")
    sub = ap.add_subparsers(dest="cmd")
    for name, args in {"pending": [], "approve": ["key", "text"], "dismiss": ["key"], "repeat": ["key", "rule"],
                       "edit": ["rule", "text"], "retire": ["rule"], "export": [], "status": []}.items():
        p = sub.add_parser(name)
        for a in args:
            p.add_argument("--" + a, required=True, type=int if a == "rule" else str)
    sub.choices["status"].add_argument("--kill", action="store_true")
    a = ap.parse_args(argv)
    if not a.cmd:
        return  # ponytail: Task 4 turns no-argument mode into hook mode.
    today = dt.date.today().isoformat()
    ops = {"pending": lambda s: (False, pending(s)),
           "status": lambda s: (False, status(s, today, a.kill)),
           "export": lambda s: (True, "rules file written"),
           "approve": lambda s: approve(s, a.key, a.text, today),
           "dismiss": lambda s: dismiss(s, a.key),
           "repeat": lambda s: repeat(s, a.key, a.rule),
           "edit": lambda s: edit(s, a.rule, a.text, today),
           "retire": lambda s: retire(s, a.rule)}
    print(mutate(ops[a.cmd]))


if __name__ == "__main__":
    main()
