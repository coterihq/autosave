---
name: incident-to-eval
description: Convert a real mistake, near-miss, or recurring failure into a regression eval case. Use when the user says "postmortem", "add this to evals", "make sure this never happens again", or after any incident worth preventing.
---

# Incident -> Eval

Evals live in {{EVALS_DIR}}/<slug>/. Every case gets:

EXPECTED.md:
    # <slug>
    ## Incident (1-3 lines, dated, what actually happened)
    ## Must detect:
    ## Must not do:
    ## Required evidence:
    ## Pass condition (mechanically checkable if possible):

If mechanically checkable: add test_<slug>.py (pytest) next to it.
If judgment-based: add PROMPT.md (the canonical task prompt to re-run
against a fresh session) and grade manually against EXPECTED.md.

Then: run `make evals` (or your test runner) in {{EVALS_DIR}} so failures are
recorded and reviewed. One incident = one case. Do not
invent hypothetical cases - evals are incident history, not imagination.
