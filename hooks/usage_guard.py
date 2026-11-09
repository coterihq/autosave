#!/usr/bin/env python3
"""Claude Code Stop hook: track spend, warn on burn rate, recommend a model downgrade.

pace = (spent / budget) / (fraction of cycle elapsed); 1.0 = exactly on budget pace.
Config via env in ~/.claude/settings.json:
  CLAUDE_MONTHLY_BUDGET_USD (200)  CLAUDE_CYCLE_START_DAY (1)
  CLAUDE_WARN_PACE (0.8)  CLAUDE_DOWNGRADE_PACE (1.0)  CLAUDE_CONTEXT_WARN_TOKENS (150000)
"""
import json, os, sys, datetime as dt
from pathlib import Path

# $ per million tokens: (input, output). VERIFY BEFORE USE against
# https://docs.claude.com/en/docs/about-claude/pricing - prices change per model
# version (e.g. Opus 4/4.1 were 15/75; Opus 4.5+ list at 5/25). Unknown models
# fall back to the sonnet row. Add a row for any new tier you use.
PRICES = {"opus": (5.0, 25.0), "sonnet": (3.0, 15.0), "haiku": (1.0, 5.0)}
CACHE_READ_MULT, CACHE_WRITE_MULT, CACHE_WRITE_1H_MULT = 0.1, 1.25, 2.0
TIER_DOWN = {"opus": "sonnet", "sonnet": "haiku", "haiku": None}
LEDGER = Path.home() / ".claude" / "usage" / "ledger.json"


def tier(model):
    m = (model or "").lower()
    return next((t for t in PRICES if t in m), "sonnet")


def _usage_by_message(path):
    """Last usage per assistant message. Claude Code repeats one message's usage on several
    transcript lines (one per content block), keyed by message.id + requestId; lines with
    neither (older versions) each count once."""
    seen, model, last_ctx = {}, "", 0
    for i, line in enumerate(Path(path).open()):
        try:
            e = json.loads(line)
        except ValueError:
            continue
        msg = e.get("message") or {}
        u = msg.get("usage")
        if e.get("type") != "assistant" or not u:
            continue
        key = (msg.get("id"), e.get("requestId"))
        model = msg.get("model", model)
        seen[key if any(key) else i] = (model, u)
        last_ctx = (u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0)
                    + u.get("cache_creation_input_tokens", 0))
    return seen.values(), last_ctx, model


def _price(model, u):
    pin, pout = PRICES[tier(model)]
    cw = u.get("cache_creation_input_tokens", 0)
    cw_1h = min((u.get("cache_creation") or {}).get("ephemeral_1h_input_tokens", 0) or 0, cw)
    return (u.get("input_tokens", 0) * pin
            + u.get("cache_read_input_tokens", 0) * pin * CACHE_READ_MULT
            + (cw - cw_1h) * pin * CACHE_WRITE_MULT + cw_1h * pin * CACHE_WRITE_1H_MULT
            + u.get("output_tokens", 0) * pout) / 1e6


def session_stats(transcript):
    """(cost USD, last context tokens, last model). Cost includes subagent transcripts in
    <transcript dir>/<session>/subagents/*.jsonl; context and model come from the main one."""
    transcript = Path(transcript)
    entries, last_ctx, model = _usage_by_message(transcript)
    cost = sum(_price(m, u) for m, u in entries)
    for sub in sorted((transcript.parent / transcript.stem / "subagents").glob("*.jsonl")):
        cost += sum(_price(m, u) for m, u in _usage_by_message(sub)[0])
    return cost, last_ctx, model


def cfg():
    g = os.getenv
    return (float(g("CLAUDE_MONTHLY_BUDGET_USD", 200)), float(g("CLAUDE_WARN_PACE", 0.8)),
            float(g("CLAUDE_DOWNGRADE_PACE", 1.0)), int(g("CLAUDE_CONTEXT_WARN_TOKENS", 150000)),
            int(g("CLAUDE_CYCLE_START_DAY", 1)))


def cycle_bounds(today, start_day):
    if os.getenv("CLAUDE_CYCLE", "monthly") == "weekly":  # Mon-start week
        start = today - dt.timedelta(days=today.weekday())
        return start, start + dt.timedelta(days=7)
    d = min(start_day, 28)
    start = today.replace(day=d)
    if today < start:
        start = (start.replace(day=1) - dt.timedelta(days=1)).replace(day=d)
    end = (start.replace(day=28) + dt.timedelta(days=4)).replace(day=d)
    return start, end


