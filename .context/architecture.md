# System Architecture

## 1. Overview

TicketLens is a local-first, single-user web application.

```text
Browser
  |
  | React + Vite UI
  v
FastAPI backend (localhost)
  |                 |
  |                 +----------------------+
  |                                        |
  v                                        v
MongoDB Community                    AI Provider Adapters
(local machine)                       |             |
                                      v             v
                                 TypeSafe Jev    OpenAI GPT
```

The browser never calls Jev or OpenAI directly. All provider requests pass through FastAPI so API keys remain private.

## 2. Technology choices

### Frontend
- React + Vite + TypeScript
- Tailwind CSS + shadcn/ui
- React Router for pages
- TanStack Query for API state, caching, invalidation, and polling
- React Hook Form + Zod for forms and validation
- Recharts for dashboard charts

### Backend
- FastAPI for HTTP endpoints and OpenAPI docs
- Pydantic for request/response schemas
- PyMongo for MongoDB access
- HTTPX for provider HTTP calls
- Pydantic Settings or python-dotenv for configuration
- pytest for tests

Use a straightforward layered structure:
- `api/`: route handlers
- `schemas/`: request and response contracts
- `services/`: business workflows
- `providers/`: Jev and GPT adapters
- `repositories/`: MongoDB access
- `core/`: settings, taxonomy, logging, errors
- `jobs/`: in-process bulk job runner

## 3. Provider adapter boundary

Expose a common application-level interface such as:

- `classify(ticket, taxonomy, prompt_config) -> ProviderExecutionResult`

Provider adapters own:
- authentication
- provider-specific request shape
- provider-specific response parsing
- provider usage extraction
- safe error normalization

The service layer owns:
- creating an execution record before/at request start
- duration and status measurement
- cost calculation using the pricing snapshot
- result validation against the current taxonomy
- persisting raw and normalized records
- creating/updating comparison records

Do not leak provider-specific response structures into React. Return a normalized API response and retain raw provider data only for the execution detail/log view.

## 4. Jev-specific behavior

**Local option (2026-11-07):** `JEV_BASE_URL=http://127.0.0.1:11434` with `JEV_MODEL=autotrust-jev:9b` sends the same System One request to Ollama, which serves AutoTrust's open JEV model locally with no key. The adapter is `backend/app/providers/jev.py`.

Official API reference: https://api.typesafe.ai/redoc

Relevant documented endpoints:
- `GET https://api.typesafe.ai/v1/models`
- `POST https://api.typesafe.ai/v1/systemone`

Authentication: `Authorization: Bearer <API_KEY>`.

The System One request includes `model`, `state`, and named `questions`. Supported documented question types include:
- `choice`: select one of a defined set of options; response includes selected choice, confidence, and probabilities.
- `noul`: yes/no probability.
- `score`: probability-weighted score against ordered criteria.

The response includes the model used, named answers, and `usage.input_tokens` / `usage.output_tokens`.

Use `choice` for category, subcategory, priority, and sentiment; use `noul` for escalation. Validate all returned choice names and category/subcategory combinations. Store confidence/probabilities.

Jev does not provide general free-form text generation in this documented API. Do not fabricate summaries or resolutions. Mark those fields unsupported for Jev.

Do not hardcode a model if the authenticated model list is available. Provide a model refresh/test action in Settings if feasible; otherwise load models at backend startup or on demand and cache briefly.

## 5. GPT-specific behavior

**Local default (2026-11-07):** `LLM_BACKEND=ollama` with `OLLAMA_MODEL=qwen3:8b` calls Ollama's `/api/chat` with a JSON schema that restricts every enum field to the taxonomy (`backend/app/providers/ollama.py`). `LLM_BACKEND=openai` selects OpenAI once its adapter is built. Both sides receive the same task definitions (`backend/app/providers/definitions.py`).

Use the official OpenAI Python SDK and the currently documented Responses API with structured output / JSON schema support. Confirm current SDK/API details during implementation.

The GPT adapter should:
- receive the same canonical ticket input and taxonomy as Jev
- request a strict structured classification schema
- validate the response with Pydantic
- extract provider-reported token usage when available
- store requested and actual model identifiers
- produce English summary and suggested resolution

