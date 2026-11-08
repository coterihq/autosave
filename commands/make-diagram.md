---
description: Create a diagram (flowchart, sequence, ER, architecture, timeline); shows the real mechanism, asks only what is missing
argument-hint: <what it must show, and for whom>
---

The user wants to create a DIAGRAM: $ARGUMENTS

1. Restate in one line: what the diagram explains, the diagram type and the route. Do not start before that line.
2. Pick the route:
   - Flowchart, sequence, state, ER, gantt, mindmap: Mermaid (renders natively in an Artifact; or a .mmd file if the user wants a file). Use the `artifact-diagramming` skill for drawing guidance.
   - System or architecture with real layout: hand-built SVG (same skill), checked in light and dark.
   - A quick inline sketch in chat: the visualize widget (`mcp__visualize__read_me` first, module "diagram").
   - A polished presentation graphic: the `anthropic-skills:canvas-design` skill.
3. Ask at most 3 questions, only what is missing: the nodes and relationships it must show, the audience, left-to-right or top-down. Give recommended defaults.
4. Draw the real mechanism, not labelled boxes: every arrow says what flows, one diagram answers one question, split anything over about 12 nodes.
5. Verify: render it and LOOK (overlaps, clipped labels, crossing arrows, readable at the size it will be seen).
6. Save under {{OUTPUT_DIR}}/diagrams/YYYY-MM-DD-<slug>.<ext> and report the path. Do not publish unless asked.
