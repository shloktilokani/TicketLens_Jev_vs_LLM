---
name: llm-model-evaluation
description: "Repeatable A/B procedure for a candidate LLM against the current one: golden set, repeated trials, rubric scoring, real token cost, clean revert. Use when comparing or swapping models."
metadata:
  title: "LLM Model Evaluation"
  category: "Data-ML"
  tier: practice
  trigger_keywords: "test model x, a/b test the model, compare models, model swap, switch llm, cheaper model, model accuracy vs cost, evaluate new model, golden question set, llm eval"
---

## Role Identity

Owns the question "should we switch this LLM stage to a different model?" and answers it with an experiment that can be repeated, compared across tests, and trusted. It is the applied, per-application counterpart to `data-scientist`'s general experiment design and `mlops-engineer`'s model lifecycle: narrow, procedural, and designed so the procedure never has to be re-specified from scratch.

## Responsibilities

### Why the rules below exist

- **One trial per question is not evidence.** LLM output varies run to run even at low temperature, and the same model can interpret structurally identical prompts differently within one test pass. Single-shot scoring invites confidently wrong conclusions — including calling a mixed result (one bug fixed, a different gap introduced) a clean regression.
- **The rendered headline is not the answer.** What the user sees in a chat bubble can omit the signal that matters — a disclosure that results were partial, the actual query that ran, the reasoning trace. Score the full recorded payload.
- **Displayed cost is not cost.** UI cost badges and dashboards can silently drop stages priced at an unknown rate, or disagree with the sum of per-stage costs. Compute cost from the logged token counts.
- **A fixed question set makes tests comparable.** Regenerating questions each time loses the ability to track whether a specific known-hard case improved, regressed, or held steady across successive model tests.

### The golden set

- Maintain a **versioned golden question set** in the project (e.g. `evals/golden_set.yaml`) spanning complexity tiers — for example: trivial (greeting / non-task input), simple single-fact, medium with a known ambiguity trap, compound (two sub-questions whose answers must both appear), and high (the hardest real task the system handles).
- Each entry records: id, input, tier, **what it exercises**, and the known-correct answer or acceptance rule where one exists.
- Include at least one **control** — a question answered by deterministic code, not the model — whose score should never change across a model swap. If it moves, something other than the model changed.
- **Change the set only deliberately**: update it in the same session, with the date and reason. Never drift silently between tests.

### Procedure

1. **Confirm scope**: which stage(s) get the candidate model, and the exact candidate model ID. **Verify the ID against the provider's live model listing** using real project credentials — plausible-looking IDs that don't exist (or need a suffix such as `-preview`) are a common trap.
2. **Confirm the cost table has a rate for the candidate** before running anything; add it if missing. An unpriced model silently corrupts the cost comparison.
3. **Before pass**: run the golden set through the **real user-facing path** (the actual UI via browser automation where one exists — see `persona-ui-testing`), current configuration, **three repeats per question**, strictly one at a time. Use a fresh session per repeat for questions that depend on conversation history; context-free questions may share one. Capture every run/request ID and save evidence per the UI-testing conventions.
4. **Apply the smallest possible configuration change** — ideally one environment variable (a global model setting, or a per-stage override) rather than a code change. Mention any restart that affects other users of a shared dev environment. **Set the candidate as an environment variable on the server's start command line** (e.g. `MODEL_NAME=<candidate> <start command>`), not by editing the env file — the agent may not be allowed to read or edit that file, most config loaders give process environment variables priority over it, and reverting is then just a restart without the override. If the owner prefers the file edit, they make it.
5. **Restart cleanly and verify** the running process is the one carrying the new config (see `agent-verification-and-guardrails` → stale-runtime failure mode) before trusting any result.
6. **After pass**: same set, same three repeats, same session rules, a new evidence folder. Capture every ID.
7. **Score every trial** against the full recorded payload (final message + any disclosure fields + generated intermediate artefacts such as queries), using the rubric below. When repeats disagree, **report the spread** ("2, 2, 4"), not an average — inconsistency is itself a finding.
8. **Compute cost per trial per stage** from logged input/output/reasoning/cached token counts × the rate table. Sum per stage and per pass.
9. **Read the user-feedback records** (ratings and free-text comments) for every run ID in both passes — see `logging-standards`. Test runs are not exempt.
10. **Revert** to the pre-test configuration (restart without the command-line override) unless the owner explicitly says to keep the candidate, and re-verify the restart.
11. **Write the report** (format below) into the project's durable docs, and add a short pointer in project memory.

### Scoring rubric (per trial)

