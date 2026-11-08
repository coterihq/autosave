---
description: Generate a session handoff block and save it to ~/.claude/handoffs/
---

Generate a handoff block for continuing this session in a fresh thread.

1. Summarize: current objective, work completed this session, decisions made
   (with rationale one-liners), open items, exact next action.
2. If any live data was used (prices, metrics, quotes, API results): snapshot it
   WITH timestamps and label it DATED; the next session must re-fetch, never
   treat it as live.
3. State what was validated (commands run + results) and what was not.
4. Write the block to ~/.claude/handoffs/YYYY-MM-DD-<topic>.md
   (use today's date and a short kebab-case topic).
5. Also print the full block in chat as copy-paste.

Keep it dense: only what the next session needs to continue correctly.
No conversation recap, no transient debugging notes, never secrets or keys.
