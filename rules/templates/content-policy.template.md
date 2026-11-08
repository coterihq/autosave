---
paths:
  - "src/content/**"
  - "src/moderation/**"
  - "app/api/content/**"
  - "app/api/media/**"
---
# Content policy integration
# TEMPLATE — copy into <project>/.claude/rules/content-policy.md ONLY for
# projects with an explicit product content policy. Adjust paths to the repo.

## Source of truth
- Product policy is defined in docs/policy/content-policy.md.
- Do not infer restrictions from content category alone.
- Implement only the classifications, actions, and review flows explicitly
  defined by the product policy.

## Architecture
- Keep classification separate from storage, discovery, entitlement, and
  rendering — distinct classification / decision / action / audit layers.
- Store: policy decision, policy version, reason code, confidence, timestamp.
- Support configured actions: allow, label, age-gate, restrict by
  jurisdiction, queue for review, redact, or block.
- Decisions must be auditable and reversible when policy or classifier
  behavior changes.

## User controls
- Apply consent, age, region, account settings, and entitlement rules before
  presentation where the product requires them.
- Never expose private, unconsented, or unauthorized content.
