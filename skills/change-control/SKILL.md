---
name: change-control
description: Use when a consequential change spans several agents, a rollout, drift or an unproven plan and you must pick the discipline; routes to exactly one specialist skill.
---

# Change Control

Classify, then run only the relevant branch.

| Situation | Specialist skill | Proposed first move |
|---|---|---|
| Consequential rollout (migration, deploy, shared data) | release-and-recovery-rehearsal | Success signal, tested recovery, approval, observe |
| Session drifting, compacted or being handed off | context-loss-recovery | Re-observe, ledger, invalidate stale artifacts, cold-start check |
| Bug just fixed (cause known) | incident-to-immunity | Repro, fix, regression test, sibling scan |
| About to edit shared logic or schema | change-impact-recon | Consumer trace, invariants, bounded plan |
| Plausible but unproven plan | assumption-breaker | Rank assumptions, smallest discriminating test |
| Shipped, "done" must mean more than merged | outcome-validation | Success condition, post-change observation, verdict |
| Unclear | smallest discriminating investigation | One cheap observation that separates the candidate explanations |

## Escalate if
- Two branches both apply: run them in this order, one at a time: assumption-breaker, change-impact-recon, context-loss-recovery, release-and-recovery-rehearsal, incident-to-immunity, outcome-validation.
- The cheap observation does not separate the candidates: report Inconclusive and ask.

## Skip if
- The change is trivial, local and reversible: just do it.
- A specialist skill is already running for this situation.

## Stop rules
- Investigation never authorizes change: diagnose, propose, get {{APPROVER}}'s recorded go (the authority gate), then implement, then verify independently.
- A branch may end with a diagnosis and no changes.
- Name the target environment/account on every step or proposal; no external writes without a separate approval.

Never run every branch.

## Parallel writing boundary
This free kit does not include a parallel-agent coordination workflow. Do not dispatch concurrent writers without a separately reviewed coordination plan; use one writer at a time otherwise.
