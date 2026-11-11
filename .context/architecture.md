# System Architecture (as built, 2026-11-11)

This describes the code as it is. Product intent is in `requirements.md`; status, decisions and history are in `PROGRESS.md`.

## 1. Overview

TicketLens is a local-first, single-user web app. There is no login.

```text
Browser (React + Vite, localhost:5173)
   │  HTTP, JSON
   ▼
FastAPI backend (127.0.0.1:8000) ──────► MongoDB Community (127.0.0.1:27017, database "ticketlens")
   │
   ▼  provider adapters (backend only)
   ├─ Jev side:  AutoTrust JEV via Ollama's System One API   (in use)
   │             TypeSafe's hosted Jev, same API              (built, deferred: needs a paid key)
   ├─ LLM side:  Ollama chat model, such as qwen3:8b          (in use)
   │             OpenAI                                       (not built, deferred by owner decision)
   └─ Fake AI:   MOCK_PROVIDERS=true, no network, no cost
```

- **The browser never calls an AI provider.** All provider calls go through FastAPI, so keys stay server-side.
- **The paid APIs (hosted Jev and OpenAI) are deferred** by the owner (2026-11-11). Their architecture is kept so they can be added later; see section 4.

## 2. Code layout

### Backend (`backend/app/`)

| Folder | Role |
|---|---|
| `main.py` | App factory. On startup it connects to MongoDB, creates indexes, marks interrupted work and loads the saved taxonomy. Also mounts the routers, CORS and the 503 handler for a missing database. Production turns the API docs off. |
| `api/` | Route handlers only: validate input, call a service, map errors to HTTP. `deps.py` provides the database handle. |
| `services/` | Workflows: `tickets`, `executions` (one AI run), `comparisons`, `csv_import`, `csv_export`, `dashboard`, `evaluation` (accuracy), `run_metrics` and `run_report` (reports), `app_settings` (saved settings). |
| `jobs/bulk.py` | Bulk runs: an in-process worker pool. |
| `providers/` | AI adapters behind one contract: `base.py` (contract, input building, failure kinds), `jev.py`, `ollama.py`, `mock.py`, `registry.py` (picks the adapter for each side), `http.py` (the shared HTTP call with bounded retries), `definitions.py` (task definitions both sides receive). |
| `repositories/` | All MongoDB access. Only this layer talks to PyMongo. `database.py` holds the connection, indexes and the Decimal codec. |
| `schemas/` | Pydantic request and response models. |
| `core/` | `settings.py` (the only reader of environment variables), `taxonomy.py` (canonical values and the active taxonomy), `pricing.py`, `redaction.py`, `clock.py`. |

Scripts: `backend/scripts/init_db.py` (create indexes) and `run_report.py` (HTML test-run report).

### Frontend (`frontend/src/`)

| Folder | Role |
|---|---|
| `app/` | Router, app shell (sidebar, header badges, search, theme toggle, bulk-run banner) and the not-found page. |
| `features/` | One folder per area: `tickets`, `compare`, `comparisons`, `executions`, `bulk`, `dashboard`, `settings`. |
| `components/` | Shared pieces (`states`, `ConfirmDialog`, `Detail`, `ListControls`) and shadcn/ui primitives in `ui/`. |
| `services/api.ts` | The one HTTP client. `queries.ts` holds shared queries (taxonomy, provider status). |
| `types/api.ts` | API response types. Enum values come from `GET /api/taxonomy`, not hard-coded lists. |
| `lib/format.ts` | Date, duration, cost and side-label formatting. |

Stack: React 19, Vite, TypeScript, Tailwind 4, shadcn/ui, React Router, TanStack Query, React Hook Form + Zod, Recharts, lucide-react, sonner.

## 3. Naming: "gpt" means the LLM side

The original spec compared Jev with OpenAI GPT. The internal provider key stays `gpt` (in the API, stored records and code) and means **the LLM side**, whichever model serves it. The UI says "LLM". Renaming the key would change stored data and the API, so it was deliberately left alone.

## 4. Provider adapters

Contract (`providers/base.py`): `Adapter.classify(data: ProviderInput) -> ProviderResult`, which raises `ProviderFailure(kind, message, ...)` with a user-safe message.

| Owned by the adapter | Owned by `services/executions.run` |
|---|---|
| Request shape, authentication, response parsing, usage extraction, mapping errors to failure kinds | Writing the run record as Running before the call, timing it, validating the answer against the taxonomy, redacting payloads, cost from the rate snapshot, storing the outcome. A failure is recorded and returned, never raised. |

**Input** (`build_input`): ticket ID, title, description, order ID, product name, channel, language, taxonomy version, allowed categories, priorities and sentiments, and the saved prompt text. **Never sent:** labels, earlier results, the final classification, notes, customer name or email. Tests check this.

**Jev side** (`jev.py`): System One `POST {JEV_BASE_URL}/v1/systemone`. It asks in two steps, because AutoTrust accepts only 2 to 16 options per `choice` question and the taxonomy has 36 subcategories:
1. `choice` for category, priority and sentiment, and `noul` for escalation (yes if the probability is at least `JEV_ESCALATION_THRESHOLD`).
2. `choice` among only the chosen category's subcategories.

Both steps' payloads are stored as `{"steps": [...]}` and their token counts are summed. Jev returns typed decisions only, so summary and suggested resolution are marked unsupported. A local URL needs no key; a hosted one needs `TYPESAFE_API_KEY` and sends it as a Bearer token.

