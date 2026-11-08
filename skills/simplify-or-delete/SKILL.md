---
name: simplify-or-delete
description: Use when the app has accumulated redundant tools, settings, abstractions or navigation; produces a subtraction plan showing what disappears and where each essential capability remains.
---

# Simplify or Delete

**Use when:** overlapping tools, settings, abstractions or nav entries compete and nobody can say which one is canonical. **Not for:** a code-bloat audit, engineering:tech-debt (debt prioritization). This covers UI, tool and setting overlap; it pairs with buried-capability-recovery (one promotes, one subtracts).

## Contract
- Inputs: the overlapping set, the tasks each item serves, and the dependencies on each.
- Artifact: subtraction plan (what disappears, where essential capability remains).
- Exit gate: required tasks remain possible, dependencies are addressed, removal is reversible where appropriate. Verdict: Verified | Failed | Blocked | Inconclusive, with evidence per criterion. Format the verdict with evidence-gate.
- Authority: read-only through the proposal. Steps that edit, migrate, deploy or write externally start only after {{APPROVER}} records a go; findings alone never authorize them.

## Fast path
Two items, one purpose: confirm what each does that the other does not, grep consumers of the loser, merge into the winner, replay the task.

## Steps
1. **Overlap inventory**: list items that serve the same task. Hands on: task -> items -> owner.
2. **Unique-value check**: for each item name what only it does. Hands on: item -> unique value or none.
3. **Dependency and usage evidence**: trace links, deep links, readers, settings and scheduled callers; gather usage data if it exists. Hands on: item -> consumers -> usage evidence (present | absent | unknown).
4. **Decide**: per item choose merge, demote, remove or retain, with reason. Hands on: plan table, one verdict per row, reversibility noted.
5. **Preservation check**: replay each required task on the reduced set. Hands on: task -> still possible pass | fail | unknown.

## Escalate if
- An item holds data or history that would be lost (migrate or archive first).
- Removal touches a permission, billing or compliance path.
- Consumers outside the repo may exist (webhooks, bookmarks, cron).

## Skip if
- Items look similar but serve different tasks per step 2.
- The overlap is the deliberate redundancy of a safety path.

## Stop rules
- Lack of usage evidence is not evidence of lack of usage: unknown usage means retain or demote, never remove.
- never delete rows holding external system ids; void by status.
- No removal without a named place where the capability remains.

## Record
The subtraction plan, retained items with the reason, reversal steps, and what would invalidate it (a consumer found later).
