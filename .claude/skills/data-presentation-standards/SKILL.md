---
name: data-presentation-standards
description: "Rules for apps that answer with data: chart vs table vs text, table formats, number formatting, summary prose, chart design, with code backstops. Use when shaping how query results are shown."
metadata:
  title: "Data Presentation Standards"
  category: "Engineering"
  tier: practice
  trigger_keywords: "chart or table, response format, visualization choice, how should this answer be displayed, summary text for query result, pivot table, dual axis, data labels, chart title, kpi answer, visualization suggester"
---

## Role Identity

Owns the layer *above* chart mechanics. Given a query result, it decides **whether** the answer should be a chart, a table, or a sentence; which kind of table; what the summary must and must not say; and which design rules the chosen format must satisfy on the surface it will actually render on. Once it has decided "this is a chart," the chart's detailed mechanics (form within the chart family, palette, marks) belong to a chart-mechanics skill such as `dataviz`.

## Responsibilities

### 1. Format selection

- **Let the audience's stated preference set the default order**, and write it down. A general reference that is *silent* on a hierarchy is not evidence against one — the actual audience's stated preference is better evidence. A common executive-audience default is **chart → table → text**: chart wherever the data reads well as one, table when readability requires it, text only when there's nothing to plot. Measure the actual format mix in production logs and compare it to the stated preference.
- **Two text cases are information rules, not preferences**: *zero rows*, and *a single value* (one bar is just a number with axes). A single value gets a comparison clause only when the result itself contains something to compare against.
- **Readability ceilings override the default**: more series than the categorical palette has distinct hues (commonly ~8), or more axis categories than fit legibly on the render surface (e.g. ~30 in a narrow chat bubble). Past a ceiling, use a table and note that a chart was considered.
- **Two-dimension cross-tabs are chartable by default** — stacked for parts of a whole, grouped for independent comparisons — falling back to a matrix table past the ceilings.
- **No dual-axis charts.** Two quantities in different units (revenue and volume, say) become two separate single-axis charts in the same response, never one chart with two y-axes.
- **Treat dense sequential axes as trends, discrete ones as categories**: months/quarters stay on time-series charts; a handful of years is a discrete comparison that may route to a matrix.

### 2. Summary prose

- Lead with the answer (bottom line up front); keep it tight — often one sentence.
- State the dimensions the answer covers (period, scope, filters) so the number can't be misread.
- **A comparison or direction clause ("up 12% year on year", "highest", "leads") only when the result contains the comparison basis.** Never fabricated.

### 3. Tables

- **Flat table**: one categorical dimension, any number of metric columns.
- **Matrix/pivot**: two categorical dimensions plus one or more metrics — not a flat table with the dimensions concatenated or truncated.
- **Never mix incompatible unit families in one table's metric columns** (currency beside tonnage implies false comparability). Split into separate tables or sections.
- **Subtotal/rollup rows are marked explicitly by the producer** (e.g. a list of row indices in the response), never guessed by the renderer from cell text — a pattern like `/total/i` will misfire on real names that contain the word.

### 4. Chart design

- **Direct data labels on every mark that carries an answer-relevant value**, when the render surface is static or hover is not the primary interaction (narrow bubbles, printed reports, screenshots). Hover tooltips are a bonus, never the only place a value appears.
- **Labels carry their unit and scale** (`$10.4M`, `44.9K (t)`), not bare scaled digits — sibling charts labelled "746" and "19" with the units only in a tooltip mislead badly. Parenthesise a physical unit after a scale suffix (`44.9K (t)`, not `44.9K t`, which reads as if the K qualified the unit). Prefer per-point label strings when a shared template would let one outlier collapse the formatting of the rest — and make any label checker accept both per-point and series-level placements.
- **Takeaway titles only when the data supports the claim** ("Plant A leads volume at 41.7K t") — same never-fabricate rule as summaries; otherwise a descriptive title.
- **Chart type follows the data relationship** — deviation, correlation, ranking, distribution, change over time, magnitude, part-to-whole, spatial, flow (the Financial Times *Visual Vocabulary* is a good cross-check).

### 5. Enforce in code, not only in prompts

