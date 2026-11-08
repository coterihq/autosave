---
name: status
description: Factual status of the current project — where are we, what's open, what's stale. Works in any repo; uses project status docs when present, git otherwise.
---

Answer "where are we" for the project in the current working directory. Facts only, no motivation, no nudging.

1. Find the status sources (use what exists, skip what doesn't, never invent):
   - Project CLAUDE.md router → follow its "read first" pointers for status/backlog docs.
   - Else look for: docs/SOURCE-OF-TRUTH.md, docs/ROADMAP.md, docs/BUILD-STATE.md, docs/MASTER-BUILD-TODO.md, STATUS.md, TODO.md, ROADMAP.md, README "Status" section.
   - Also read the project's memory index (MEMORY.md) and any open work-state list if available.
2. Run: `git status --short`; `git log --oneline -5`; `git worktree list`; `git branch --show-current`.
   For each worktree/branch, last commit date: `git -C <path> log -1 --format=%cs`.
3. Report:
   - Active objective + current in-progress work
   - Top 3 next actions from the backlog (name the doc each came from; if no backlog doc exists, say so)
   - Uncommitted changes (files, one-line what they are)
   - Dormant/stale areas: list factually WITH last-touched dates only. Never editorialize about staleness.
4. Doc-sync check: if a status doc carries a "Last updated" date older than the latest commit touching source (`src/`, `app/`, `lib/`, or the repo's main code dir), flag the gap once, factually.
5. Mark anything taken from memory or a doc dated more than a day old as unverified; don't assert live state (prices, positions, prod state) from it.