def load_ledger(start):
    led = json.loads(LEDGER.read_text()) if LEDGER.exists() else {}
    if led.get("cycle_start") != start.isoformat():
        led = {"cycle_start": start.isoformat(), "sessions": {}}
    return led


def pace_for(spent, budget, start, end, today):
    elapsed = max((today - start).days + 1, 1) / (end - start).days
    return (spent / budget) / elapsed


HANDOFFS = Path.home() / ".claude" / "handoffs"


def write_handoff(tp, hook, ctx, model):
    """Deterministic handoff (no model call): goal, recent asks, files touched, last reply."""
    sid = hook.get("session_id", tp.stem)
    mark = HANDOFFS / f".done-{sid}"
    if mark.exists():
        return None
    asks, files, last = [], [], ""
    for line in tp.open():
        try:
            e = json.loads(line)
        except ValueError:
            continue
        c = (e.get("message") or {}).get("content")
        if e.get("type") == "user" and isinstance(c, str) and not c.startswith("<"):
            asks.append(c.strip()[:400])
        elif e.get("type") == "assistant" and isinstance(c, list):
            for b in c:
                if b.get("type") == "text" and b["text"].strip():
                    last = b["text"].strip()
                elif b.get("type") == "tool_use" and b.get("name") in ("Edit", "Write", "MultiEdit"):
                    f = (b.get("input") or {}).get("file_path")
                    if f and f not in files:
                        files.append(f)
    cwd = hook.get("cwd") or ""
    proj = Path(cwd).name or "session"
    now = dt.datetime.now()
    out = HANDOFFS / f"{now:%Y-%m-%d-%H%M}-{proj}-{sid[:8]}.md"
    HANDOFFS.mkdir(parents=True, exist_ok=True)
    body = [f"# Handoff — {proj} ({now:%Y-%m-%d %H:%M} local)",
            f"Auto-written at {ctx:,} tokens context on {model}. Session {sid}. Dir: {cwd}",
            "Any live data in the prior session is dated; re-fetch it before acting.",
            "", "## First ask (goal)", asks[0] if asks else "(none)",
            "", "## Last 5 asks"] + [f"- {a}" for a in asks[-5:]] + \
           ["", "## Files edited"] + ([f"- {f}" for f in files[-30:]] or ["- (none)"]) + \
           ["", "## Last assistant reply", last[:3000],
            "", "## Resume prompt", f"Read this handoff ({out}) and continue from the last ask. Confirm state before editing."]
    out.write_text("\n".join(body))
    mark.touch()
    return out


def main():
    hook = json.load(sys.stdin)
    tp = Path(hook.get("transcript_path", ""))
    if not tp.is_file():
        return
    budget, warn_pace, down_pace, ctx_warn, start_day = cfg()
    cost, ctx, model = session_stats(tp)
    today = dt.date.today()
    start, end = cycle_bounds(today, start_day)
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    led = load_ledger(start)
    led["sessions"][hook.get("session_id", tp.stem)] = round(cost, 4)
    LEDGER.write_text(json.dumps(led, indent=1))
    spent = sum(led["sessions"].values())
    pace = pace_for(spent, budget, start, end, today)
    msgs, t = [], tier(model)
    if pace >= down_pace and TIER_DOWN[t]:
        msgs.append(f"Over budget pace ({pace:.2f}x, ${spent:.2f}/${budget:.0f}). "
                    f"Switch {t} -> {TIER_DOWN[t]}: /model {TIER_DOWN[t]}")
    elif pace >= warn_pace:
        msgs.append(f"Budget pace {pace:.2f}x (${spent:.2f}/${budget:.0f}). Downgrade soon if this continues.")
    if ctx >= ctx_warn:
        h = write_handoff(tp, hook, ctx, model)
        msgs.append(f"Context {ctx:,} tokens. Handoff saved: {h}. Start a fresh session with it."
                    if h else f"Context {ctx:,} tokens. Handoff already saved; start a fresh session.")
    if msgs:
        print(json.dumps({"systemMessage": "[usage_guard] " + " | ".join(msgs)}))


if __name__ == "__main__":
    try:
        main()
    except Exception as ex:  # never block the session
        print(json.dumps({"systemMessage": f"[usage_guard] error: {ex}"}))
