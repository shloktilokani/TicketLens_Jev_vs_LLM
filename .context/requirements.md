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

The application supports English, Hindi, and Hinglish ticket text. Preserve the original ticket text. All generated summaries and suggested resolutions must be in English.

## 5. AI provider behavior

- Providers: TypeSafe Jev and OpenAI GPT.
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
