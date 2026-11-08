#!/usr/bin/env python3
"""Weekly digest: cycle spend, pace vs budget, top 3 costly sessions.
Writes ~/.claude/usage/digest-YYYY-MM-DD.md and prints a one-line summary.
On macOS, pass --notes to also post it to Apple Notes.
Schedule it yourself (cron/launchd), e.g. Sundays:  5 18 * * 0 python3 ~/.claude/hooks/usage_digest.py"""
import glob, os, subprocess, sys, datetime as dt
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import usage_guard as ug

budget = ug.cfg()[0]
today = dt.date.today()
start, end = ug.cycle_bounds(today, ug.cfg()[4])
home_slug = str(Path.home()).replace("/", "-")
rows, tiers = [], {}
for f in glob.glob(str(Path.home() / ".claude/projects/*/*.jsonl")):
    if dt.date.fromtimestamp(os.path.getmtime(f)) < start:
        continue
    cost, ctx, model = ug.session_stats(f)
    proj = Path(f).parent.name.replace(home_slug + "-", "") or "?"
    rows.append((cost, proj, Path(f).stem[:8], ctx, ug.tier(model)))
    tiers[ug.tier(model)] = tiers.get(ug.tier(model), 0) + cost
spent = sum(r[0] for r in rows)
pace = ug.pace_for(spent, budget, start, end, today)
top = sorted(rows, reverse=True)[:3]
md = [f"# Claude usage: cycle starting {start:%b %d}", "",
      f"- Spent: ${spent:,.2f} (API-equivalent estimate) of ${budget:,.0f} budget",
      f"- Pace: {pace:.2f}x  (1.0 = exactly on budget pace)",
      f"- Sessions: {len(rows)}",
      "- By tier: " + ", ".join(f"{k} ${v:,.2f}" for k, v in sorted(tiers.items(), key=lambda x: -x[1])),
      "", "## Top 3 sessions"] + \
     [f"- ${c:,.2f}: {p} ({s}), {t}, peak ctx {x // 1000}k" for c, p, s, x, t in top] + \
     ["", "Estimates from local transcripts; the PRICES table in usage_guard.py is approximate."]
out = Path.home() / ".claude/usage" / f"digest-{today:%Y-%m-%d}.md"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text("\n".join(md) + "\n")
if "--notes" in sys.argv and sys.platform == "darwin":
    body = "<br>".join(md).replace('"', '\\"')
    subprocess.run(["osascript", "-e", f'tell application "Notes" to make new note with properties {{body:"{body}"}}'], check=False)
print(f"digest written to {out}: ${spent:,.2f}, {pace:.2f}x, {len(rows)} sessions")
