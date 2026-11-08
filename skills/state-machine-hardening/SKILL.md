---
name: state-machine-hardening
description: Use when happy paths work but interruptions, retries or partial completion behave badly; produces a state-transition map, missing recovery paths and executable adversarial scenarios.
---

# State Machine Hardening

**Use when:** the flow works end to end, yet loading, stale, denied, partial or retried states are undefined or unsafe. **Not for:** engineering:testing-strategy (test planning), superpowers:test-driven-development (red-green loop). This adds a state inventory and invalid-transition hunt before tests are written.

## Contract
- Inputs: the flow's code or spec, and the actions it can trigger.
- Artifact: state-transition map, list of missing recovery paths, executable scenarios.
- Exit gate: each consequential state has a defined user interpretation and a safe next action. Verdict: Verified | Failed | Blocked | Inconclusive, with evidence per criterion. Format the verdict with evidence-gate.
- Authority: read-only through the proposal. Steps that edit, migrate, deploy or write externally start only after {{APPROVER}} records a go; findings alone never authorize them.

## Fast path
One flow, one suspect state: list its states, ask what evidence authorizes entering and leaving each, write one scenario that forces the bad transition, fix or record it.

## Steps
1. **State inventory**: list loading, empty, stale, disconnected, denied, partial, retrying, failed, plus the flow's own. Hands on: state list with user-visible meaning.
2. **Transition map**: for each permitted transition, name the evidence that authorizes it. Hands on: from -> to -> evidence -> expiry.
3. **Invalid-transition hunt**: find paths that skip evidence, replay after expiry, or double-fire. Hands on: invalid transition -> how reachable.
4. **Recovery design**: for each consequential state define what the user sees and the safe next action. Hands on: state -> interpretation -> next action.
5. **Adversarial replay**: write scenarios that interrupt, retry and half-complete. Hands on: scenario -> expected state -> result.

## Escalate if
- A state can trigger an external write or order without fresh evidence.
- Retry could duplicate a side effect (an order, a booked leg).
- Two sources hold the same state and can disagree (hand to evidence-conflict-resolution).

## Skip if
- The flow is read-only with no side effect and no expiry.
- The state set is already enumerated in a spec with tests.

## Stop rules
- Cannot run the scenarios safely (would touch prod or place real orders): stop as Blocked, write them but do not execute.
- Expiry or timeout values unknown: mark unknown, never assume a number.
- Undo a bad transition by status change, never by deleting rows that hold external system ids.

## Record
The transition map, each missing recovery path with verdict, scenarios and their results, and invalidation conditions (new state added, expiry changed). e.g. a stale GO record must grant nothing after 24h.
