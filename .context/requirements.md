# Product and Technical Requirements

## 1. Product identity

- Project/repository name: `TicketLens_Jev_vs_LLM`
- Product: TicketLens
- Fictional business: ShopKart, an Indian e-commerce marketplace
- Primary purpose: demonstrate and evaluate structured AI classification of customer-support tickets using Jev and GPT.

## 2. Intended operator

The first release is a **single-user demonstration application** operated by one person locally.

There is no customer-facing portal, login, authentication, role system, or multi-user workflow in the initial version. The app must bind to localhost for local use. Public exposure is prohibited until authentication and production security are added.

## 3. Business context

ShopKart sells electronics, clothing, groceries, home appliances, and other products across India. Its customer-support tickets cover order fulfilment, payments, returns, product problems, accounts, and general enquiries.

The application uses fictional/synthetic customer and ticket data only.

## 4. Ticket lifecycle and data

### Ticket fields

Required:
- `ticket_id`: generated sequential identifier, e.g. `SK-1001`
- `title`
- `description`
- `customer_name`
- `customer_email`
- `submission_channel`: `Email`, `Chat`, `Phone`, or `Website`
- `status`: `Open`, `In Progress`, `Resolved`, or `Closed`
- `created_at`, `updated_at`

Optional:
- `order_id`
- `product_name`
- manually selected final classification
- operator notes

### Ticket categories

Use these six top-level categories:
1. Orders & Delivery
2. Payments & Billing
3. Returns & Refunds
4. Product Issues
5. Account & Login
6. General Enquiries

The default subcategory taxonomy must be centrally defined and versioned. The Settings page may manage the taxonomy, but prevent deletion/renaming that would invalidate historical records. Existing records retain the taxonomy label/version used when classified.

### Initial subcategory taxonomy

- Orders & Delivery: Order Status; Delayed Delivery; Missing Package; Wrong Item Delivered; Address Change; Delivery Attempt Failed; Damaged in Transit.
- Payments & Billing: Payment Failed; Duplicate Charge; Refund Status; Invoice Request; Payment Method; Promotional Discount.
- Returns & Refunds: Return Request; Return Pickup; Refund Delay; Exchange Request; Return Rejected; Cancellation.
- Product Issues: Defective Product; Damaged Product; Missing Parts; Product Information; Warranty; Wrong Product.
- Account & Login: Login Failure; Password Reset; Account Locked; Profile Update; Account Access; Verification.
- General Enquiries: Store Policy; Product Availability; Feedback; Complaint; Other.

If a category/subcategory pair is inconsistent, reject or flag the output for review rather than silently rewriting it.

### Other classification fields

- Priority: `Critical`, `High`, `Medium`, `Low`
- Sentiment: `Positive`, `Neutral`, `Negative`
- Escalation required: boolean
- Short summary: English text
- Suggested resolution: English text

The application supports English ticket text only (owner decision, 2026-11-07; Hindi and Hinglish were dropped). Preserve the original ticket text. All generated summaries and suggested resolutions must be in English.

## 5. AI provider behavior

- Providers: TypeSafe Jev and OpenAI GPT.
- **Provider change (owner decision, 2026-11-07):** both sides are switchable, and local models are the default until API keys exist. The **Jev side** uses TypeSafe's hosted Jev, or AutoTrust's open JEV model (`autotrust-jev:9b`) served locally by Ollama through the same System One API. AutoTrust JEV is not TypeSafe's Jev and is labelled as such. The **LLM side** (called "GPT" in the rest of this document) uses a local Ollama model (`qwen3:8b`) by default, or OpenAI. Wherever this document says GPT, read "the LLM side".
- The GPT model is configurable; default model comes from backend configuration and can be changed from Settings using a validated model identifier.
- Jev model must be discovered/configured using TypeSafe's documented model list endpoint; do not hardcode an undocumented model name. `jev-latest` may be used as the documented default alias when available.
- The operator can run Jev only, GPT only, or both.
- Bulk processing supports selected tickets or all eligible tickets, with Jev-only, GPT-only, or both.
- Run providers independently. A failure from one provider must not block the other.
- Both providers receive the same normalized ticket content, taxonomy version, and classification definitions.
- No model is automatically selected as the final answer. The operator manually selects or edits the final classification.
- Jev's documented System One API returns typed structured decisions, not free-form generated prose. Compare Jev and GPT only on common structured fields. For Jev, summary and suggested resolution must display as `Not supported by Jev` (or equivalent), not fabricated text.
- GPT may produce all requested fields, including summary and suggested resolution, using a validated structured response.

## 6. Execution history and cost logging

Every AI execution attempt must be logged, including successful, failed, and partially completed attempts.

Store, when available:
- execution ID, ticket ID, provider, requested and actual model
- start/end timestamps and duration
- exact normalized input and provider request payload (credentials redacted)
- raw provider response payload (secrets/headers redacted)
- normalized output and validation warnings
- input tokens, output tokens, total tokens
- configured price snapshot and estimated cost
- HTTP status/provider error code and safe error message
- execution status: `Succeeded`, `Failed`, `Invalid Response`, `Cancelled`, or `Timed Out`
- taxonomy and prompt version identifiers

Use provider-reported token usage wherever available. If usage is unavailable, store null and label any estimate clearly. Do not invent token counts.

Cost calculation must be configurable and versioned:
- GPT: input and output rates per million tokens for the selected model; include cached-input rates only if supported and reported.
- Jev: input-token rate per million; output tokens are currently documented as free. Pricing must be configurable rather than embedded as a permanent constant.
- Show cost as estimated unless provider billing data confirms exact charges.
- Record the pricing snapshot used at execution time so historical totals do not change when rates are updated.

