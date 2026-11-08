---
name: performance-bottleneck-proof
description: Use when the app feels slow and you need a justified fix; produces a baseline, critical-path trace, single isolated intervention and a before/after measurement under stated conditions.
---

# Performance Bottleneck Proof

**Use when:** something feels slow and an intervention must be justified by measurement. **Not for:** diagnosing-bugs (has a performance-regression mode; this adds baseline-first discipline and separate claims).

## Contract
- Inputs: one named slow task, the environment it runs in, a way to measure it.
- Artifact: reproducible measurement, proposed cause, before/after comparison under stated conditions.
- Exit gate: the target measure improves without violating correctness or usability constraints. Verdict: Verified | Failed | Blocked | Inconclusive, with evidence per criterion. Format the verdict with evidence-gate.
- Authority: read-only through the proposal. Steps that edit, migrate, deploy or write externally start only after {{APPROVER}} records a go; findings alone never authorize them.

## Fast path
Single endpoint or query with an obvious cost: measure it three times, change one thing, measure three times, compare, record.

## Steps
1. **Define the slow task**: one user-visible action, start and end events, a target. Hands on: task definition.
2. **Baseline**: measure before touching anything; record environment, data size, cold vs warm, run count. Hands on: baseline table.
3. **Critical-path trace**: break the task into timed segments (network, API, DB, render); find where time actually goes. Hands on: segment timings.
4. **Bottleneck hypothesis**: one cause, stated so a measurement can refute it. Hands on: hypothesis line.
5. **Isolated intervention**: change one variable only; on a fixture harness on a private port, foregrounded; never a hidden pane (the dashboard never loads there) or a logged-in browser. Hands on: diff.
6. **Repeat measurement**: same conditions, same run count; compare to baseline; confirm results are still correct. Hands on: before/after table.

## Escalate if
- The baseline is noisy enough that the change is within variance.
- The fix trades correctness (staleness, truncation) for speed.
- Host contention, not code, explains the time (e.g. fetch aborts from local contention).

## Skip if
- No measurable task can be named.
- The slowness is a one-off outage, not a pattern.

## Stop rules
- Keep three claims separate: "feels faster", measured latency, resource use. Report each only with its own evidence.
- No baseline: no intervention.
- Do not stack multiple changes before measuring.

## Record
Task, conditions, baseline, trace, hypothesis, intervention, after numbers, verdict, and the conditions under which the result would not hold.
