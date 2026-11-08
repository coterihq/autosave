---
name: cross-layer-contract-repair
description: Use when each component passes its own checks but the system fails between components; produces a contract mismatch table, an ordered repair sequence and boundary tests.
---

# Cross-Layer Contract Repair

**Use when:** frontend, API, database, publisher/consumer, agent/tool or config/runtime each look correct alone and the failure appears at a seam. **Not for:** engineering:system-design (new design), engineering:testing-strategy (test planning) or migration-auditor (DB boundary only); this finds and repairs mismatched assumptions across seams.

## Contract
- Inputs: a failing or suspect operation that crosses at least two layers, access to both sides of each seam.
- Artifact: contract mismatch table, coordinated repair sequence, boundary tests.
- Exit gate: a representative operation succeeds end to end, including one failure path. Verdict: Verified | Failed | Blocked | Inconclusive, with evidence per criterion. Format the verdict with evidence-gate.
- Authority: read-only through the proposal. Steps that edit, migrate, deploy or write externally start only after {{APPROVER}} records a go; findings alone never authorize them.

## Fast path
One seam, one field: read both sides, state each side's assumption in a row, compare, fix the side that owns the contract, and add one boundary test that fails before and passes after.

## Steps
1. **Boundary map**: list the seams on the operation's path (frontend/API, API/DB, publisher/consumer, agent/tool, config/runtime). Hands on: ordered seam list.
2. **Contract extraction**: per seam record field semantics, optional vs required, versions, error shapes, ordering, and who owns the contract. Hands on: two-column table, producer vs consumer.
3. **Mismatch detection**: diff the columns; include silent ones (truncation, default values, dropped constraints). Hands on: mismatch table with severity and evidence.
4. **Compatibility plan**: order the repair so no intermediate state breaks a consumer (additive first, switch readers, remove old). Hands on: numbered sequence with the safe rollback point.
5. **Vertical-slice test**: drive one real operation through all seams, then one failure. Hands on: reproducible test or script.
6. **Contract lock**: add the narrowest test, type or check that fails on the next drift. Hands on: the test name and where it runs.

## Escalate if
- The mismatch spans a DB schema change plus deployed readers (e.g. a readers-vs-row-cap mismatch, a signup trigger vs a dropped unique): call migration-auditor before any apply.
- Two owners claim the same contract, or neither does.
- The repair order requires a window where old and new coexist in prod.

## Skip if
- Only one layer is involved: use diagnosing-bugs.
- The mismatch is a typo or missing import inside one module.

## Stop rules
- Do not repair a seam you have only read one side of.
- No reproducible failing operation: verdict Inconclusive, stop.
- Do not widen a type or loosen a check just to make the slice pass.

## Record
Mismatch table, chosen repair order, the boundary test, the contract owner per seam, and the condition that reopens it (version bump, new consumer).
