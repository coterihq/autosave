---
description: "Create an image: routes to AI generation, a designed layout, or SVG; asks only what is missing"
argument-hint: <what the image is for / what it shows>
---

The user wants to create an IMAGE: $ARGUMENTS

1. Restate in one line: what you will make and which route you will use (below). Do not start before that line.
2. Pick the route. Use only what is actually available in this session; say which routes you checked.
   - A picture, illustration or photo-like scene: a local image model if one is installed (for example mflux / FLUX on Apple Silicon, or a local Stable Diffusion CLI), otherwise an image-generation MCP tool if one is connected. A hosted model costs money: state the model and image count BEFORE running. Image models do not render text reliably.
   - A designed layout with real text (poster, banner, social card, slide cover): a canvas/design skill if one is installed; otherwise build it as HTML or SVG and render it to PNG. Do not use an image model for text-heavy images.
   - A logo, icon or simple graphic: write SVG by hand and render it to PNG to check it. This route always works.
   - Editing an existing design in a design tool (Canva, Figma): only through that tool's connector, and only if it is connected and authorized; if not, say so once and offer the other routes.
3. Ask at most 3 questions, only for what $ARGUMENTS does not already say: where it will be used, aspect ratio, style or mood. Give a recommended default for each.
4. Never use image generation for a chart or any picture of real data: it invents numbers. Route that to /make-chart.
5. Verify before reporting: open the image file and LOOK at it (composition, legibility of any text, anything odd like extra fingers or garbled letters). Iterate once if it is off.
6. Save under {{OUTPUT_DIR}} and report the path. Do not publish or send it anywhere.
