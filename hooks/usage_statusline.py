#!/usr/bin/env python3
"""Statusline: model · budget pace · spend · context. Read-only (ledger + live session)."""
import json, sys, datetime as dt
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import usage_guard as ug

try:
    hook = json.load(sys.stdin)
    budget, warn, down, ctx_warn, start_day = ug.cfg()
    today = dt.date.today()
    start, end = ug.cycle_bounds(today, start_day)
    led = ug.load_ledger(start)
    sid = hook.get("session_id", "")
    tp = hook.get("transcript_path", "")
    cost, ctx, model = ug.session_stats(tp) if tp and Path(tp).is_file() else (0.0, 0, "")
    sessions = dict(led["sessions"]); sessions[sid] = cost
    spent = sum(sessions.values())
    pace = ug.pace_for(spent, budget, start, end, today)
    name = (hook.get("model") or {}).get("display_name") or model or "?"
    flag = " ▼" + (ug.TIER_DOWN[ug.tier(name)] or "") if pace >= down else (" !" if pace >= warn else "")
    print(f"{name} · {pace:.2f}x{flag} · ${spent:.0f}/${budget:.0f} · ctx {ctx//1000}k")
except Exception as ex:
    print(f"usage: err {ex}")
