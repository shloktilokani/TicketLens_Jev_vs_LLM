# AI Integration, Classification, Evaluation, and Cost Logging

## 1. Purpose

TicketLens compares TypeSafe Jev and an OpenAI GPT model on the same ShopKart ticket-classification task. The purpose is evaluation and demonstration, not model training.

## 2. Shared classification contract

Both providers are evaluated on these five structured fields:

1. `category`
2. `subcategory`
3. `priority`
4. `sentiment`
5. `escalation_required`

GPT additionally returns:
6. `summary` (English)
7. `suggested_resolution` (English)

Jev's documented System One API is for typed decisions and does not provide general free-form text generation. For Jev, summary and suggested resolution are unsupported. The UI must show this explicitly.

## 3. Taxonomy

### Categories and subcategories

Use the taxonomy in `requirements.md`. Keep canonical enum values stable and send their definitions to both providers.

### Priority definitions

- Critical: immediate risk, safety/security concern, severe service failure, or high-impact account/payment issue requiring urgent human attention.
- High: major customer impact, significant delay, failed essential transaction, or repeated unresolved issue.
- Medium: normal issue requiring support but without immediate severe impact.
- Low: informational request, minor inconvenience, or non-urgent feedback.

### Sentiment definitions

- Positive: appreciation, satisfaction, or clearly favorable tone.
- Neutral: factual/informational language without clear positive or negative emotion.
- Negative: frustration, dissatisfaction, anger, disappointment, or distress.

### Escalation definition

Escalate when the issue involves safety, suspected fraud, account compromise, legal threats, sensitive personal data exposure, repeated unresolved severe issues, or a critical/high-impact situation requiring a human specialist. The model should not escalate merely because a ticket is negative.

## 4. Language handling

- Input is English only (owner decision, 2026-11-07; Hindi and Hinglish were dropped).
- Preserve the original title and description.
- Do not translate or rewrite the original ticket before sending it.
- Both providers receive the same language instruction and original text.
- All GPT summaries and suggested resolutions must be in English.
- Classification labels must use the canonical English enum values.
- Synthetic evaluation tickets are in English.

## 5. Canonical provider input

Construct a canonical payload containing:
- title
- description
- customer name only if relevant
- order ID if present
- product name if present
- submission channel
- taxonomy and definitions
- classification field definitions
- language/output instructions

Do not include evaluation labels, previous model responses, comparison results, or final manual classification.

Both providers must receive semantically identical content and taxonomy. Provider-specific formatting is permitted.

## 6. Jev / TypeSafe adapter

Official API:
- API docs: https://api.typesafe.ai/redoc
- Models: `GET https://api.typesafe.ai/v1/models`
- Classification: `POST https://api.typesafe.ai/v1/systemone`
- Auth header: `Authorization: Bearer <TYPESAFE_API_KEY>`

System One request uses:
- `model`
- `state`
- `questions`

Use documented question types:
- `choice` for category, subcategory, priority, sentiment
- `noul` for escalation yes/no probability

Choice responses include:
- selected choice
- confidence
- probabilities for alternatives

Noul returns a probability between 0 and 1. Convert to boolean using a configurable threshold (initial default 0.5), and retain the raw probability. Make the threshold visible/configurable in settings if feasible.

The API response includes:
- actual model name
- named answers
- `usage.input_tokens`
- `usage.output_tokens`

Implementation rules:
- Discover available model names through `GET /v1/models`.
- Use `jev-latest` only if returned/accepted by the account.
- Validate every selected value against the taxonomy.
- Validate category/subcategory pair consistency.
- Store the complete redacted request and response.
- Preserve confidence and probability distributions.
- Do not request free-text summary/resolution from Jev.

## 7. GPT adapter

Use the official OpenAI Python SDK and current documented Responses API structured-output capabilities. Verify current SDK syntax from official docs during implementation.

The response schema must require:
- category
- subcategory
- priority
- sentiment
- escalation_required
- summary
- suggested_resolution

Use enums for classification fields and reject unexpected values. The prompt must tell GPT to:
- classify only from the ticket evidence
- avoid inventing order facts or company policy
- choose the closest allowed category/subcategory
- use English for summary and resolution
- mark uncertainty through a suitable field or validation warning if the schema supports it
- never claim an action has already been completed

Extract usage from the official response object where available. Store requested model and returned model metadata where available.

## 8. Fair comparison rules

- Same canonical input and taxonomy version.
- Same expected task definitions.
- No ground truth in provider prompt.
- Compare only the five shared structured fields.
- Agreement rate = matching shared fields / number of comparable shared fields.
- If one provider fails, mark comparison partial and preserve the successful result.
- Never automatically choose a winning provider.
- Operator manually selects/edits final classification.
- Agreement is not accuracy. Evaluation accuracy is measured separately against labelled sample tickets.
- Do not treat Jev confidence and GPT self-reported confidence as directly comparable calibrated probabilities.

## 9. Labelled sample dataset

Generate 100 synthetic English tickets across all six categories.

Requirements:
- Each sample ticket has expected category, subcategory, priority, sentiment, and escalation label.
- Include realistic variation in phrasing, spelling, urgency, and detail.
- Include unambiguous examples and some realistic borderline examples.
- Do not use real personal information; use `.test` email domains and fictional order IDs.
- Distribute tickets across categories; avoid severe imbalance.
- Dataset is downloadable as CSV and imported manually.
- Do not auto-seed MongoDB.
- Keep ground truth in `evaluation_labels`, separate from provider input.
- Dataset version: `shopkart-synthetic-v1`.

