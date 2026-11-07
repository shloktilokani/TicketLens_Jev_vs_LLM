# End-to-End Implementation Plan

Project: **TicketLens_Jev_vs_LLM**

This is the authoritative, sequential implementation plan. Build one phase at a time. Do not skip acceptance criteria.

## Phase 0 — Repository and agent setup

1. Create the repository root `TicketLens_Jev_vs_LLM`.
2. Add all supplied documentation files.
3. Read `AGENTS.md` and this implementation plan.
4. Create `PROGRESS.md` with every phase as a checklist.
5. Create `.gitignore` for `.env`, virtual environments, `node_modules`, build output, caches, logs, and local exports.
6. Create root README run instructions and architecture links.

Acceptance:
- Repository structure exists.
- Secrets and local database files are ignored.
- Agent progress file exists.

## Phase 1 — Scaffold the frontend and backend

Suggested structure:

```text
TicketLens_Jev_vs_LLM/
  frontend/
    src/
      app/
      components/
      features/
        dashboard/
        tickets/
        comparisons/
        executions/
        settings/
      lib/
      services/
      types/
    public/
    package.json
    vite.config.ts
  backend/
    app/
      api/
      core/
      jobs/
      providers/
      repositories/
      schemas/
      services/
      main.py
    tests/
    requirements.txt
    .env.example
  README.md
  AGENTS.md
  CLAUDE.md
  .context/
    implementation.md
    design.md
    architecture.md
    requirements.md
    data-model.md
    ai-evaluation.md
    DEPLOYMENT_DECISIONS.md
    sample_tickets_template.csv
    sample_tickets_100.csv
    PROGRESS.md
```

1. Scaffold React + Vite + TypeScript in `frontend`.
2. Install Tailwind CSS using the current Vite-compatible setup.
3. Initialize shadcn/ui and add only required components.
4. Install React Router, TanStack Query, React Hook Form, Zod, Recharts, and Lucide icons.
5. Scaffold FastAPI backend and Python virtual environment.
6. Add FastAPI, Uvicorn, Pydantic Settings, PyMongo, HTTPX, pytest, and required test tools.
7. Add lint/format configuration appropriate to TypeScript and Python.

Acceptance:
- Frontend starts locally.
- Backend starts locally.
- `/docs` serves FastAPI Swagger UI.
- No provider keys are needed to start either application.

## Phase 2 — Local configuration and MongoDB connectivity

1. Implement backend settings loaded from environment.
2. Create `.env.example`; do not create or commit a real `.env`.
3. Configure MongoDB URI default `mongodb://127.0.0.1:27017` and database `ticketlens`.
4. Create database connection lifecycle and repository base utilities.
5. Implement `/api/health` for process health.
6. Implement `/api/health/ready` to verify MongoDB connectivity.
7. Create index initialization for all collections described in `data-model.md`.
8. Create an explicit `scripts/init_db.py` or equivalent for database/index initialization.
9. The human operator installs MongoDB Community Edition locally. The coding agent may start it on loopback (`127.0.0.1`) only, as delegated by the owner on 2026-11-07. The agent must not install MongoDB, use Docker, or expose MongoDB publicly.
10. Show a clear setup error if MongoDB is unavailable.

Acceptance:
- Backend reports healthy when running.
- Readiness reports database unavailable when MongoDB is stopped.
- Readiness succeeds when local MongoDB is running.
- Index initialization is repeatable and safe.

## Phase 3 — Domain schemas and taxonomy

1. Implement Pydantic models for tickets, classifications, provider results, executions, comparisons, imports, and bulk jobs.
2. Implement canonical category/subcategory taxonomy from `requirements.md`.
3. Implement enums for priority, sentiment, status, channel, provider, and execution status.
4. Add taxonomy versioning.
5. Implement validation for category/subcategory pair consistency.
6. Add unit tests for all enums and validation cases.

