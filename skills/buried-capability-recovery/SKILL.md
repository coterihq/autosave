---
name: buried-capability-recovery
description: Use when powerful features exist but users do not meet them at the moment of need; produces a capability-to-placement matrix with concrete moves or an explicit leave-alone verdict.
---

# Buried Capability Recovery

**Use when:** a capability exists and works, but the person who needs it never finds it at the moment of need. **Not for:** /hero-promote (promotes the differentiator, demotes the rest). This adds a capability inventory, moment-of-need mapping and an explicit "leave alone" verdict.

## Contract
- Inputs: the app's actual capabilities (from code, routes and APIs, not nav labels) and the tasks users attempt.
- Artifact: capability-to-placement matrix with concrete moves.
- Exit gate: important tools are discoverable at the point of need without duplicate interfaces. Verdict: Verified | Failed | Blocked | Inconclusive, with evidence per criterion. Format the verdict with evidence-gate.
- Authority: read-only through the proposal. Steps that edit, migrate, deploy or write externally start only after {{APPROVER}} records a go; findings alone never authorize them.

## Fast path
One known-buried capability: name the moment it is needed, check what the user sees at that moment, add one contextual link or relocate it, replay the task.

## Steps
1. **Capability inventory**: list what the app can actually do. Hands on: capability -> where it lives -> who calls it.
2. **Discoverability audit**: tag each as hidden, duplicated, misnamed or disconnected. Hands on: capability -> tag -> evidence.
3. **Moment-of-need map**: for each real task, name the screen and decision where the capability would help. Hands on: moment -> capability needed -> present? (yes/no).
4. **Surface or link**: per capability pick one of promote, relocate, contextually link, consolidate, or leave alone. Hands on: the matrix, one chosen move per row with the reason.
5. **Task replay**: run each task with the moves applied, no prior knowledge. Hands on: task -> found at moment of need pass | fail | unknown.

## Escalate if
- Two surfaces for one capability would remain after the move (hand to simplify-or-delete).
- The moment of need sits in a different room or app than the capability.
- Surfacing it needs new data or a new permission.

## Skip if
- Users already reach it from the moment of need (leave alone is a valid verdict).
- The capability is dormant or shelved by decision; do not resurface it unprompted.
- The issue is order within one screen (use decision-flow-surgery).

## Stop rules
- No evidence of the moment of need: mark unknown, do not invent a task.
- Never add a second interface to fix discoverability; link to the one that exists.

## Record
The matrix, each leave-alone verdict with reason, moves made or proposed, and invalidation conditions (capability renamed, room restructured).
