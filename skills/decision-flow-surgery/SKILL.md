---
name: decision-flow-surgery
description: Use when the app holds all the needed information but shows it in the wrong order; produces a dependency-ordered decision map and a minimal reorder plan.
---

# Decision Flow Surgery

**Use when:** the information exists but the user meets it after the decision it should have informed. **Not for:** ui-ux-pro-max-extras (grades a running UI), design:design-critique (feedback only), /hero-promote (redesigns a tab around its differentiator). This adds a dependency-ordered decision map.

## Contract
- Inputs: the starting question, the screens/tabs/tools involved, and a way to view them (fixtures or a private-port harness, never a logged-in browser).
- Artifact: before/after sequence map, list of unsupported decisions, exact placement changes.
- Exit gate: every consequential decision is preceded by its required evidence. Verdict: Verified | Failed | Blocked | Inconclusive, with evidence per criterion. Format the verdict with evidence-gate.
- Authority: read-only through the proposal. Steps that edit, migrate, deploy or write externally start only after {{APPROVER}} records a go; findings alone never authorize them.

## Fast path
One screen, one decision: list what must be known before it, check where each item appears today, move the single misplaced item, replay the decision with no hidden knowledge.

## Steps
1. **Journey map**: write start question -> decisions -> intended outcome. Hands on: ordered decision list.
2. **Decision dependencies**: for each decision, list the evidence required first. Hands on: decision -> required-evidence table.
3. **Information sequence audit**: record where each evidence item appears today (within screens, between tabs, across tools). Hands on: evidence -> current location -> before/after decision column.
4. **Minimum reorder**: choose the smallest set of moves that repairs broken handoffs; prefer moving over adding. Hands on: exact placement changes, each tied to a decision.
5. **Journey verification**: walk the revised sequence as a user who knows nothing outside the screen. Hands on: per-decision pass | fail | unknown.

## Escalate if
- A required evidence item exists nowhere in the app (the gap is data, not order).
- Fixing one decision breaks the evidence order of another.
- Target environment/account names are missing on a step or proposal the decision depends on.

## Skip if
- The complaint is visual polish, copy or contrast, not order.
- The decision has no consequence (browsing, read-only exploration).
- A recent plan already fixed the order; read it first and check whether it holds.

## Stop rules
- No way to view the real screens safely: stop as Blocked, do not infer order from code alone.
- Evidence for a dependency is a guess: mark unknown, never pass.
- Do not redesign navigation or restyle; moves only.

## Record
The before/after sequence map, each unsupported decision with its verdict, the placement changes made or proposed, and what would invalidate the map (a layout change, a new tab, a renamed field).