Acceptance:
- Invalid category/subcategory combinations are rejected.
- API schemas and frontend types use the same canonical values.
- Taxonomy version is stored with ticket classifications and AI executions.

## Phase 4 — Ticket CRUD and sequential IDs

1. Implement repository methods for ticket create/read/update/delete/list.
2. Implement atomic sequential ID allocation using the `counters` collection.
3. Format IDs as `SK-1001`, `SK-1002`, etc.
4. Implement ticket creation with required/optional field validation.
5. Implement ticket update and status changes.
6. Implement operator notes.
7. Implement search by ticket ID, title, customer name/email, and order ID.
8. Implement category/priority/status filters and date/priority sorting.
9. Implement pagination or bounded list loading.
10. Implement deletion cascade in the order specified in `data-model.md`.
11. Add tests for ID uniqueness, CRUD, filters, and deletion failure behavior.

Acceptance:
- Tickets can be created and receive unique sequential IDs.
- Search/filter/sort work.
- Deleting a ticket removes dependent execution/comparison/evaluation records.
- Failed dependent deletion does not delete the parent ticket.

## Phase 5 — Frontend shell and design system

1. Build the app shell with sidebar and header.
2. Add routes listed in `design.md`.
3. Configure shadcn/ui components and Tailwind semantic theme tokens.
4. Implement light/dark theme toggle and persist selection locally.
5. Implement responsive sidebar/drawer.
6. Add reusable loading, error, empty, confirmation, and toast components.
7. Add API client and TanStack Query setup.
8. Add typed frontend API contracts.

Acceptance:
- Every route loads.
- Theme toggle works.
- Layout is usable on desktop/tablet.
- No page uses mock success responses in place of backend APIs.

## Phase 6 — Ticket screens

1. Build ticket list with search, filters, sorting, pagination.
2. Build create-ticket form with React Hook Form and Zod.
3. Build ticket detail page.
4. Add edit ticket form and status selector.
5. Add notes section.
6. Add delete confirmation dialog.
7. Add empty states and validation messages.
8. Preserve ticket text exactly as entered, in inputs and display.

Acceptance:
- Manual ticket creation and editing work end to end.
- Ticket IDs appear after successful creation.
- Status and notes persist.
- Delete behavior matches requirements.

## Phase 7 — CSV template, import, and export

1. Implement CSV parser and row-level validation on backend.
2. Provide downloadable template using `sample_tickets_template.csv`.
3. Implement normalized duplicate fingerprint generation.
4. Skip duplicate rows and report them separately.
5. Import valid rows even if other rows fail.
6. Return row number, field, and validation message for invalid rows.
7. Implement import preview/result UI.
8. Implement export endpoints for tickets, execution logs, and comparisons.
9. Ensure exports redact credentials and do not include secrets.
10. Do not run AI automatically after import.

Acceptance:
- Mixed valid/invalid/duplicate CSV returns accurate counts.
- Valid rows are imported.
- Invalid rows are reported.
- Duplicate rows are skipped.
- Exports open as valid CSV files.

## Phase 8 — Provider adapter contracts and mock mode

1. Define a shared provider interface and normalized result schema.
2. Define safe provider error types.
3. Implement mock Jev and mock GPT adapters for tests and local UI development.
4. Add tests for response normalization and provider failures.
5. Ensure every execution attempt can be logged before provider integration is complete.

Acceptance:
- Application can be developed/tested without paid API calls.
- Mock responses follow the exact normalized schema.
- Provider-specific data does not leak into frontend contracts.

## Phase 9 — Jev integration

1. Read current TypeSafe API documentation: `https://api.typesafe.ai/redoc`.
2. Implement model discovery using `GET /v1/models`.
3. Implement `POST /v1/systemone` with Bearer authentication.
4. Use `choice` questions for category, subcategory, priority, and sentiment.
5. Use `noul` for escalation probability.
6. Parse confidence/probabilities and token usage.
7. Validate choices against the taxonomy.
8. Implement configurable escalation threshold (default 0.5).
9. Persist redacted request, raw response, normalized result, timing, usage, and cost.
10. Display summary and suggested resolution as unsupported for Jev.
11. Add mocked unit tests and an optional live integration test that runs only when a Jev key is configured.

