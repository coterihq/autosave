---
description: Factual inventory of open/stale projects with last-touched dates
---
List every project directory under {{PROJECTS_DIR}} (one level deep) with its
last-touched date: `git log -1 --format=%cs` where it is a repo, else the mtime
of its most recent file. Format as a table:
name | last touched | state (active <14d / dormant / blocked) | next action if one
is already written down (TODO, BUILD-STATE, handoff in ~/.claude/handoffs/).
Facts only: no nudging, no prioritization unless asked. Never raise dormant
projects outside this command.