**LLM side** (`ollama.py`): `POST {OLLAMA_BASE_URL}/api/chat` with a JSON schema whose enums come from the active taxonomy, `temperature 0` and `think: false`. It returns all five fields plus an English summary and suggested resolution. It can still pair a subcategory with the wrong category; validation records that as `Invalid Response`. `LLM_BACKEND=openai` exists in settings, but the OpenAI adapter is not built: runs record `not_configured` (deferred by owner decision).

**Fake AI** (`mock.py`): deterministic keyword rules with a fake delay. Putting `[mock-fail]`, `[mock-timeout]` or `[mock-invalid]` in a title simulates failures. Runs are labelled `mock-*`, never scored and never priced.

**Retries** (`http.py`): at most 3 attempts. Only a refused connection (nothing was sent), HTTP 429 and 5xx are retried, with growing delays plus jitter and `Retry-After` honoured up to 10 s. Other 4xx, timeouts and broken connections are never retried, because the provider may already have processed and charged for the call.

## 5. Request flows

**One side, one ticket:** `POST /api/tickets/{id}/runs/{jev|gpt}` runs synchronously and returns the run record, whatever happened.

**Both sides (Compare page):** the browser sends two run requests in parallel, so each column's timer stops on its own, then `POST /api/comparisons` with both run IDs. The comparison is Completed, Partial (one side failed) or Unavailable. There is no server-side "run both" endpoint (a deviation from the original plan): closing the browser mid-run keeps the runs but saves no comparison.

**Final answer:** `PUT /api/tickets/{id}/final-classification`. It optionally names a successful run of the same ticket, and the server records whether the answer was edited. Nothing ever sets it automatically.

**Bulk** (`jobs/bulk.py`):
- `POST /api/bulk-jobs` takes a ticket list, or `all_eligible`, plus the sides.
- One job runs at a time (a second gets 409), on a request background task with `BULK_CONCURRENCY` tickets at once. Each ticket's sides run one after another, and a comparison is made when both sides ran.
- "Eligible" means Open or In Progress. In an all-eligible run, a side that already succeeded on that ticket with the same model is Skipped.
- Progress is saved after every attempt, using atomic `$push` and `$inc`.
- On startup, Queued or Running jobs become Interrupted and Running runs become Cancelled. Neither is resumed.

**Accuracy** (`services/evaluation.py`): for each labelled ticket, each side's latest finished non-fake run is scored against `evaluation_labels`, giving per-field accuracy, exact match, macro-F1 (from 30 answered tickets), confusion matrices and head-to-head counts. Failed runs are counted separately and not as wrong.

**Settings** (`services/app_settings.py`): saved values in `app_settings` overlay the environment defaults per run (`effective()`):
- **Models**, threshold and concurrency.
- **Prompt and taxonomy:** a new version (1.0, 1.1, …) with history on every change. Labels used by stored records cannot be removed (409), and each level needs 2 to 16 options.
- **Rates:** saved per side and model.

**CSV import:** validates each row, normalises values to canonical case, finds duplicates by a fingerprint of normalised fields, and stores optional `expected_*` labels in `evaluation_labels`. A dry run is available, and import never runs AI.

**Delete ticket:** deletes comparisons, runs and labels first, then the ticket. A failure keeps the ticket, so a retry can finish the job. Standalone MongoDB has no transactions.

## 6. API routes

| Area | Routes |
|---|---|
| Health | `GET /api/health`, `GET /api/health/ready` |
| Reference | `GET /api/taxonomy`, `GET /api/providers/status` |
| Tickets | `POST/GET /api/tickets`, `GET/PATCH/DELETE /api/tickets/{id}`, `POST /api/tickets/{id}/notes`, `PUT /api/tickets/{id}/final-classification` |
| Import and export | `GET /api/imports/template`, `GET /api/imports/sample-dataset`, `POST /api/imports/tickets?dry_run=`, `GET /api/exports/{tickets\|executions\|comparisons}.csv` |
| Runs | `POST /api/tickets/{id}/runs/{jev\|gpt}`, `GET /api/executions` (filters, paging), `GET /api/executions/{id}` |
| Comparisons | `POST /api/comparisons`, `GET /api/comparisons?limit=&ticket_id=`, `GET /api/comparisons/{id}` |
| Bulk | `POST/GET /api/bulk-jobs`, `GET /api/bulk-jobs/{id}` |
| Overview | `GET /api/dashboard`, `GET /api/evaluation` |
| Settings | `GET/PATCH /api/settings`, `PUT /api/settings/{prompt\|taxonomy\|pricing}`, `GET /api/settings/models/{jev\|llm}` |

Interactive docs: http://127.0.0.1:8000/docs (development only).

## 7. Data

Collections and fields: `data-model.md`. Money is stored as exact `Decimal128`. Timestamps are UTC.

## 8. Runtime, security and limits

- **Bindings:** frontend `localhost:5173`, backend `127.0.0.1:8000`, MongoDB `127.0.0.1:27017`, Ollama `127.0.0.1:11434`. Everything binds to loopback.
- **CORS** allows one exact origin (`FRONTEND_ORIGIN`).
- **Health:** `/api/health` (process up) and `/api/health/ready` (database reachable, otherwise 503).
- **Secrets** are read only in `core/settings.py`, are `SecretStr`, and are redacted from stored payloads (`core/redaction.py`). Settings errors never echo input values.
- **One backend process only.** The active taxonomy is held in memory, and startup marks unfinished bulk work as interrupted, so a second worker would break both. Both are marked as `shortcut:` in the code.
- **Production** (`APP_ENV=production`) refuses to start with a local database, a non-https origin, fake AI, or without `ACCESS_CONTROL_CONFIRMED=true`. See `DEPLOYMENT_DECISIONS.md`.
- **No login.** Do not expose the app publicly as it is.
