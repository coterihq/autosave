---
name: journey-quality
description: Use when a user journey feels wrong and you must pick the specialist; routes by symptom to one of four journey skills or one discriminating observation.
---

# Journey Quality (router)

Classify, then run only the relevant branch.

## Branch table
| Concern | Specialist skill | Proposed first move |
|---|---|---|
| Information is present but in the wrong order | decision-flow-surgery | Move the one misplaced evidence item before its decision, replay. |
| Capability exists but is not found at the moment of need | buried-capability-recovery | Add one contextual link at the moment of need, replay the task. |
| Interruption, retry or partial completion misbehaves | state-machine-hardening | List the suspect state's transitions, force the bad one in a scenario. |
| Too many competing tools, settings or nav entries | simplify-or-delete | Merge the duplicate into the canonical item, replay the task. |
| Unclear | Smallest discriminating investigation | One cheap observation that separates the candidate explanations (e.g. one fixture walk of the journey). |

## Escalate if
- Two branches both apply: run the one whose output the other needs first, usually decision-flow-surgery before buried-capability-recovery.
- The symptom is a wrong or untrusted number, not a journey problem (route to a correctness skill).

## Skip if
- The complaint is visual polish only; use ui-ux-pro-max-extras or design:design-critique.
- A single tab needs a differentiator promoted; use /hero-promote.

## Stop rules
- No observation of the real journey (fixtures or private-port harness, never a logged-in browser): stop as Blocked.
- A diagnosis alone is a valid end state; do not implement without a separate go.

## Never
Never run every branch. Pick one, record the verdict (Verified | Failed | Blocked | Inconclusive), then reassess.
