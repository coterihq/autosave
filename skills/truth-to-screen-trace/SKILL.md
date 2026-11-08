---
name: truth-to-screen-trace
description: Use when a dashboard or screen looks plausible but you must decide whether its numbers deserve trust; produces a provenance map from UI value to upstream source.
---

# Truth-to-Screen Trace

**Use when:** a displayed output (number, status, chart, recommendation) is about to be relied on or acted on. **Not for:** data:validate-data (QA of an analysis) or review (financial-correctness lens on a diff); this traces one shipped output end to end and rules on trust.

## Contract
- Inputs: the screen or component, the specific outputs in question, read access to code and stored data.
- Artifact: provenance map, discrepancy table, required confidence indicators.
- Exit gate: each consequential output has a traceable basis or visibly says why it cannot be trusted. Verdict: Verified | Failed | Blocked | Inconclusive, with evidence per criterion. Format the verdict with evidence-gate.
- Authority: read-only through the proposal. Steps that edit, migrate, deploy or write externally start only after {{APPROVER}} records a go; findings alone never authorize them.
- Rule: presentation quality and data correctness are separate verdicts. Report both.

## Fast path
One output, one chain: name the claim, trace UI -> selector -> calculation -> API -> stored record -> upstream source, check units and freshness at each hop, give the verdict. Skip the reconcile and confidence steps if nothing conflicts.

## Steps
1. **Claim inventory**: list each consequential output and what it asserts. Hands on: claim list, one row each.
2. **Provenance trace**: follow UI -> selector -> calculation -> API -> stored record -> upstream source. Hands on: table of claim, hop, file or table, owner.
3. **Transformation audit**: at each hop note missing-value handling, aggregation, fallbacks, truncation, row caps. Hands on: per-hop list of what can change the value silently.
4. **Freshness and units**: record timestamp, as-of, currency, per-share vs per-contract, scale. Hands on: unit and age column added to the table.
5. **Reconcile sources**: where two sources feed the same claim, compare with one concrete sample. Hands on: discrepancy table, magnitude and direction.
6. **Confidence surface**: for each untrusted or stale output state the indicator the user needs (stale badge, partial-data flag, source label). Hands on: indicator spec per claim.

## Truth-to-action (use when the display leads to a consequential action)
Trace the forward chain too: source -> transformation -> displayed interpretation -> user decision -> action payload -> execution acknowledgment -> resulting state.
- Question: did the action preserve the meaning of what the user saw and approved?
- Compare displayed values to the payload field by field, then the acknowledgment to the resulting stored state. Include the account name on both sides.
- Name every place the payload can differ from the display (rounding, unit, account, default).
Keep the short path above for read-only views.

## Escalate if
- A value differs by a fixed factor (e.g. ~27x, ~2x) between display and source: stop and find the unit or scale error.
- A reader returns exactly a platform cap of rows (e.g. a 1,000-row cap) or non-prod data appears in totals (e.g. sandbox data).
- The output feeds an order, proposal or write: run the Truth-to-action section.

## Skip if
- The value is decorative, or the source is the only source and already labelled as an estimate.
- The question is visual quality only: use design:design-critique.

## Stop rules
- Do not mark a hop Verified without a sample value observed at that hop.
- Cannot reach the upstream source: verdict Blocked or Inconclusive, never Verified.
- Do not fix a discrepancy during the trace; hand the table to a separate change.

## Record
Provenance map, sample values with timestamps and environment, verdict per claim, and what would invalidate it (schema change, new upstream, source swap).