Acceptance:
- Jev can classify a ticket through FastAPI.
- Token usage is captured when returned.
- Confidence/probabilities are preserved.
- Invalid outputs are logged as invalid responses.
- API key never reaches the browser or logs.

## Phase 10 — GPT integration

1. Read current official OpenAI Python SDK and Responses API documentation.
2. Implement structured output with the five shared fields plus English summary and suggested resolution.
3. Make GPT model configurable from backend settings.
4. Validate response against Pydantic schema and taxonomy.
5. Extract provider-reported usage.
6. Calculate estimated cost using the configured pricing snapshot.
7. Persist redacted request/response and all execution metadata.
8. Add mock tests and optional live integration tests when an OpenAI key is configured.

Acceptance:
- GPT can classify a ticket.
- All seven GPT output fields validate.
- Usage and cost are logged where available.
- API key never reaches frontend or logs.

## Phase 11 — Execution history and cost logging

1. Implement `ai_executions` repository and service.
2. Create an execution record for each provider attempt.
3. Record failed, timed-out, invalid, and successful executions.
4. Store token counts, total tokens, duration, pricing snapshot, and estimated cost.
5. Store full redacted request and response payloads.
6. Implement execution list/detail API and UI.
7. Add provider/status/date/ticket filters.
8. Add CSV export.
9. Add tests for cost formulas and missing usage.

Acceptance:
- Every attempt creates a persistent execution record.
- Failed calls remain inspectable.
- Historical cost uses the rate snapshot from the time of execution.
- Secrets are absent from stored payloads.

## Phase 12 — Comparison workflow

1. Implement run-one-provider and run-both endpoints.
2. For run-both, execute providers independently and concurrently with bounded timeout.
3. Create comparison record linking execution IDs.
4. Compare category, subcategory, priority, sentiment, escalation only.
5. Show field-level agreement/disagreement.
6. Mark comparison partial if one provider fails.
7. Never automatically choose a winner.
8. Build comparison list/detail UI.
9. Add manual final-classification selection/editing on ticket detail.

Acceptance:
- Jev-only, GPT-only, and compare-both work.
- One provider failure does not erase the other result.
- Comparison records show accurate shared-field matches.
- Final classification changes only after explicit operator action.

## Phase 13 — Bulk processing

1. Implement bulk job schema/repository/service.
2. Support selected ticket IDs and all eligible tickets.
3. Support Jev-only, GPT-only, and both providers.
4. Process with bounded concurrency (default 2).
5. Persist progress and per-ticket outcomes.
6. Implement polling endpoint.
7. Build bulk selection toolbar and progress UI.
8. Mark interrupted jobs after backend restart; do not silently repeat paid calls.

Acceptance:
- Selected and all-ticket bulk modes work.
- Progress is visible and persisted.
- Individual execution records exist for each provider attempt.
- Failures are summarized without stopping unrelated tickets.

## Phase 14 — Evaluation dataset and analytics

1. Generate 100 synthetic ShopKart tickets across six categories.
2. Write all tickets in English (Hindi and Hinglish dropped by the owner, 2026-11-07).
3. Include expected labels for five shared fields.
4. Export labelled dataset as CSV; do not auto-seed.
5. Store labels in `evaluation_labels`, separate from tickets and provider inputs.
6. Ensure labels are never included in model requests.
7. Implement per-field accuracy, overall exact match, macro-F1/confusion matrix where appropriate.
8. Implement agreement vs ground-truth accuracy distinction.
9. Build dashboard metric cards and Recharts visualizations.
10. Handle no-data state without showing misleading charts.

