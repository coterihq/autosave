---
description: Convert an incident into a regression eval (incident-to-eval skill)
---
Use the incident-to-eval skill on the incident just discussed:
1. Write {{EVALS_DIR}}/<slug>/EXPECTED.md (incident, must detect, must not
   do, evidence, pass condition).
2. Automatable? add test_<slug>.py. Judgment-based? add PROMPT.md.
3. Run the eval suite in {{EVALS_DIR}} (e.g. `make evals` or `pytest`) and
   confirm the new case is picked up.
4. One-line summary: what class of mistake this now guards.
