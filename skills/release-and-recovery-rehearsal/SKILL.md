---
name: release-and-recovery-rehearsal
description: Use when a change works locally but its rollout is consequential; produces a release checklist with observable success criteria and a rehearsed recovery path before any production action.
---

# Release and Recovery Rehearsal

**Use when:** a change works locally and the rollout (migration, config, deploy, shared data) is consequential. **Not for:** /preflight (pre-change risk check), engineering:deploy-checklist (generic list), scripts/deploy-prod.sh (the mechanism). This adds an explicit recovery choice, a rehearsal and halt conditions.

## Contract
- Inputs: the change, its diff, target environment, and current state of that environment (observed, not remembered).
- Artifact: release checklist with observable success criteria, halt conditions, and a rehearsed recovery path.
- Exit gate: forward deployment and recovery are both understood before production changes begin. Verdict: Verified | Failed | Blocked | Inconclusive, with evidence per criterion. Format the verdict with evidence-gate.
- Authority: read-only through the proposal. Steps that edit, migrate, deploy or write externally start only after {{APPROVER}} records a go; findings alone never authorize them. Any prod action needs explicit approval from {{APPROVER}}.

## Fast path
Reversible, no schema or config change, nothing else in flight: state the success signal, state the revert command, get approval, release, observe once.

## Steps
1. **Classify**: schema, config, data, UI-only, or engine behavior; reversible or not. Hands on: class + reversibility line.
2. **Rollout dependencies**: config, migrations, compatibility window, ordering, other in-flight deploys or PRs. Check migration numbers by name and for collisions on main. Hands on: ordered dependency list.
3. **Recovery design**: choose explicitly rollback, restoration, or forward fix, and say why. Void by status, never delete rows holding external system ids. Hands on: recovery plan with the exact trigger.
4. **Rehearse**: run the forward and recovery steps against a named non-prod target (a DB branch, a local DB or a fixture), never prod; a migrate command that targets the remote project is not a rehearsal. Hands on: rehearsal log.
5. **Approval**: present checklist, risk, recovery to {{APPROVER}}. Hands on: approval recorded.
6. **Bounded release**: halt conditions written first (e.g. error signal, disk, a second deploy starting). Confirm the served SHA, not merge status. Hands on: release log.
7. **Observe**: check the success criteria against observed output, naming the environment/account on every step checked; verdict per criterion. Hands on: observation table.

## Escalate if
- Recovery is irreversible or only a forward fix exists.
- Another deploy, migration or auto-merge could land during the window (e.g. concurrent prod deploys plus disk-full; auto-merge firing before a pushed fix).
- Environment state differs from what the plan assumed.

## Skip if
- No production surface is touched.
- The change is a doc-only edit.

## Stop rules
- No approval: do not touch prod.
- Recovery path untested and change irreversible: Blocked.
- Free disk or process state not checked before deploy: check first.

## Record
Classification, chosen recovery and rationale, rehearsal result, approval, served SHA, observation verdicts, and what would invalidate the checklist.
