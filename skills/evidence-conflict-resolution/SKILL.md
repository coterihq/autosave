---
name: evidence-conflict-resolution
description: Use when code, runtime behavior, docs or agent reports disagree about the same fact; produces a contradiction table with resolved findings and explicitly remaining unknowns.
---

# Evidence Conflict Resolution

**Use when:** two or more sources give incompatible answers and a decision depends on which is right. **Not for:** diagnosing-bugs or superpowers:systematic-debugging (one bug, one cause); this adjudicates multiple sources about one claim and keeps what stays unknown.

## Contract
- Inputs: the conflicting statements with their sources.
- Artifact: contradiction table (claim, sources, context, status) with resolved findings and remaining unknowns.
- Exit gate: no consequential decision silently depends on an unresolved contradiction. Verdict: Verified | Failed | Blocked | Inconclusive, with evidence per criterion. Format the verdict with evidence-gate.
- Authority: read-only through the proposal. Steps that edit, migrate, deploy or write externally start only after {{APPROVER}} records a go; findings alone never authorize them.

## Fast path
Two sources, one claim: record environment, version and timestamp for each, name the two explanations, run the one cheapest observation that separates them, and state the result.

## Steps
1. **Conflict inventory**: write each contradiction as one claim with the sources on each side. Hands on: table rows, one per claim.
2. **Evidence context**: before choosing what to trust, record environment, build or SHA, timestamp, scope and who or what produced each item. Hands on: context columns filled for every source.
3. **Competing explanations**: list the explanations that would make both sources honest (different build, stale cache, fixture vs live, different scope). Hands on: explanation list per row.
4. **Targeted observation**: pick the one observation that separates the explanations; run it. Hands on: observation, command or query, and its raw result with timestamp.
5. **Reconcile or preserve uncertainty**: mark each row Resolved (with the evidence) or Unresolved (with who or what would resolve it). Hands on: final table plus decision impact per unresolved row.

## Example
A test passes but the running UI fails: compare config, build, fixtures and execution path. Neither source is universally authoritative; the one whose context matches the decision's context wins.

## Escalate if
- An unresolved row gates a prod change, a trade, or a "closed" claim (e.g. "audit closed" from merge status without checking the served prod SHA).
- Sources are agent reports with no observable artifact behind them.

## Skip if
- One source is plainly stale by timestamp and nothing depends on it.
- The disagreement is about taste or priority, not a checkable fact.

## Stop rules
- Do not average sources or pick the newest by default.
- Do not treat an agent's report as evidence without the artifact it cites.
- If the separating observation cannot be run, mark Inconclusive and name the blocker.

## Record
Contradiction table with context columns, the observations and raw results, remaining unknowns with the decisions they block, and what would reopen a resolved row.
