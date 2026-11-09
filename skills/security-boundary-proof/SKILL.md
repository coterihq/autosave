---
name: security-boundary-proof
description: Use when a feature touches identity, permissions, private data or external actions; produces an authority matrix, concrete abuse scenarios and denial-path tests.
---

# Security Boundary Proof

**Use when:** a change adds or alters who can see, change or trigger something, or sends data or actions outside the system. **Not for:** review (security/RLS/GRANT lens on a diff), engineering:code-review or /preflight (RLS and GRANT correctness); this proves the boundary holds under abuse, not that the diff reads well.

## Contract
- Inputs: the feature, its actors, the data and actions it exposes, read access to code and policy definitions.
- Artifact: authority matrix, abuse scenarios, denial-path tests.
- Exit gate: unauthorized operations are rejected at the enforcing boundary, not merely hidden in the UI. Verdict: Verified | Failed | Blocked | Inconclusive, with evidence per criterion. Format the verdict with evidence-gate.
- Authority: read-only through the proposal. Steps that edit, migrate, deploy or write externally start only after {{APPROVER}} records a go; findings alone never authorize them.
- Rule: an external write gets its own approval gate, never bundled into general implementation permission.

## Fast path
One endpoint or view: list actor and asset, find where authority is actually checked, call it as an unauthorized actor, confirm denial at the server or database, not the client; run it on a private-port harness with fixtures.

## Steps
1. **Asset and actor map**: list data, actions and secrets, and every actor (owner, other user, operator, service, anonymous). Hands on: asset by actor grid.
2. **Trust boundaries**: mark where input crosses from less to more trusted, and where a service role or definer privilege widens access. Hands on: boundary list with the enforcing layer named.
3. **Abuse cases**: write concrete scenarios (other user's id, replayed request, stale token, injected text, bulk read). Hands on: scenario list, each with expected denial.
4. **Permission trace**: for each case follow who initiates, whose data, and where authority is checked. Hands on: authority matrix, cell = enforced at (layer) or UNENFORCED.
5. **Containment**: for each UNENFORCED cell choose the narrowest enforcement at the owning boundary. Hands on: proposed control per gap, not yet applied.
6. **Negative tests**: one test per abuse case that asserts rejection. Hands on: test list, run results.

## Escalate if
- Data leaves via a definer view or service role path (e.g. definer-view data exposure).
- A secret appears in code, a doc or a log (e.g. a real key in a doc): stop and report location, do not echo the value.
- The feature performs an external write or moves money: separate approval gate.

## Skip if
- Purely cosmetic change with no data or action behind it.
- Local-only tooling with no shared data or network path.

## Stop rules
- Never test with real third-party credentials or another person's data; use fixtures and a private-port harness.
- No access to the enforcing layer: verdict Blocked.
- A UI hide is not a pass; require denial from the server or database.

## Record
Authority matrix, abuse list with results, which layer enforces each denial, accepted residual risks with owner, and what reopens the proof (new actor, new export, new role).
