---
name: system-correctness
description: Use when a number, behavior or permission is wrong or untrusted and you cannot yet tell which kind of failure it is; routes to one specialist skill or one discriminating observation.
---

# System Correctness (router)

Classify, then run only the relevant branch.

**Use when:** a correctness concern is stated but not yet typed. **Not for:** a known single bug (diagnosing-bugs) or a diff review (review).

## Branches

| Concern | Skill | Proposed first move |
|---|---|---|
| Displayed number wrong or untrusted | truth-to-screen-trace | Trace one output UI -> source, check units and freshness |
| Fails between components | cross-layer-contract-repair | Compare both sides of the one seam, add a boundary test |
| Permission, identity, private data or external action | security-boundary-proof | Call as an unauthorized actor, confirm denial at the server |
| Sources disagree (code, runtime, docs, reports) | evidence-conflict-resolution | Record context per source, run the separating observation |
| Slow | performance-bottleneck-proof | Capture a baseline before touching anything |
| Unclear | smallest discriminating investigation | One cheap observation that separates the candidate explanations |

## Escalate if
- The concern spans two branches (a wrong number caused by a seam): run the one nearest the symptom first, hand its artifact to the second.
- Any branch reaches an external write or prod change: stop for approval.

## Skip if
- The cause is already known and local: fix it with debug or diagnosing-bugs.

## Stop rules
- Name the chosen branch and the evidence that picked it before starting.
- If the discriminating observation cannot be run, report Inconclusive, not a guess.

Never run every branch.
