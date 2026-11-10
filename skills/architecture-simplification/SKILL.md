---
name: architecture-simplification
description: Use when every change touches too many places; produces one targeted seam extraction plan from observed change coupling, or a do-not-abstract-yet verdict. Never a rewrite.
---

# Architecture Simplification

**Use when:** every change touches too many places. **Not for:** codebase-design (deep-module vocabulary), pathfinder (map and unify), engineering:tech-debt (prioritize debt). This skill picks one boundary from observed change history and extracts across it, or declines.

## Contract
- Inputs: git history or a list of recent concrete changes, and the files each touched.
- Artifact: coupling map, one chosen seam, incremental extraction steps, behavior-equivalence checks, or a do-not-abstract-yet verdict.
- Exit gate: reduces a demonstrated source of coupling while preserving required behavior. Verdict: Verified | Failed | Blocked | Inconclusive, with evidence per criterion. Format the verdict with evidence-gate.
- Authority: read-only through the proposal. Steps that edit, migrate, deploy or write externally start only after {{APPROVER}} records a go; findings alone never authorize them.

## Fast path
One recurring co-change cluster with an obvious owner: name the cluster, name the seam, list three extraction steps, the equivalence check, done.

## Steps
1. **Change history scan**: take the last several concrete changes and list which files each touched. Evidence is observed co-change, not taste. Hands on: change | files touched.
2. **Coupling map**: find files that change together repeatedly and the dependency that forces it (duplicated rule, shared type, copied constant, pass-through layer). Hands on: cluster | forcing dependency | count of changes.
3. **Responsibility audit**: for the top cluster, state what each member owns and where one concern is split or two are fused. Hands on: owner | responsibility | misplaced item.
4. **Seam selection**: choose exactly one boundary. Write its interface in terms callers need. If no seam is justified by at least repeated co-change, return "do not abstract yet" and name what evidence would change that. Hands on: seam statement or defer verdict.
5. **Incremental extraction**: ordered steps each leaving the tree green and shippable; old and new paths coexist until callers move. Hands on: step list with check after each.
6. **Behavior equivalence**: tests or recorded outputs that must match before and after; run them before the first step to confirm a baseline. Hands on: equivalence set and result.

## Escalate if
- The seam crosses a DB schema or API contract: also use change-impact-recon and /preflight.
- Equivalence cannot be established: report Blocked, do not extract.

## Skip if
- Fewer than two repeated co-changes: the pain is a single event, not a structure.
- Code is slated for deletion.

## Stop rules
- One seam per run. A second boundary is a new run.
- No rewrite, no new framework, no abstraction for a single caller.
- Do not start extraction without a baseline equivalence check that passes.

## Record
Change evidence, chosen seam or defer verdict with reopening evidence, step list status, equivalence result.
