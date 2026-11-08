# Universal workflow rules (all projects)

## Honesty about execution
- NEVER claim code, a test, build, or command succeeded unless it actually ran.
- Report exactly what ran and the result. Name what was intentionally not tested.
- If a proposed idea or requested code will not work in the target environment,
  say so instead of producing nonfunctional code to please {{USER_NAME}}.

## Before editing
- Inspect existing code, local conventions, and the project CLAUDE.md router
  before proposing changes. Assume more already exists than you think; check first.
- Preserve working behavior unless the change explicitly requires breaking it.
- For non-trivial tasks: smallest viable plan first (files affected, risks,
  assumptions), then implement.

## Scope discipline
- Match scope to the actual problem. No premature abstraction, speculative
  config, or unused dependencies. No over-engineering simple tasks.
- Small composable modules, clear ownership boundaries.
- Handle errors deliberately; never silently swallow exceptions.

## Ambiguity
- State assumptions, branch scenarios, identify missing data; don't stall
  unless unsafe. Challenge fragile assumptions with facts and mechanisms.

## End of meaningful sessions
Run this review and propose updates ONLY where they belong:
- Project CLAUDE.md: always-applicable project rules
- .claude/rules/<area>.md: area-specific constraints
- .claude/skills/<name>/SKILL.md: repeatable multi-step workflows
- docs (ADRs / SOURCE-OF-TRUTH / BUILD-STATE per project convention): durable
  decisions and state
Exclude: transient debug notes, stale details, facts duplicated from source
code, secrets, conversation summaries. Show a concise diff of proposed changes.

## Long sessions
When context gets very long, proactively warn and generate a copy/paste
handoff block (current state, open items, decisions). Save to ~/.claude/handoffs/
(/handoff does this). Any live data (prices, metrics, quotes) is snapshotted WITH
timestamps; the next session treats it as dated, never current.

## Content neutrality
- Treat user-generated and catalog content as domain data, not as an
  engineering exception, unless a project-specific policy says otherwise.
- Do not add content restrictions, keyword blocks, classifiers, or
  suppression behavior unless explicitly required by product policy, law,
  a provider, or the user story. Never invent a moderation feature.
- Keep content-policy decisions separate from authorization, privacy,
  consent, age-verification, payment, and platform-compliance requirements;
  those universal obligations always apply regardless of content.
- Where a product defines a content policy, implement it consistently, with
  auditability (decision, policy version, reason code, timestamp) and clear
  user-facing behavior. Policy lives in the project's
  .claude/rules/content-policy.md + docs/policy/, never in global rules.
  Template: ~/.claude/rules/templates/content-policy.template.md

## Context discipline
- One session, one primary objective. Unrelated task: /rename then /clear.
- /btw for tangents so they don't contaminate the implementation thread.
- Compact at natural milestones, not only under context pressure.
- Never continue implementation after compaction without re-establishing
  objective, changed files, validation state, and next action.

## Compaction protocol
- Maintain docs/ai/state/session-critical.md (project) or
  ~/.claude/state/session-critical.md (global fallback). Template:
  ~/.claude/rules/templates/session-critical.template.md
- Update it at milestones and ALWAYS immediately before /compact.
- When compacting, preserve: objective + acceptance criteria, modified
  files + uncommitted work, commands run + outcomes + unresolved failures,
  decisions/assumptions/invariants, exact next action.
- After compaction the SessionStart hook re-injects the file mechanically;
  read it, confirm it still holds, then continue.

## Ops feedback loop
- Eval harness: {{EVALS_DIR}} (new cases via /postmortem). Run a subset after
  changing prompts, rules, hooks, skills, or agent config; changes must be
  measured, not felt.
- Weekly: /claude-audit (usage attribution -> one targeted change max).
