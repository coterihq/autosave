---
name: plan-redteam
description: Use when {{APPROVER}} hands over a plan, spec, roadmap or strategy (a file, a doc, or written out in the message itself) and wants it attacked before acting on it: red-team it, adversarially audit it, poke holes, stress-test it, play devil's advocate on it, or check it for contradictions and feasibility. Review only, no build. Not for critiquing writing (cover letters, prompts), designs, a single trade or decision already made, or code/PR reviews.
---

# Plan Red-Team

**Use when:** a plan already exists and {{APPROVER}} wants only the adversarial review. **Not for:** grilling (interviews {{APPROVER}} to sharpen a spec), a build workflow (concept to merged PR), assumption-breaker alone (one claim). Calls assumption-breaker and evidence-gate as sub-steps; inline fallbacks if not installed.

## Contract
- Inputs: the plan (file, paste or link) and its stated goal. No plan text = ask for it; never audit from a summary.
- Artifact: severity-ranked findings table + assumption ledger + verdict.
- Exit gate: every Critical/High finding has a concrete fix, or {{APPROVER}} accepts it as risk in writing.
- Authority: read-only. Never edit the plan, code, data or external systems; findings authorize nothing.
- Independence: the reviewer must not be the plan's author. If this session wrote the plan, run the review in a fresh subagent given only the plan + goal; if no subagent, say so and label the verdict self-review.

## Steps
1. **Freeze scope**: restate the goal in one line; list every enumerated item the plan refers to ("14 screens", "7 rules"). Any list referenced but not stated = Critical finding.
2. **Inventory before critique**: check what already exists (repo, database, prior work, memory). Flag plan steps that rebuild something that exists.
3. **Attack surfaces**: check each, one line per hit:
   - Internal contradictions (step A vs step B; goal vs constraint)
   - Feasibility (platform/API limits, data availability, rate limits) — verify with a search or read, not memory
   - Ordering (decisions made before the evidence they need)
   - Gates (single end gate; self-graded review)
   - Testability (vague targets, untestable acceptance criteria)
   - Conflicts with the standing rules in rules/standing-rules.md (exit conditions, caps, position limits, auto-merge exceptions)
   - Failure / rollback (what happens when step N fails; reversibility)
   - Missing owners, data contracts, privacy, licensing, cost
   - Numbers: any threshold, sample size or trigger in the plan is computed, not eyeballed (power / n needed, how often a trigger fires at the base rate, whether units are independent or grouped)
4. **Assumptions**: invoke assumption-breaker on the plan; keep its ledger and the pivotal test result. If an earlier step already produced a ledger for this plan version this session, reuse it instead of rerunning. Fallback if not installed: list the plan's "this works because" claims, rank by work wasted if false, run the smallest read-only check on the top one.
5. **Rank**: Critical (plan fails or harms) / High (major rework) / Medium (gap, fixable later) / Low (polish). Table: # | Severity | Finding | Evidence | Fix.
6. **Root cause**: if 3+ findings share a cause, say so and propose a restructure (e.g. added gates) instead of patching.
7. **Verdict** via evidence-gate (fallback: criterion / evidence / pass-fail-unknown table): Approve | Approve with fixes | Revise | Reject. List residual risks that remain after fixes. Flag any fix that is time-sensitive (e.g. data that can't be backfilled later).

## Output
TL;DR verdict (1 line) → findings table → assumption ledger → residual risks → diagram if a resequence is proposed.

## Stop rules
- No evidence = Unknown, never Pass.
- No filler findings to pad the table; "no Critical issues" is a valid result.
- Do not rewrite the plan unless {{APPROVER}} asks; offer it as a next step.
