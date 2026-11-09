---
name: change-impact-recon
description: Use when about to edit shared logic, schemas or widely used components; produces a consumer impact map, an invariant list and a focused regression set before any edit.
---

# Change Impact Recon

**Use when:** about to edit shared logic, schemas or widely used components. **Not for:** /preflight (blast radius of prod-adjacent operations), engineering:system-design (new design). This skill is a reusable consumer trace plus invariant map before an edit.

## Contract
- Inputs: the intended change (file, function, column, type or contract) and read access to the repo.
- Artifact: impact map (consumer | how it uses the behavior | affected? | evidence) and a focused regression set.
- Exit gate: relevant consumers are accounted for, or uncertainty explicitly limits the permitted change. Verdict: Verified | Failed | Blocked | Inconclusive, with evidence per criterion. Format the verdict with evidence-gate.
- Authority: read-only through the proposal. Steps that edit, migrate, deploy or write externally start only after {{APPROVER}} records a go; findings alone never authorize them.

## Fast path
Private helper or leaf component: grep for callers and imports, list them, name the one test that covers the change, done. Escalate only if a caller lives outside the file's module.

## Steps
1. **Change surface**: state exactly what behavior changes (inputs, outputs, side effects, defaults, error shapes), not which lines. Hands on: before/after behavior statement.
2. **Consumer trace**: find every consumer by search, not memory: direct imports, dynamic references, API routes, SQL and views, cron jobs, scripts, tests, docs that encode the behavior. Hands on: consumer table with file path and call pattern.
3. **Invariant map**: list what must not change: units, ordering, nullability, idempotency, auth boundary, row limits. Hands on: invariant | who relies on it.
4. **Collateral risk**: follow indirect paths: derived tables, caches, serialized data already stored, downstream readers of this output (e.g. one row cap that hit 7+ readers). Hands on: indirect path | risk | how to check.
5. **Bounded change plan**: smallest edit that satisfies the request; list anything deliberately left unchanged and why. Hands on: ordered edit list, with rollback note.
6. **Targeted regression**: pick the minimum tests or checks that exercise each affected consumer and invariant; add missing ones first. Hands on: regression set with pass condition.

## Escalate if
- A consumer is outside the repo, in prod data, or unreachable by search: report Blocked on that consumer and cap the change to what is provable.
- The change alters a persisted format or a DB object: use /preflight.
- The impact spans more than one deployable surface: run /preflight too.

## Skip if
- A pure addition with no existing consumer, or a rename fully handled by the compiler.
- A prior impact map for the same surface exists and the code has not moved (cite it).

## Stop rules
- An unaccounted consumer of a consequential invariant blocks the edit, not just the PR.
- Do not widen the edit to "tidy" a consumer found along the way; list it instead.

## Record
Impact map, invariants, the regression set and its result, and the consumers left unverified.