The GPT model name is configurable. Do not assume a model name is permanently valid; make it a setting and validate provider errors clearly.

## 6. Canonical provider input

Both providers receive the same safe, normalized input:
- ticket ID (optional if it does not bias the model; use consistently)
- title
- original description
- customer/order/product context if present
- submission channel
- language note (English only)
- taxonomy version and allowed labels
- classification definitions

Never include:
- expected/ground-truth labels
- previous provider outputs
- comparison result
- manually selected final classification
- API keys or secrets

Use identical ticket content and definitions. Provider-specific serialization may differ, but semantic input must be equivalent.

## 7. Request flows

### Single provider execution
1. UI requests Jev or GPT execution for a ticket.
2. FastAPI verifies the ticket exists and validates the provider choice.
3. Backend creates an execution record with `Running` status and start timestamp.
4. Provider adapter sends request.
5. Backend extracts raw response and usage.
6. Backend validates and normalizes the result.
7. Backend calculates estimated cost using the pricing snapshot.
8. Backend updates the execution record to success/failure.
9. UI refreshes ticket history and execution detail.

### Run both / compare
1. Create a comparison group/record for the ticket.
2. Start Jev and GPT independently, preferably concurrently with bounded timeouts.
3. Persist each execution independently.
4. If both succeed, compare the five shared classification fields.
5. If one fails, retain the successful result and mark comparison partial.
6. Never select a winner automatically.
7. UI displays side-by-side outputs and field-level agreement.

### Bulk processing
- UI sends selected ticket IDs or an explicit `all eligible` instruction plus provider mode.
- Backend validates and creates a `bulk_jobs` record.
- An in-process background worker processes tickets with bounded concurrency (default 2; configurable).
- Each provider call creates its own execution log.
- Job status records total, completed, failed, skipped, and current progress.
- UI polls job status and can navigate away without losing persisted progress.
- On backend restart, mark interrupted jobs as `Interrupted`; do not silently resume paid requests.

### CSV import
1. UI uploads CSV to backend.
2. Backend parses and validates each row.
3. Normalize whitespace, email, channel, and enum values.
4. Compute duplicate fingerprint using stable normalized ticket fields; if source has an external ticket key, include it.
5. Insert valid non-duplicate rows.
6. Return imported/invalid/duplicate counts and row-level errors.
7. Never run AI automatically after import.

### Ticket deletion
Delete dependent comparisons and execution records first, then delete the ticket. If any dependent deletion fails, do not delete the parent ticket. Make the operation idempotent and report failure clearly. This avoids requiring MongoDB replica-set transactions for the local standalone setup.

## 8. MongoDB collections

See `data-model.md` for complete document shapes:
- `tickets`
- `ai_executions`
- `comparisons`
- `bulk_jobs`
- `app_settings`
- `counters`

Use MongoDB-generated `_id` values internally and explicit `ticket_id` for human-readable IDs.

## 9. Local runtime and CORS

- Frontend default: `http://localhost:5173`
- Backend default: `http://127.0.0.1:8000`
- MongoDB default: `mongodb://127.0.0.1:27017`
- Database: `ticketlens`
- Configure CORS for the exact local frontend origin only.
- Bind backend to loopback for local use.
- Do not bind MongoDB to a public interface.
- Provide `/api/health` and `/api/health/ready` (or equivalent) to distinguish process health from database readiness.

## 10. Deployment boundary

No hosting platform has been selected. The initial target is local execution and deployment readiness, not a specific cloud provider.

A local MongoDB instance cannot serve a cloud-hosted backend through `localhost`. Before public/cloud deployment:
1. choose a hosting platform,
2. provision a reachable, secured production MongoDB service,
3. configure production secrets,
4. add authentication/access control,
5. restrict CORS and network access,
6. configure HTTPS, backups, monitoring, and retention,
7. run migration and production smoke tests.

Do not expose the unauthenticated initial demo publicly. Do not attempt to tunnel the local MongoDB port to the internet.
