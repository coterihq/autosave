---
name: safe-agent-execution
description: Use when several agents could work in parallel but may collide or exceed authority; produces a scope contract, execution graph, ownership map and verification ledger.
---

# Safe Agent Execution

**Use when:** parallel agents or threads will touch one repo or folder. **Not for:** superpowers:dispatching-parallel-agents / subagent-driven-development (how to dispatch; this adds a scope and ownership contract and an integration gate).

## Contract
- Inputs: the task, the repo state (branch, worktree, uncommitted work), the list of files and operations the task may touch.
- Artifact: scope contract, execution graph, ownership map, verification ledger.
- Exit gate: no ownership conflicts, no unauthorized changes, no completion claim without evidence. Verdict: Verified | Failed | Blocked | Inconclusive, with evidence per criterion. Format the verdict with evidence-gate.
- Authority: read-only through the proposal. Steps that edit, migrate, deploy or write externally start only after {{APPROVER}} records a go; findings alone never authorize them.

## Fast path
Single narrow task with disjoint files: write the scope contract (3 lines), give each agent one owner and one file set, run, diff each result against the contract, record the ledger. Skip the graph.

## Steps
1. **Scope contract**: list permitted files, permitted operations, prohibited actions (deploy, migration apply, external write, broad staging). Hands on: contract table.
2. **Dependency partition**: split work into independent vs sequential. Parallelism is a scheduling decision, not the default; if the split is unclear, run sequentially. Hands on: execution graph with phases.
3. **Ownership assignment**: one exclusive owner per shared interface, schema, doc row and conflict-prone file. Give each agent its own worktree or branch. Hands on: file -> owner map.
4. **Bounded execution**: make phases resumable (a long single agent can die on a usage limit). Each agent reports changed assumptions and blockers, not just results. Hands on: per-agent report.
5. **Integration review**: diff every agent's changes against the contract; flag any file outside its owner's set; stage by explicit path only. Hands on: violations list.
6. **Evidence gate**: for each completion claim, attach the command and output that backs it, or mark it unknown. Hands on: verification ledger.

## Escalate if
- Two agents need the same file or interface and no owner can be assigned.
- A result touches files outside the contract.
- An agent proposes a migration, deploy or external write.
- Target environment/account names are missing from any step or proposal that agents produced.

## Skip if
- One agent, one small change: just do it.
- Agents are read-only investigators with no writes.

## Stop rules
- No worktree isolation for concurrent writers: stop (e.g. shared-checkout sweeps, a worktree taken over mid-session, `git add -A` committing a node_modules symlink).
- Contract not written before dispatch: stop and write it.
- Never use a logged-in browser; use fixtures or a private-port harness.

## Record
Scope contract, ownership map, what each agent changed, which claims were verified vs unknown, and any contract violation with its resolution.
