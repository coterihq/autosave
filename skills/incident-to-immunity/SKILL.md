---
name: incident-to-immunity
description: Use after a bug's cause is confirmed and the fix has a regression test; produces sibling-scan results and one narrow prevention rule, or an explicit no-rule verdict.
---

# Incident to Immunity

**Use when:** a bug is fixed and you want to know whether the same mechanism lives elsewhere. **Not for:** diagnosing-bugs / superpowers:systematic-debugging (contain, reproduce, find the cause, fix, regression test), incident-to-eval and /postmortem (turn it into an eval case). This starts where they stop.

## Contract
- Inputs: the confirmed cause, the fix, and a regression test with before/after output (from diagnosing-bugs or equivalent). Missing any of these: go back, do not scan on a guess.
- Artifact: list of related locations with a verdict each, plus one narrowly scoped prevention rule or the words "no rule".
- Exit gate: related instances checked and the original failure confirmed covered. Verdict: Verified | Failed | Blocked | Inconclusive, with evidence per criterion. Format the verdict with evidence-gate.
- Authority: read-only through the proposal. Steps that edit, migrate, deploy or write externally start only after {{APPROVER}} records a go; findings alone never authorize them.

## Fast path
One grep for the mechanism, none found: write "no rule", stop.

## Steps
1. **Confirm inputs**: cause stated, fix merged or staged, regression test fails before and passes after. Hands on: the three artifacts, or the missing one named.
2. **Name the mechanism**: one line that generalizes the cause beyond this instance (e.g. "a reader assumes fewer than 1,000 rows"; "premium is per-share here, per-contract there"). Hands on: mechanism line.
3. **Sibling scan**: search for the same mechanism elsewhere. Hands on: location list, each with verdict (affected / safe / unknown) and evidence.
4. **Prevention rule**: only if the scan justifies it, one narrow reusable test or lint. Otherwise "no rule". Hands on: rule or "no rule".

## Escalate if
- The scan finds instances in prod-adjacent paths: fix them as separate changes through release-and-recovery-rehearsal.
- The mechanism is a design flaw, not a defect: propose it separately; do not refactor here.

## Skip if
- A one-off typo with no shared mechanism.
- The cause is unknown: diagnose first.

## Stop rules
- Do not turn an incident into a broad refactor.
- Do not claim covered without the before/after test output.
- never delete rows holding external system ids; void by status.

## Record
Mechanism line, sibling list with verdicts, prevention rule or "no rule", and what would reopen it.
