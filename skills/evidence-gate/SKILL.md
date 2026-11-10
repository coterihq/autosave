---
name: evidence-gate
description: Use when a stage lists pass criteria and you must give a go/no-go; maps each criterion to evidence as pass, fail or unknown and returns one verdict.
---

# Evidence Gate

**Use when:** a plan, stage or release needs a go/no-go against explicit criteria. **Not for:** a review prompt; this gives no opinions and does not judge quality.

## Input
- Criteria: the list the stage must satisfy (written before looking at evidence).
- Evidence: observed items (command output, row counts, diffs, served SHA, test results), each with source and time. (Quick Save, https://coterihq.gumroad.com, checks the served SHA for you.)

## Output
| Criterion | Evidence | Result |
|---|---|---|
| <criterion> | <item + source + time, or none> | pass / fail / unknown |

Then one overall verdict: Verified | Failed | Blocked | Inconclusive.

## Rules
- no evidence = unknown, never pass.
- Evidence must be observed in this session or dated; a remembered or merged-status claim is unknown. e.g. "closed" claimed from merge status without checking the served prod SHA.
- Implementation evidence ("the widget moved") does not satisfy an outcome criterion ("the journey now presents X before the decision"); mark it unknown for the outcome.
- Evidence that contradicts another item makes both unknown until reconciled.
- A stale record (e.g. a GO record older than 24h) grants nothing.

## Verdicts
- Verified: every criterion pass.
- Failed: at least one criterion fail.
- Blocked: a criterion cannot be evaluated because access, approval or a dependency is missing.
- Inconclusive: no fail, but at least one unknown.
- Precedence when several apply: Failed, then Blocked, then Inconclusive.

## Stop rules
- Do not add criteria after seeing evidence; list them as a new gate.
- Do not advance on Inconclusive or Blocked; name the cheapest observation that would resolve each unknown.
- Gate output is read-only; it authorizes nothing by itself beyond the next stage it guards.

## Record
The table, the verdict, and the unknowns with the observation that would resolve each.
