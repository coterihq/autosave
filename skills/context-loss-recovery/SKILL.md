---
name: context-loss-recovery
description: Use before trusting an old plan, audit or verification after compaction, drift or a changed build; produces an invalidation list and a cold-start check, and has /handoff write the packet.
---

# Context Loss Recovery

**Use when:** an old plan, audit or verification may no longer hold after drift, compaction or a changed build, or a handoff is due. **Not for:** /handoff (writes the block), session-handoff (consumes it). This adds re-observation, artifact invalidation and a cold-start check.

## Contract
- Inputs: current repo and environment (re-observed), the conversation, existing plans, audits and verifications.
- Artifact: invalidation list plus a handoff packet (exact files, decisions, blockers, next actions), written via /handoff to ~/.claude/handoffs/, not a new location.
- Exit gate: a fresh agent can name the next valid action without reconstructing the conversation. Verdict: Verified | Failed | Blocked | Inconclusive, with evidence per criterion. Format the verdict with evidence-gate.
- Authority: read-only through the proposal. Steps that edit, migrate, deploy or write externally start only after {{APPROVER}} records a go; findings alone never authorize them.

## Fast path
Short session, no stale artifacts: re-observe branch and status, write observed / decided / changed / uncertain / next, run the cold-start check, stop.

## Steps
1. **Ground-truth refresh**: re-observe git branch, status, running processes and prod SHA; do not trust the conversation. Hands on: observed-state block with timestamps.
2. **Decision ledger**: five lists: observed, decided, changed, uncertain, what the next agent is authorized to do. Hands on: ledger.
3. **Assumption diff**: list assumptions made earlier and mark each held, broken or unchecked. Hands on: diff table.
4. **Unresolved frontier**: open questions, blockers, half-done work. Hands on: frontier list.
5. **Artifact invalidation**: inventory every artifact (plan, audit, verification, snapshot, injected state); list its inputs; compare to current inputs; mark each fresh, stale or unknown; revalidate or discard. e.g. a plan built on an older schema, a UX audit of a replaced layout, a verification from a different build, a stale GO record that must grant nothing after 24h. Hands on: invalidation list (artifact -> input changed -> verdict).
6. **Context pack**: write the packet with exact paths, SHAs, commands and the next actions, prices and counts dated. Hands on: handoff packet.
7. **Cold-start check**: a fresh agent reads only the packet and names the next valid action; if it cannot, the packet fails. Hands on: cold-start result.

## Escalate if
- Re-observed state contradicts the ledger.
- Uncommitted work belongs to another session.
- A decision in the ledger lacks evidence.

## Skip if
- The session is under a few turns and nothing was changed.
- A current handoff already exists and nothing moved since.

## Stop rules
- Never carry forward a stale artifact as current; mark it stale or revalidate.
- Missing evidence for a claim: write unknown, not a guess.

## Record
Packet location, invalidation list with reasons, cold-start verdict, and what would make the packet stale.
