---
description: Pre-change risk check before touching prod-adjacent systems
---
Before executing the requested change:
1. Blast radius: what reads/writes this? Grep callers; check scheduled jobs
   (cron, CI, queues), database tables and API consumers.
2. Invariants in play: list the project's non-negotiables (examples: GRANT after
   CREATE on DB migrations, dry-run flags stay on, append-only ledgers, RLS +
   GRANT both present). Read the project CLAUDE.md for its own list.
3. Rollback: exact command/file state to restore. If none exists, say so
   and get an explicit go from {{APPROVER}}.
4. Then execute. Report as: risk -> mitigation -> done.
Skip ceremony for read-only or scratch work.
