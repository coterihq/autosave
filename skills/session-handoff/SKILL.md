---
name: session-handoff
description: Write or consume a session handoff block. Use when a conversation is getting long, when switching surfaces (claude.ai <-> Claude Code <-> Cowork), when the user says "handoff", or at any natural milestone before /clear or /compact.
---

# Session Handoff

## Writing (triggers: long conversation, milestone, surface switch, "handoff")
Produce a copy/paste block AND save it to ~/.claude/handoffs/YYYY-MM-DD-<slug>.md:

    # HANDOFF: <task> | <date> | from: <surface>
    ## Objective + acceptance criteria
    ## Current state (done / verified how)
    ## Files changed (paths, committed or not)
    ## Data snapshots (any prices/metrics WITH timestamps - treat as dated)
    ## Decisions made + assumptions
    ## Open items (exact next action first)
    ## Invariants in play (DB grants, dry-run flags, do-not-touch guards)

Rules: any live data (prices, metrics, quotes) must carry timestamps; the next session treats it as stale.
Never include secrets/keys. One handoff per objective, append-only per day.

## Consuming
On session start with a handoff present: read it, verify claims against the
filesystem before acting on "already built", state the next action, proceed.
Do not re-litigate closed decisions unless evidence contradicts them.
