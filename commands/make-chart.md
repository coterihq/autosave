---
description: Create a chart or plot of a specific kind from REAL data only; sets kind-appropriate defaults and verifies against the source
argument-hint: "<kind> <what to show>   (kinds: bar line scatter histogram box heatmap area waterfall candlestick equity funnel sankey treemap)"
---

The user wants to create a CHART: $ARGUMENTS

1. NO DATA, NO CHART. Identify the real data source first: a file path, a query result, or numbers the user pasted. If there is none, ask for it and stop. Never generate a chart as an image (image models invent numbers) and never make up values.
2. Restate in one line: the kind, the question the chart answers, the data source and the route. Do not start before that line.
3. Pick the route:
   - Interactive or shareable page: the `dataviz` skill (HTML/Artifact).
   - Publication-quality static image: `data:create-viz` (matplotlib/seaborn/plotly).
   - Several linked charts with filters: `data:build-dashboard`.
   - A quick inline chart in chat: the visualize widget (`mcp__visualize__read_me`, module "chart").
4. Kind defaults (apply unless the user says otherwise):
   - bar / column: compare categories; sort descending; zero baseline.
   - line: trend over time; direct labels; mark events sparingly.
   - scatter: relationship; label outliers; optional fit line with its n.
   - histogram / box: distribution; state bin width or quartile rule.
   - heatmap: matrix or correlation; diverging scale centred on 0.
   - area / stacked: composition over time; order series by size.
   - waterfall: bridge from start to end value (P&L).
   - candlestick: OHLC with volume panel; state the interval and the data timestamp.
   - equity: equity curve plus drawdown panel, shared x axis.
   - funnel: stage-to-stage conversion with counts.
   - sankey: flows between stages; cap at about 8 nodes.
   - treemap: part-of-whole with many parts; pie only for 5 parts or fewer.
5. Ask at most 3 questions, only what is missing: the data source, the question it must answer, the audience or size.
6. Label axes with units, keep honest scales (say so if an axis is truncated or log), put the data's as-of date on any market data.
7. Verify before reporting: render and LOOK, then check 2 to 3 plotted values against the source numbers. If the chart aggregates several sources or accounts, name them.
8. Save under {{OUTPUT_DIR}}/charts/YYYY-MM-DD-<slug>.<ext> and report the path and the data source used.