When an LLM chooses the format or writes the chart config, prompt rules hold only probabilistically. Back each rule that must hold with a **deterministic check** in the formatting stage:
- *Repairable in place* (cheap, safe, no new information needed) → repair it and log that a repair happened (e.g. force direct labels on; reformat a number with too many integer digits into a scaled unit).
- *Not safely repairable* (would require inventing structure) → retry the generation once, then **fail open** with the best valid response and a log line, rather than hard-failing a correct answer over a format preference.
- *Detect-only* (the render surface can't show the fix yet) → log it for follow-up; don't pretend it's handled.
- Classify columns from the **type the producer already declares per column** (e.g. a `data_type` in the column formats), not by re-deriving it from header text.
- A final **outcome-level gate** (e.g. "no user-visible number shows more than three integer digits") catches whole families of formatting bugs with different causes. If it fires regularly, fix the upstream cause — the gate is a net, not a licence.

### 6. Number & field formatting

- **Never show raw database names** — no column/table names, snake_case identifiers, or codes in titles, headers, or prose. Derive labels from the user's question and intent, and keep a small code-level alias map as a backstop for anything that slips through.
- **Currency**: round to whole units *before* scaling, then scale — K/M/B for USD/EUR/GBP; for INR, Lakh (`L`, ≥ 1,00,000) and Crore (`Cr`, ≥ 1,00,00,000) with Indian digit grouping (`₹84,200`, `1,00,000`) below the Lakh threshold. State the scale (in the value or the header — `Revenue ($M)`), and promote at boundaries (a value that rounds to `100L` becomes `1Cr`). Each currency column scales by its own currency.
- **Counts and volumes**: whole numbers with thousands separators.
- **Percentages and ratios: exactly 1 decimal place, always** — never whole-number rounded; 94.3% vs 94.7% is a real gap that "94% vs 95%" distorts.
- **One precision and one scale per column** — never `94.3%` beside `94%`, or detail rows in K beside a total in M meant for comparison.
- **Numbers right-aligned, text left-aligned** in every table.
- **One convention for negatives** across the product (leading minus, or accounting parentheses) — keep what already ships unless the owner decides to change it.
- **Partial data** → answer with what exists, plus an explicit plain-language note of what's missing and why (not an error code). Never pad, estimate, or interpolate to make a result look complete.
- **Add a grouping/breakdown dimension at the intent or presentation layer, never forced into query generation** — a hard-coded `GROUP BY` turns single-KPI questions into breakdown tables, fragments top-N results, and changes ratio-of-sums answers (overall ≠ average of parts). Security scoping is a filter, not a grouping.

**QA checklist before a response ships**: no raw DB names · currency whole-unit, scaled, scale stated · percentages at 1 decimal · consistent precision per column · numbers right / text left · column count fits the render surface · partial data carries an explicit note · chart series/categories within the ceilings, units on labels.

## Technical Skill Set

Charting libraries' config models (Highcharts, ECharts, Vega-Lite, Chart.js, Plotly) — data-label, tooltip, and axis options; number formatting with scale suffixes and units; pivot/matrix construction from long-format rows; the FT Visual Vocabulary (github.com/Financial-Times/chart-doctor, CC BY-SA 4.0; poster at [`references/ft-visual-vocabulary-poster.png`](references/ft-visual-vocabulary-poster.png), attribution and source notes in [`references/SOURCES.md`](references/SOURCES.md)) for relationship-to-chart mapping; BLUF writing; Tufte's data-ink principle as a lens, not a mandate.

## Decision-Making Lens

Optimises for **a reader getting the right answer from what is actually rendered** — no JSON, no hover, no backend log. A response can be factually correct in its payload and still fail this lens (right number, missing unit; complete-looking chart built from nulls). Format preference yields to correctness: a correct table beats a failed chart.

## Trigger Signals

- **Keywords**: chart or table, how to display, response format, visualisation suggestion, summary sentence, pivot, dual axis, data labels, units on the chart, chart title.
- **File/path signals**: the stage/prompt that selects visualisations; the response formatter; chart-config builders; renderer code in the frontend.
- **Project-context signals**: an application that turns queries or data into user-facing answers; a charting library in frontend or backend dependencies.

## Collaboration Behavior

- **Hands chart mechanics to `dataviz`** (or the project's chart skill) once "chart" is decided.
- **Parallel with `frontend-developer`** — what the renderer actually supports (labels, notes, subtotal styling) bounds what this skill can require; gaps are logged, not assumed away.
- **Parallel with `api-contract-checker`** when a new response field is needed (e.g. subtotal indices) — additive, with a stated deploy order.
- **Checked by `persona-ui-testing`**, whose visual-review pass verifies these rules on real rendered output.

## Output Style / Conventions

- Format decisions state the rule that selected them ("table: 34 categories exceeds the 30-category ceiling").
- Each deterministic backstop logs a named event when it repairs, retries, or detects.

## Anti-Patterns

- A second y-axis.
- Units only in tooltips.
- Comparison or ranking language with nothing in the data to compare.
- Renderer-side guessing of subtotal rows from cell text.
- Rewriting an LLM-authored table into a chart in code (it would invent structure you can't verify).
- Relying on a prompt instruction alone for a rule that must always hold.
- Raw column names in user-facing labels; whole-number percentages; mixed precision in one column.
- Padding or interpolating missing periods to make a partial result look complete.

## Stack Detection & Adaptation

Identify the render surface (chat widget, dashboard, PDF, email) and its real constraints (width, height, interactivity), the charting library and version on the rendering side, the response schema between producer and renderer, and where format decisions are made (prompt, code, or both). Calibrate the ceilings to the actual surface, express labels and units in the library's own config idiom, and place backstops in the stage that finalises the response.
