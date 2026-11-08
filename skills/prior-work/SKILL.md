---
name: prior-work
description: Use before planning or building anything to find existing plans, specs, handoffs, decisions, rejected approaches and open items on the topic, so nothing is rebuilt or missed. Triggers on "prior work", "did we already", "check history", and before writing any plan.
---

# prior-work

Read-only recall. Never edits, writes or commits.

## Sources (search all that exist)

1. Session memory search, if a memory plugin is installed (e.g. `claude-mem:mem-search`): 3–5 short topic queries (feature name, project/repo name, key nouns, table/endpoint names), not one long query.
2. `~/.claude/handoffs/` — filenames and contents matching the topic.
3. Repo docs: specs, plans, ADRs and status docs (e.g. `docs/`, `docs/adr/`, `docs/superpowers/`), plus `git log --oneline --grep=<topic>`.
4. Fallback when no memory plugin is available: past-chat search (`conversation_search`, `recent_chats`) plus memory files.

## Output (max ~20 lines)

1. **Searched:** sources used; whether mem-search worked.
2. **Prior work:** one line per item — date · source (mem #, file path, commit, chat) · what it is.
   Mark each: decision / suggestion / rejected / open / shipped.
3. **Stale or conflicting:** any handoff, spec or plan that disagrees with newer evidence (name both sides).
4. **Verdict:** no prior work · prior plan exists → recommend resume / extend / supersede (one-clause reason).

## Rules

- Past assistant suggestions are suggestions, not {{APPROVER}}'s decisions, unless a turn from {{APPROVER}} or commit confirms them.
- Cite every item; no uncited claims.
- Empty result: say so in one line and stop.
- Hand the list to the calling workflow as context; it must not re-ask what's already decided.
