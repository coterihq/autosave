---
description: Create a slide deck (.pptx, deck from a document, or a shareable deck); asks only what is missing
argument-hint: <topic, audience, or the source document>
---

The user wants to create a SLIDE DECK: $ARGUMENTS

1. Restate in one line: topic, audience, rough slide count and which route. Do not start before that line.
2. Pick the route:
   - A PowerPoint file (.pptx): the `anthropic-skills:pptx` skill (file-based, no app needed).
   - A deck to share from this app: a private Artifact (quickstart intent "slides").
   - Only if the user asks to drive the actual PowerPoint app: the PowerPoint MCP tools.
3. Ask at most 3 questions, only what is missing: the audience and what they should decide or remember, slide count or talk time, the source material. Give recommended defaults.
4. Slide rules: each title states the takeaway, one idea per slide, at most ~6 short lines, a real chart for any number (use /make-chart), speaker notes only if asked.
5. Verify: render the slides to images and LOOK at the first, one dense slide and the last (text overflow, contrast, orphaned titles).
6. Save under {{OUTPUT_DIR}}/decks/YYYY-MM-DD-<slug>.pptx and report the path. Do not publish or send unless asked.
