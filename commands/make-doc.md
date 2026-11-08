---
description: Create a document (Word, PDF, shareable page, README); routes to the right skill and asks only what is missing
argument-hint: <what the document is, who reads it>
---

The user wants to create a DOCUMENT: $ARGUMENTS

1. Restate in one line: the document, the reader and the format you will produce. Do not start before that line.
2. Pick the route:
   - Word (.docx): the `anthropic-skills:docx` skill.
   - PDF: the `anthropic-skills:pdf` skill.
   - A document for other people to read in this app, a report, a write-up: a private Artifact (start from the Artifact quickstart with intent "document"; do not hand-write markdown to get around the design pass).
   - README, runbook, API or architecture documentation: `engineering:documentation`.
   - Notes for the user's own use: a plain markdown file.
3. Ask at most 3 questions, only what is missing: the reader and what they must do after reading, length or depth, format. Give a recommended default for each.
4. Write for the reader's decision first, detail second. No filler paragraphs.
5. Verify: open or convert the output and LOOK at page 1 and one interior page (headings, tables, page breaks, fonts). For .docx/.pdf render a page to an image.
6. Save under {{OUTPUT_DIR}}/docs/YYYY-MM-DD-<slug>.<ext> and report the path. Do not publish, email or share unless asked.