Acceptance:
- Dataset contains exactly 100 synthetic labelled rows.
- Import creates ticket records and separate evaluation labels.
- Model execution payloads contain no ground-truth labels.
- Metrics are reproducible and show denominators.

## Phase 15 — Settings page

1. Implement settings read/update API.
2. Add GPT model selection.
3. Add Jev model list/selection or refresh.
4. Add prompt editor with version history.
5. Add taxonomy management with validation and versioning.
6. Add pricing configuration per provider/model.
7. Add Jev escalation threshold.
8. Add bulk concurrency control.
9. Show provider configured/not configured state without exposing secrets.
10. Keep API keys in backend `.env` only.

Acceptance:
- Settings persist in MongoDB.
- Old execution records retain old prompt/taxonomy/pricing snapshots.
- API keys cannot be read or changed through the UI.

## Phase 16 — Testing, reliability, and security review

1. Add unit tests for schemas, taxonomy, costs, imports, provider adapters, and repositories.
2. Add API integration tests using a disposable test database.
3. Add frontend tests for forms, filters, comparison rendering, and error states.
4. Add end-to-end tests for create → classify → compare → select final → export → delete.
5. Test provider failures, timeout, malformed response, invalid key, insufficient credits, and rate limits using mocks.
6. Add bounded retries only for transient errors.
7. Verify CORS, localhost binding, secret handling, and log redaction.
8. Verify no ground-truth leakage to providers.
9. Run frontend lint/build and backend lint/tests.

Acceptance:
- All automated checks pass.
- No secrets appear in Git history, browser bundles, logs, or exported files.
- No public network binding is enabled by default.

## Phase 17 — Local release and documentation

1. Create final root README with setup instructions.
2. Document MongoDB Community installation/start steps at a high level, with OS-specific official links rather than assuming the OS.
3. Document creation of `.env` from `.env.example`.
4. Document API key setup.
5. Document frontend/backend run commands.
6. Document CSV import, AI execution, comparison, evaluation, and export.
7. Add troubleshooting for MongoDB unavailable, invalid keys, Jev insufficient credits, GPT quota/rate errors, and CORS.
8. Add final `PROGRESS.md` completion report.

Acceptance:
- A developer can clone the repo, configure local MongoDB and API keys, run both services, and use the app by following README only.

## Phase 18 — Deployment readiness (platform intentionally undecided)

Prepare the application for deployment without choosing a provider or exposing the local database.

1. Separate development and production configuration.
2. Ensure production secrets are environment-injected.
3. Add production build and health checks.
4. Add secure CORS configuration.
5. Add HTTPS/proxy-aware configuration.
6. Document database backup/restore and migration steps.
7. Document logging/monitoring requirements.
8. Document production MongoDB requirements.
9. Add authentication/access-control requirement before public exposure.
10. Create `DEPLOYMENT_DECISIONS.md` listing what must be selected before actual deployment.

Important:
- The local MongoDB URI is not usable from a cloud-hosted backend.
- Do not expose the local MongoDB port publicly.
- A cloud deployment requires a production MongoDB service reachable from the backend (for example, MongoDB Atlas or a secured self-managed MongoDB deployment).
- The initial no-auth single-user demo must not be deployed publicly as-is.
- Do not select a paid hosting provider or provision infrastructure without explicit approval.

Acceptance:
- Production configuration and deployment instructions are documented.
- The app builds successfully for production.
- Remaining deployment blockers are explicitly listed; no infrastructure is provisioned without approval.

## Final definition of done

The project is complete when:
- all local workflows operate end to end,
- both provider integrations work with real credentials,
- every provider attempt is logged with usage and estimated cost,
- 100 labelled synthetic tickets are available for manual import,
- evaluation and comparison dashboards work,
- tests pass,
- the local setup is documented,
- production deployment prerequisites are documented without pretending local MongoDB can be used as a cloud database.
