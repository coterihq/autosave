#!/usr/bin/env python3
"""Statusline: model · budget pace · spend · context. Read-only (ledger + live session).
Live session cost and context % come from Claude Code's own statusline input
(cost.total_cost_usd, context_window.used_percentage); the transcript estimate is the fallback."""
import json, sys, datetime as dt
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import usage_guard as ug

try:
    hook = json.load(sys.stdin)
    budget, warn, down, ctx_warn, start_day = ug.cfg()
    today = dt.date.today()
    start, end = ug.cycle_bounds(today, start_day)
    led = ug.load_ledger(start, quarantine=False)
    sid = hook.get("session_id", "")
    tp = hook.get("transcript_path", "")
    native_cost = (hook.get("cost") or {}).get("total_cost_usd")
    pct = (hook.get("context_window") or {}).get("used_percentage")
    cost, ctx, model = (0.0, 0, "")
    if (native_cost is None or pct is None) and tp and Path(tp).is_file():
        cost, ctx, model = ug.session_stats(tp)
    if native_cost is not None:
        cost = float(native_cost)
    sessions = dict(led["sessions"]); sessions[sid] = cost
    spent = sum(sessions.values())
    pace = ug.pace_for(spent, budget, start, end, today)
    name = (hook.get("model") or {}).get("display_name") or model or "?"
    flag = " ▼" + (ug.TIER_DOWN[ug.tier(name)] or "") if pace >= down else (" !" if pace >= warn else "")
    ctx_txt = f"ctx {float(pct):.0f}%" if pct is not None else f"ctx {ctx//1000}k"
    print(f"{name} · {pace:.2f}x{flag} · ${spent:.0f}/${budget:.0f} · {ctx_txt}")
except Exception as ex:
    print(f"usage: err {ex}")