Evaluation:
- per-field accuracy
- overall exact-match accuracy across all five fields
- macro-F1 and confusion matrices where sample counts allow
- agreement rate between Jev and GPT
- count of both-correct, Jev-only-correct, GPT-only-correct, and both-incorrect
- report denominators and exclude failed/unsupported fields transparently

## 10. Execution logging

Create an execution record for each provider attempt, including failures.

Capture:
- execution ID, ticket ID, comparison ID
- provider, requested model, actual model
- start/end UTC timestamps and duration
- canonical input snapshot
- redacted provider request payload
- redacted raw provider response
- normalized output
- input/output/total tokens when reported
- usage source (`provider_reported`, `estimated`, or `unavailable`)
- pricing snapshot and pricing version
- estimated cost and currency
- status and safe error details
- prompt and taxonomy versions

Never log API keys or authorization headers.

## 11. Cost calculation

Use configurable rates stored in app settings and snapshot them into each execution.

Formula:

`estimated_cost = (input_tokens / 1_000_000 * input_rate_per_million) + (output_tokens / 1_000_000 * output_rate_per_million)`

- Jev pricing documentation currently states $0.042 per million input tokens and free output tokens; verify current pricing before configuring. Source: https://help.typesafe.ai/articles/5187202169-how-much-does-jev-cost
- GPT rates vary by model and can change. Do not hardcode a universal GPT rate.
- If provider usage is missing, store token counts and cost as null unless a clearly labelled estimate is implemented.
- Display estimated costs, not guaranteed invoice totals.
- Store currency and pricing version. Do not recalculate old execution records using new rates.

## 12. Errors and retries

- 400/422: invalid request; do not retry automatically.
- 401/403: credentials/permission issue; do not retry automatically.
- 402 from TypeSafe: insufficient credits; do not retry automatically.
- 429: respect provider retry guidance; bounded exponential backoff only.
- 5xx/temporary network errors: bounded retry with jitter and idempotency-aware handling.
- Timeouts: record a timed-out execution; do not silently duplicate paid calls.
- One provider's failure must not suppress the other provider's result.
- Return user-safe error messages; keep technical details in backend logs.

## 13. Privacy and data handling

Use synthetic data only. Provider calls send ticket content to external AI services. TypeSafe's current privacy FAQ says customer inputs/outputs are not used to train Jev and describes US processing; verify current terms before using real data. Reference: https://help.typesafe.ai/articles/5974925716-how-is-submitted-data-used-or-retained

The application stores full redacted request/response logs locally in MongoDB because the product owner explicitly requested detailed auditability.

## 14. As built (2026-11-11)

This document is the original intent. Where the app differs, this section wins. Architecture: `architecture.md`; decisions and history: `PROGRESS.md`.

- **Providers in use: local models only.** The Jev side is AutoTrust's open JEV model (`autotrust-jev:9b`), served by Ollama through the same System One API. It is not TypeSafe's Jev. The LLM side is an Ollama chat model (`qwen3:8b`). The internal key `gpt` means "the LLM side".
- **Paid APIs are deferred by owner decision (2026-11-11).** The hosted-Jev path (`JEV_BASE_URL=https://api.typesafe.ai` with `TYPESAFE_API_KEY`) is built but has never run with a real key. The OpenAI adapter in section 7 is not built: `LLM_BACKEND=openai` records a `not_configured` run. The architecture is kept so either can be added later.
- **Jev asks in two steps** (section 6): category, priority, sentiment and escalation first, then only that category's subcategories. AutoTrust accepts 2 to 16 options per `choice` question, so Jev can never return a mismatched pair. The escalation threshold is editable on the Settings page.
- **Model lists** come from `GET {base}/v1/models` on both sides (Settings, Refresh). A saved model name is checked against the list when the server answers.
- **Provider input** (section 5) never includes the customer's name or email, and also carries the saved prompt text and its version.
- **Prompt:** one instruction text is shared by both sides, editable and versioned on the Settings page. Each run stores the text and version it used.
- **Dataset** (section 9): the supplied 100 tickets are corrected in `.context/sample_tickets_100_v2.csv`, with the same labels, realistic titles and English text. `shopkart-synthetic-v1` is kept as the dataset version. The labels have not yet been reviewed by a person, so accuracy figures are preliminary.
- **Accuracy** (`services/evaluation.py`): each side's latest finished non-fake run per labelled ticket is scored. Failed runs are counted apart, not as wrong. Macro-F1 is shown from 30 answered tickets up. The confusion matrices leave out subcategory, because 36 by 36 is unreadable.
- **Cost** (section 11):
  - Local models are recorded at $0, as `local-no-charge`.
  - Hosted Jev's default is $0.042 per million input tokens.
  - OpenAI has no default rate.
  - Rates can be saved per side and model on the Settings page, and each run keeps its rate snapshot. Money is stored as exact `Decimal128`.
- **Retries** (section 12) are as specified: at most 3 attempts for a refused connection, 429 and 5xx, honouring `Retry-After` up to 10 s. Timeouts and other 4xx are not retried.
- **Privacy** (section 13): with local models, ticket text never leaves this computer.
