#!/usr/bin/env python3
"""Trigger test for an INSTALLED skill: runs `claude -p` per query and checks whether the first turn calls Skill(<name>).

skill-creator's eval loop can't test an installed skill (it looks for a temp copy, and the real one wins). This can.
Usage: probe.py --skill plan-redteam --eval-set evals.json [--runs 1] [--workers 4] [--out DIR] [--cwd ~]
Eval set: [{"query": "...", "should_trigger": true}, ...]
Limit: first turn only (--max-turns 1); a skill called after a Bash/ToolSearch step is not seen.
"""
import argparse, concurrent.futures as cf, json, pathlib, subprocess, time

def run_one(query, skill, cwd, timeout):
    try:
        p = subprocess.run(["claude", "-p", query, "--output-format", "stream-json", "--verbose", "--max-turns", "1"],
                           cwd=cwd, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=timeout)
        out = p.stdout
    except subprocess.TimeoutExpired as e:
        out = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
    first, skills = None, []
    for line in out.splitlines():
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        if ev.get("type") != "assistant":
            continue
        for c in ev["message"].get("content", []):
            if c.get("type") == "tool_use":
                first = first or c["name"]
                if c["name"] == "Skill":
                    skills.append(c["input"].get("skill") or "")
    hit = any(s == skill or s.endswith(":" + skill) for s in skills)
    return {"first_tool": first, "skills": skills, "triggered": hit}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skill", required=True)
    ap.add_argument("--eval-set", required=True)
    ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--timeout", type=int, default=180)
    ap.add_argument("--cwd", default=str(pathlib.Path.home()))
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    items = json.load(open(a.eval_set))
    out = pathlib.Path(a.out or f"{a.skill}-trigger-{time.strftime('%Y%m%d-%H%M%S')}")
    out.mkdir(parents=True, exist_ok=True)
    jobs = [(i, r) for i in range(len(items)) for r in range(a.runs)]
    res = {i: [] for i in range(len(items))}
    with cf.ThreadPoolExecutor(a.workers) as ex:
        futs = {ex.submit(run_one, items[i]["query"], a.skill, a.cwd, a.timeout): i for i, _ in jobs}
        for f in cf.as_completed(futs):
            res[futs[f]].append(f.result())
    rows, tp, fp, fn, tn = [], 0, 0, 0, 0
    for i, it in enumerate(items):
        rate = sum(r["triggered"] for r in res[i]) / len(res[i])
        trig = rate >= 0.5
        exp = bool(it["should_trigger"])
        tp += trig and exp; fn += (not trig) and exp; fp += trig and not exp; tn += (not trig) and not exp
        rows.append({"query": it["query"], "should_trigger": exp, "trigger_rate": rate, "runs": res[i]})
        mark = "ok  " if trig == exp else ("MISS" if exp else "FALSE")
        print(f"{mark:5} {rate:4.0%}  {'+' if exp else '-'}  {it['query'][:80]}")
    summary = {"skill": a.skill, "runs": a.runs, "tp": tp, "fn": fn, "fp": fp, "tn": tn,
               "recall": tp / (tp + fn) if tp + fn else None, "false_trigger_rate": fp / (fp + tn) if fp + tn else None}
    json.dump({"summary": summary, "rows": rows}, open(out / "results.json", "w"), indent=1)
    print(f"\nrecall {tp}/{tp+fn} · false triggers {fp}/{fp+tn} · first turn only · results: {out}/results.json")

if __name__ == "__main__":
    main()