Store full request/response content because the operator explicitly wants detailed logs. Use synthetic ticket data only. Never store API keys, Authorization headers, or secrets in payload logs.

## 7. Comparison and evaluation

- Show side-by-side provider results.
- Highlight agreements and disagreements for category, subcategory, priority, sentiment, and escalation.
- Do not compare free-text summary/resolution as if Jev produced them.
- Save comparison records linked to the two execution IDs. If one provider fails, retain the successful execution and mark the comparison `Partial` or `Unavailable`.
- The 100 sample tickets must include expected labels for the five shared classification fields.
- Expected labels must never be sent to either provider.
- Report per-field accuracy and overall exact-match accuracy; include macro-F1/confusion matrix where appropriate and enough sample counts to interpret the metric.
- Report provider agreement separately from ground-truth accuracy. Agreement does not mean correctness.
- Confidence/probability values from Jev should be shown as provider-reported confidence, not treated as guaranteed correctness. Do not compare GPT self-reported confidence directly to Jev calibrated probabilities as equivalent measures.

## 8. Ticket management

The operator can:
- create tickets manually
- edit ticket/customer/order details
- change category, subcategory, priority, and status
- add internal notes
- choose/edit a final classification
- delete a ticket with confirmation

Deleting a ticket must also delete its AI executions, comparisons, and ticket-specific dependent records. Implement deletion idempotently and safely for a standalone local MongoDB deployment (do not assume multi-document transactions are available).

## 9. CSV import/export

- Manual ticket creation and CSV import are both supported.
- Provide a downloadable 100-ticket synthetic, labelled CSV dataset.
- Do not automatically seed the database.
- CSV import accepts valid rows and rejects invalid rows individually.
- Skip duplicates and report duplicate rows.
- Show a summary: total rows, imported, invalid, duplicates skipped, and row-level validation errors.
- Export tickets, AI execution logs, and comparison results as CSV.
- Never export API keys or authorization headers.
- Include an import template file and an in-app template download.

## 10. Dashboard

Show:
- total tickets
- open and resolved tickets
- tickets by category
- priority distribution
- Jev/GPT agreement and disagreement
- average AI processing time
- labelled-dataset evaluation metrics when available
- estimated provider costs and token totals

Charts:
- category distribution
- priority distribution
- Jev vs GPT evaluation accuracy
- agreement/disagreement

Use Recharts or a similarly lightweight React chart library.

## 11. Search and ticket history

Ticket list must support:
- search by ticket ID, title, customer name, customer email, and order ID
- filters by category, priority, and status
- sorting by creation date and priority
- pagination or bounded result loading

Ticket detail must show:
- original ticket data
- status and manual edits
- Jev execution history
- GPT execution history
- comparison history
- manually selected final classification
- operator notes

## 12. Settings page

Include:
- GPT model selection
- AI prompt configuration/versioning
- category and subcategory taxonomy management with validation
- provider pricing configuration

API keys remain in backend `.env` only and are not editable or retrievable through the UI.

## 13. Technical stack

Frontend:
- React
- Vite
- TypeScript
- Tailwind CSS
- shadcn/ui
- React Router
- TanStack Query
- React Hook Form + Zod
- Recharts
- Lucide icons

Backend:
- Python
- FastAPI
- Pydantic
- PyMongo
- HTTPX
- python-dotenv (or Pydantic Settings)
- pytest

Database:
- MongoDB Community Edition installed directly on the developer's computer
- no Docker for local database setup

## 14. Non-functional requirements

- Local-first and beginner-readable code.
- Clear separation between UI, API routes, business logic, database repositories, and provider adapters.
- Secrets only on backend.
- Input validation on both frontend and backend.
- Useful loading, empty, success, and error states.
- Accessible controls and keyboard navigation.
- Responsive layout for desktop and tablet; mobile remains usable.
- Structured application logs for operational errors, separate from persisted AI execution records.
- Unit and integration tests for critical workflows.
- No model training or fine-tuning.

## 15. As built (2026-11-11)

This document is the original intent. Where the app differs, this section wins. Status and decisions: `PROGRESS.md`; architecture: `architecture.md`.

- **Providers (section 5):** only local models are in use. AutoTrust JEV runs on the Jev side and an Ollama model on the LLM side. **Hosted Jev and OpenAI are deferred by owner decision (2026-11-11)**: hosted Jev is built but has never run with a real key, and OpenAI is not built. The UI says "LLM" for the side this document calls GPT.
- **Running both sides:** done from the Compare page, which sends two parallel requests and then saves a comparison. There is no server-side "run both" endpoint.
- **Bulk runs (section 5):** "all eligible" means tickets that are Open or In Progress. A side that already succeeded on a ticket with the same model is skipped in that mode. One bulk run at a time. Progress shows on every page and on a Bulk Runs page.
- **Ticket management (section 8):** category and priority change through the final classification, which can start from an AI run's answer or be set by hand. It never changes on its own.
- **Execution statuses (section 6):** `Running` is also used while a call is in progress. `Cancelled` marks runs cut off by a backend restart.
- **Dataset (section 9):** use `.context/sample_tickets_100_v2.csv`. The original `sample_tickets_100.csv` gives the answers away in its titles and is kept only for reference.
- **Dashboard (section 10):** the Overview page shows ticket counts, agreement, median times, cost, charts by field and side, recent comparisons and an accuracy section. Figures from fake AI are excluded.
- **Settings (section 12):** besides the model, prompt, taxonomy and prices, it sets the Jev escalation threshold and the bulk speed. Taxonomy edits need 2 to 16 options per level, the limit Jev accepts.
- **Language:** English only.