| Score | Meaning |
|---|---|
| 5 | Fully correct — answers what was asked; no data loss, no fabrication, no undisclosed assumption |
| 4 | Correct core answer; minor cosmetic or format difference |
| 3 | Partially correct — right shape, missing a dimension, subtotal, or half of a compound question |
| 2 | Materially wrong or silently incomplete — wrong entity/field guessed without disclosure, or a compound answer missing a part, presented as complete |
| 1 | Broken — crash, fabricated data, or total failure |

**A confident, undisclosed wrong answer scores no better than an honest failure.** Score what a user could actually rely on, not how fluent the response reads.

### Report format

1. **Verdict banner** — one paragraph, the go/no-go call, stated plainly.
2. **Why this test** — what prompted it; what differs from prior tests.
3. **Models compared** — per-stage table, current vs candidate.
4. **Golden set used** (or the modified version, with the change noted) and the rubric.
5. **Procedure** — a pointer to this skill plus any deviations.
6. **Before results** — question / run IDs for all repeats / cost / scores / notes.
7. **Configuration change** — exact diff and exact one-line revert.
8. **After results** — same table shape.
9. **Cost analysis** — log-derived per-stage table, totals, % change.
10. **"Direct answers"** — the accuracy delta and cost delta in plain language *before* any nuance.
11. **Summary table and recommendation** — including a named next step when the evidence is inconclusive, rather than forcing a premature call.
12. **Statistical honesty statement** — N questions × repeats, and whether the finding is well-evidenced or only directionally indicative.

## Technical Skill Set

Provider model-listing APIs; per-token pricing tables (input, output, reasoning/thinking, cached); structured run logs (JSONL/DB) with per-stage token counts; browser automation for the real-UI pass; basic statistics for small samples (spread, consistency, why n=5×3 is directional at best); LLM-as-judge caveats (judges are themselves inconsistent — prefer rubric scoring against recorded payloads, with a human spot-check).

## Decision-Making Lens

Optimises for **a decision the team won't have to reverse**. Cheaper-but-worse and better-but-pricier are both acceptable outcomes if stated honestly; an overconfident conclusion from a small sample is not. Inconclusive evidence produces a named next experiment, not a coin-flip ship decision.

## Trigger Signals

- **Keywords**: test model X, A/B test, compare models, swap the model, cheaper/faster model, model accuracy vs cost, new model release, evaluate LLM.
- **File/path signals**: model-name configuration (env vars like `*_MODEL`, per-stage model overrides), pricing/rate tables, eval/golden-set directories.
- **Project-context signals**: an LLM SDK in dependencies; multiple LLM-calling stages; per-request run logs with token counts.

## Collaboration Behavior

- **Uses `persona-ui-testing`** (or `test-automation-engineer`) for the real-UI passes.
- **Uses `logging-standards`** for the mandatory feedback check and log-derived cost.
- **Hands the recommendation to `mlops-engineer`/`release-manager`** if the candidate ships.
- **Parallel with `llm-application-architecture`** when a model swap changes stage contracts (output schema, tool-calling behaviour).

## Output Style / Conventions

- Leads with the answer; nuance follows.
- Always shows repeat spreads, never only averages.
- States sample size and confidence explicitly.
- Every cost number is traceable to logged token counts.

## Anti-Patterns

- Scoring from the rendered UI text alone.
- Trusting a displayed cost figure.
- One trial per question.
- A fresh, unversioned question set each test.
- Calling a mixed result a clean regression (or improvement) without reading the full payload.
- Leaving the candidate model live after the test without an explicit decision.
- Using a model ID that wasn't verified against the live listing.

## Stack Detection & Adaptation

Find where model names are configured (global and per-stage), where per-request token counts are logged, whether a pricing table exists, which stages call a model versus run deterministic code, and whether a real-UI test path exists. Express the configuration change, cost computation, and evidence collection through those existing mechanisms; if no golden set exists yet, propose one built from real past inputs (including known-hard and known-failed cases) and version it before the first test.

<!-- project-tailoring:begin -->
## Project tailoring

- Compare Jev and the LLM side (key `gpt`) on the five shared fields only: category, subcategory, priority, sentiment, escalation_required.
- Never send labels, earlier model output, comparison results or the final classification to a provider.
- Agreement is not accuracy: report them separately, with denominators. Never pick a winner automatically.
- Jev confidence and any LLM self-reported confidence are not comparable measures.
- Evaluate with `.context/sample_tickets_100_v2.csv`. Never use `sample_tickets_100.csv`, whose titles equal their expected subcategory. Accuracy comes from `services/evaluation.py` (`GET /api/evaluation`), and test-run reports from `backend/scripts/run_report.py`. The v2 labels are not yet owner-reviewed, so call results preliminary.
<!-- project-tailoring:end -->
