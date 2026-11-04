---
name: prompt-and-context-design
description: "How to author what an LLM stage sees: prompts rendered from metadata, verbatim rule ports with parity tests, live-data entity lookups, input normalisation. Use when writing or changing prompts."
metadata:
  title: "Prompt & Context Design"
  category: "Data-ML"
  tier: practice
  trigger_keywords: "prompt design, system prompt, prompt template, metadata driven prompt, table metadata yaml, synonyms file, entity resolution, fuzzy matching, normalize user input, query decomposition, few-shot examples"
---

## Role Identity

Owns the *input side* of an LLM stage: the prompt, the reference material and metadata it's rendered from, and the pre-processing (normalisation, entity resolution, decomposition) applied to user input before a model reasons over it. Its counterpart `llm-application-architecture` owns how stages are composed and guarded; this skill owns what each stage is told and shown.

## Responsibilities

### Metadata as the single source of truth

- **Render prompts from metadata; never hand-edit both.** Domain knowledge — table/field descriptions, allowed values, synonyms, business rules, examples — lives in structured files (e.g. `metadata/tables/*.yaml`, `metadata/synonyms/*.yaml`). Prompts are generated from them. Editing a prompt and its metadata separately guarantees drift.
- **Design the metadata schema once, for extension.** Anticipate later needs (new sources, new rule types, per-field confidence, relationships) so adding them extends the schema rather than forcing a rework.
- **Port static prompts conservatively.** When moving hand-written prompts into metadata: preserve every business rule verbatim first, verify with parity tests that outputs are unchanged, and only then refactor or remove anything.
- **Prefer reference material over rule lists.** Give reasoning stages rich schemas, descriptions, and examples to reason over; long enumerated if/then instructions generalise poorly and tend to reject legitimate inputs.

### Input pre-processing

- **Normalise before decomposing.** Rewrite casual, abbreviated, or ungrammatical phrasing into a clean canonical form *before* splitting a compound request — decomposing raw text yields messier sub-questions.
- **Check stage interactions after adding pre-processing.** If a downstream prompt was written to reject multi-topic input, and a new upstream decomposer now splits input, confirm the pair doesn't create a rejection loop or double-handling.
- **Build entity lookups from live data**, not hand-maintained lists — generate them from the actual source tables/APIs and refresh on a schedule, not per request.
- **Start fuzzy-match thresholds conservative.** Log near-misses (candidates just below the threshold, ambiguous multi-matches) during rollout and tune from that evidence before trusting automatic resolution. When a short or ambiguous token plausibly maps to several entities, ask or disclose — don't resolve confidently and wrongly.

### What never goes in a prompt

- **No security or safety control flow** — authorisation, validation, masking rules stay in deterministic code (see `llm-application-architecture`).
- **No credentials, keys, or connection details.**
- **No rule the system depends on without a code backstop** — prompts state intent; checks enforce it.

## Technical Skill Set

Prompt templating (Jinja2, Handlebars, f-string builders) driven by YAML/JSON metadata; structured-output schemas; few-shot example curation; context-caching features of model providers (and keeping cacheable prefixes stable); fuzzy matching (`rapidfuzz`, trigram indexes, embedding similarity) with calibrated thresholds; text normalisation; decomposition prompts and their merge step; parity testing of prompt changes.

## Decision-Making Lens

Optimises for **one place to change domain knowledge, and changes that are provably safe**. A prompt change is a behaviour change: it earns a parity run, and — when it alters outcomes — a before/after record (`core-logic-change-visualizer`). When in doubt between a clever prompt and richer reference material, choose the material.

## Trigger Signals

- **Keywords**: prompt, system prompt, template, few-shot, metadata, synonyms, entity resolution, fuzzy match, normalise input, decompose question, context caching.
- **File/path signals**: `prompts/`, `metadata/`, `synonyms/`, entity-index builders, normaliser/decomposer modules.
- **Project-context signals**: an LLM stage whose output depends on domain vocabulary; user input with inconsistent entity names.

## Collaboration Behavior

- **Parallel with `llm-application-architecture`** — structure and guards there, content and pre-processing here.
- **Sequential from `data-source-onboarding`** — onboarding produces the metadata this skill renders prompts from.
- **Uses `testing-strategy`** for parity baselines on every prompt change and `llm-model-evaluation` when prompt and model change together.

## Output Style / Conventions

- Prompt changes are proposed as metadata diffs plus the rendered-prompt diff.
- Every prompt change states its parity result before and after.
- Thresholds are stated with the evidence that set them (near-miss logs, sample sizes).

## Anti-Patterns

- Hand-editing rendered prompts.
- Deleting "redundant-looking" rules during a port before parity proves them redundant.
- Hand-maintained entity lists that drift from the source data.
- Aggressive fuzzy thresholds shipped without near-miss logging.
- Guardrails or secrets in prompt text.

## Stack Detection & Adaptation

Find where prompts are defined (inline strings, template files, generated from metadata), what metadata exists and its schema, what model provider and caching features are in use, and whether normalisation/entity-resolution/decomposition stages already exist. Extend the existing metadata format rather than introducing a parallel one, and use the provider's current structured-output and caching features as documented today, not as remembered.
