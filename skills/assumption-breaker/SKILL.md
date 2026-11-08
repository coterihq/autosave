---
name: assumption-breaker
description: Use when about to implement a plausible but unproven solution; produces an assumption ledger ranked by blast radius and the smallest discriminating test of the pivotal one.
---

# Assumption Breaker

**Use when:** about to implement a plausible but unproven solution. **Not for:** grilling (interviews {{APPROVER}} about the plan), superpowers:brainstorming (designs options). This skill ranks assumptions by how much work they invalidate and tests the top one.

## Contract
- Inputs: the proposed solution and the claim it rests on, in words.
- Artifact: assumption ledger (claim | evidence | blast radius if wrong | status) plus the smallest test of the pivotal assumption.
- Exit gate: the pivotal assumption is supported, explicitly accepted as uncertain, or the plan changes. Verdict: Verified | Failed | Blocked | Inconclusive, with evidence per criterion. Format the verdict with evidence-gate.
- Authority: read-only through the proposal. Steps that edit, migrate, deploy or write externally start only after {{APPROVER}} records a go; findings alone never authorize them.

## Fast path
One obvious load-bearing assumption: state it, name the counterexample that would break it, run the one-query or one-read check, then proceed, revise or reject.

## Steps
1. **Claim extraction**: list every "this works because" in the plan, including unstated ones about data shape, units, row counts, ordering, freshness and who calls it. Hands on: numbered claim list.
2. **Assumption ranking**: for each, ask what work is wasted if it is false. Rank by that, not by doubt. Hands on: ledger sorted by blast radius.
3. **Counterexample search**: for the top three, look for the case that breaks them in code, data or docs (e.g. a per-share vs per-contract premium mismatch, a 1,000-row cap truncating a reader). Hands on: counterexample found | none found | not checkable.
4. **Discriminating test**: design the smallest observation that separates "true" from "false" for the pivotal claim: one query, one fixture, one read of the source. Hands on: test plus expected result under each hypothesis.
5. **Decide**: proceed (supported), proceed-with-accepted-risk (named, in the ledger), revise, or reject. Hands on: decision line plus ledger update.

## Escalate if
- The pivotal assumption cannot be tested without a prod write or external call: stop, ask {{APPROVER}}.
- Two or more high-blast-radius assumptions fail: the plan, not the detail, is wrong; return to the target outcome.

## Skip if
- The change is trivial and fully reversible.
- The assumption was already verified this session at the current build (cite it).

## Stop rules
- Never test an assumption by running the full implementation.
- Never use a logged-in browser; use fixtures or a private-port harness.
- "Looks fine" is not evidence; no evidence means status unknown.

## Record
The ledger, the test and its result, the decision, and the condition that would invalidate it (e.g. schema change, new data source).
