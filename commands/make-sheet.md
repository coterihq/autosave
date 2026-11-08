---
description: Create a spreadsheet (.xlsx) with real formulas; asks only what is missing
argument-hint: <what the sheet tracks or computes>
---

The user wants to create a SPREADSHEET: $ARGUMENTS

1. Restate in one line: the columns and the computation the sheet performs. Do not start before that line.
2. Route: the `anthropic-skills:xlsx` skill.
3. Ask at most 3 questions, only what is missing: the source data (file, paste, or query), which values are inputs vs formulas, who edits it. Give recommended defaults.
4. Build with live formulas, not pasted results; inputs in one clearly labelled area; no hard-coded constants inside formulas.
5. Verify: recalculate, check there are no formula errors, and spot-check 2 to 3 results by hand against the source.
6. If the sheet combines several sources or accounts, name the source on each block and put the as-of date on any live data (it is DATED, never live).
7. Save under {{OUTPUT_DIR}}/sheets/YYYY-MM-DD-<slug>.xlsx and report the path.
