# Progress

Build order and acceptance criteria: `implementation.md`. Update this file after every phase.

## Status (2026-11-11)

**The app is complete for local use.** Phases 0-8 and 11-18 are done, and it runs end to end on local models: AutoTrust JEV on the Jev side and an Ollama LLM such as `qwen3:8b` on the LLM side.

**Paid APIs deferred by owner decision (2026-11-11).** Hosted TypeSafe Jev (Phase 9's live part) and OpenAI (Phase 10) are not needed for now. Their architecture is kept so they can be added later:
- the provider contract in `providers/base.py`
- the hosted-Jev path in `providers/jev.py`, built but never run with a real key
- the `LLM_BACKEND=openai` setting and its not-configured path in `providers/registry.py`
- per-run rate snapshots

Code is committed on branch `shlok-ai-dev` (latest `1049480`). The knowledge graph of the code is in `.ua/knowledge-graph.json` (see `.ua/RESUME.md`).

## Handover: start here

- **Run it:** follow `README.md`, "Run it locally". MongoDB, Ollama with two models, the backend on `:8000` and the frontend on `:5173`.
- **How it works:** `architecture.md` (layers, adapters, flows, routes) and `data-model.md` (collections, fields, indexes).
- **What it was meant to do:** `requirements.md`, `design.md` and `ai-evaluation.md`. Each ends with an "As built" section listing the differences.
- **Checks:** the commands in `CLAUDE.md`. Latest results (2026-11-11): `pytest` 335 passed; ruff, lint and build clean; Playwright 14 of 14 on desktop and phone.
- **Rules for agents:** `AGENTS.md`, `CLAUDE.md` and `code-size-standards.md`. The agent never commits; the owner does.
- **Known limits:**
  - one backend process only (the active taxonomy and bulk jobs live in memory)
  - no login, so do not expose it publicly
  - accuracy figures are preliminary until the dataset is reviewed
  - the knowledge graph has some generic function summaries
- **Open owner steps:** review dataset rows 4, 11, 30, 46, 52, 64, 81, 88, 95 and 100 (ROADMAP E); follow the README once (F); deployment decisions only if going online (G).
- **Likely next work, if wanted:** an OpenAI adapter (`providers/registry.llm_adapter`), live tests of hosted Jev, login before any hosting, and a richer `--full` rebuild of the knowledge graph.

The dated notes below are the build history, oldest first. Where a later note contradicts an earlier one, the later one wins.

## Phases

- [x] Phase 0: Repository and agent setup
- [x] Phase 1: Scaffold the frontend and backend
- [x] Phase 2: Local configuration and MongoDB connectivity
- [x] Phase 3: Domain schemas and taxonomy
- [x] Phase 4: Ticket CRUD and sequential IDs
- [x] Phase 5: Frontend shell and design system
- [x] Phase 6: Ticket screens
- [x] Phase 7: CSV template, import, and export
- [x] Phase 8: Provider adapter contracts and mock mode
- [~] Phase 9: Jev integration (local AutoTrust JEV done; hosted TypeSafe Jev deferred)
- [~] Phase 10: GPT integration (local Ollama LLM done; OpenAI deferred)
- [x] Phase 11: Execution history and cost logging
- [x] Phase 12: Comparison workflow
- [x] Phase 13: Bulk processing
- [x] Phase 14: Evaluation dataset and analytics
- [x] Phase 15: Settings page
- [x] Phase 16: Testing, reliability, and security review
- [x] Phase 17: Local release and documentation
- [x] Phase 18: Deployment readiness (documents and safety checks; nothing deployed)

## Dataset note (resolved in Phase 14)

`sample_tickets_100.csv` is kept exactly as supplied and must not be used for evaluation: every title equals its expected subcategory, which leaks the answer, and about 30 rows were not in English. Use `sample_tickets_100_v2.csv`, which has the same labels, realistic titles and English text.

## Assumptions and spec gaps

- `evaluation_labels` is required by `data-model.md` but missing from the list in `architecture.md` section 8. It is included.
- `Running` is used in `architecture.md` but missing from the status list in `requirements.md`. It is treated as an in-progress status.
- `BULK_CONCURRENCY` and `JEV_ESCALATION_THRESHOLD` appear in both env and settings. Env seeds the default; `app_settings` overrides it.
- `final_classification` is populated in the `data-model.md` example, but its notes say null until selected. The notes are followed.
- Spec and status docs live in `.context/` at the owner's request; `README.md`, `AGENTS.md` and `CLAUDE.md` stay in the root. The layout in `implementation.md` is updated to match, and its root `docs/` folder is dropped.
- Bare file names inside `.context/` refer to files in that same folder. Phase 7's template download reads `.context/sample_tickets_template.csv`.
- `.env.example` lives at `backend/.env.example` (Phase 1 layout), not the repository root.
- Playwright is the tool for Phase 16 end-to-end tests. The UI-testing setup was added on 2026-11-07, outside the phase order and at the owner's request. Phase 16 tests go in `e2e/tests/` (see `e2e/README.md`), not in `frontend/`.
- Scope confirmed (2026-11-07): one phase at a time, with a review after each. The agent never stages or commits; the owner reviews changes in Source Control, then commits and pushes.
- Language is English only (owner decision, 2026-11-07).
- Considered and withdrawn (2026-11-07): an external dataset (ABCD), RAG over labelled examples, and Google OKF. The owner chose to keep the original spec.

## Phase 1 notes

**Tests run:** backend `pytest` (2 passed) and `ruff`; frontend `eslint`, `prettier --check`, `tsc` and `vite build`. Both servers were started with no `.env` and MongoDB not running: `/docs` and the frontend returned 200 and both bound to loopback only.

**Choices:**
- TypeScript is 6.0.x, not the template's 7.0.2. `typescript-eslint` 8.72 supports only versions below 6.1. Revisit when it supports 7.
- The system font stack replaces shadcn's default Geist font, as `design.md` asks.
- `react-refresh/only-export-components` is off for `src/components/ui` only, because shadcn exports variants beside components.
- The OpenAI SDK is added in Phase 10, when it is first used. (Phase 10 is now deferred by owner decision, so the SDK is not installed.)

**Dependency review (2026-11-04):**
- `pip-audit` on `backend/requirements.txt`: no known vulnerabilities.
- `npm audit --omit=dev`: 0 vulnerabilities in production dependencies.
- `npm audit`, all dependencies: 15 (2 low, 13 moderate), from `minimatch` (ESLint, typescript-eslint and ts-morph chains) and `deepmerge` (shadcn CLI). Accepted: dev tools only, not in the browser bundle, no untrusted input. npm's only fixes are downgrades to older majors.
- `cn` was added by shadcn and replaces `clsx` + `tailwind-merge`. It is MIT-licensed, published by shadcn from `shadcn-ui/cn`, used in shadcn's own install docs, and has no install script. A string scan found no network, env or exec use.

**Known warning:** pytest reports `StarletteDeprecationWarning` about `httpx` in `starlette.testclient`. It is harmless today; check it when upgrading FastAPI.

## Phase 2 notes (2026-11-07)

**Files** (stage these together to commit Phase 2 on its own):
`backend/app/core/settings.py`, `backend/app/repositories/database.py`, `backend/app/api/health.py`,
`backend/app/main.py`, `backend/scripts/init_db.py`, `backend/tests/conftest.py`,
`backend/tests/test_settings.py`, `backend/tests/test_health.py`, `backend/tests/test_indexes.py`, `README.md`,
`.context/PROGRESS.md`.

**Tests run:** `pytest` 17 passed (settings defaults, env override, empty values, secret masking, range checks,
`.env.example` completeness, health, readiness up/down with no URI leak, indexes created and rerunnable,
`init_db` repeatable and clear when MongoDB is down); `ruff check` and `ruff format --check` clean.
**Live check:** `init_db` ran twice on `ticketlens`; `/api/health` 200; `/api/health/ready` 200, then 503 with
MongoDB stopped, then 200 after restart; `/docs` 200; API and MongoDB bound to `127.0.0.1` only.

**Choices:**
- API keys are optional so the app starts without them (spec); provider calls will fail with "not configured".
- Unknown keys in `backend/.env` are rejected at startup to catch misspelt variable names; empty values count as unset.
- The MongoDB client lives in `app/repositories/database.py` (the data-access layer), not `core/`, per `code-size-standards.md`.
- Synchronous PyMongo with a 2-second server-selection timeout; indexes are also created at startup.
- Tests use a throwaway `ticketlens_test` database and skip their database parts if MongoDB is not running.

**Note:** the owner's `demo` database was dropped from MongoDB Compass at 12:06 (mongod log, `conn16`, app
"MongoDB Compass"), not by TicketLens. Nothing here touches databases other than `ticketlens` and `ticketlens_test`.

## Phase 3 notes (2026-11-07)

**Files** (stage these together to commit Phase 3 on its own):
`backend/app/core/taxonomy.py`, `backend/app/schemas/classification.py`, `backend/app/schemas/tickets.py`,
`backend/app/schemas/executions.py`, `backend/app/schemas/comparisons.py`, `backend/app/schemas/imports.py`,
`backend/app/schemas/bulk_jobs.py`, `backend/app/api/taxonomy.py`, `backend/app/main.py` (router line),
`backend/tests/test_taxonomy.py`, `backend/tests/test_schemas.py`, `.context/PROGRESS.md`.

**Tests run:** `pytest` 90 passed (exact spec taxonomy, 36 unique subcategories, every enum's values, all 36
valid pairs, 5 invalid pairs, classification and ticket validation, taxonomy version on final classifications
and executions, bulk selection rule); `ruff` clean. **Live check:** `GET /api/taxonomy` returns version 1.0,
6 categories, 36 subcategories.

**Choices:**
- Canonical values live once, in `app/core/taxonomy.py`. The frontend reads `GET /api/taxonomy` instead of copying them, which meets "frontend and backend use the same values" without duplication.
- Pair matching is exact (case-sensitive). Invalid pairs are rejected, never rewritten.
- Ticket descriptions are kept exactly as typed; title, names and email are trimmed; email is lowercased and format-checked only.
- Costs use `Decimal`, not integer micro-units as the plan said: a Jev call can cost a few millionths of a dollar, which micro-units would round to zero or one.
- `Running` is included as an execution status (see assumptions).

## Phase 4 notes (2026-11-07)

**Files** (stage these together to commit Phase 4 on its own):
`backend/app/core/clock.py`, `backend/app/repositories/tickets.py`, `backend/app/services/tickets.py`,
`backend/app/api/deps.py`, `backend/app/api/tickets.py`, `backend/app/schemas/tickets.py` (update, note and page
schemas), `backend/app/main.py` (tickets router and database-down handler), `backend/tests/test_tickets.py`,
`.context/PROGRESS.md`.

**Endpoints:** `POST /api/tickets`, `GET /api/tickets` (search `q`, filters `category`/`priority`/`status`, `sort`
`created_at`|`priority`, `order`, `page`, `page_size` up to 100), `GET`/`PATCH`/`DELETE /api/tickets/{id}`,
`POST /api/tickets/{id}/notes`, `PUT /api/tickets/{id}/final-classification`.

**Tests run:** `pytest` 119 passed (sequential IDs, 40 concurrent allocations unique and contiguous, create/read/404,
validation, exact description text, partial update and null handling, notes, manual classification with version,
invalid pair rejected, search on each of the 5 fields, regex input treated as text, three filters, both sorts,
pagination bounds, cascade delete keeps other tickets' records, repeated delete, a failed dependent delete keeps
the ticket and a retry completes, 503 when MongoDB is down); `ruff` clean; frontend lint and build unchanged and passing.
**Live check** (against `ticketlens_test`, then dropped): IDs SK-1001/SK-1002, classify 200, bad pair 422,
search, priority sort, delete 204 twice then 404. The real `ticketlens` database has no tickets and no counter yet.

**Choices:**
- Manual final-classification editing is added now (requirements.md section 8) so category and priority filters work; selecting an AI result as final comes in Phase 12.
- IDs come from an atomic `$inc` counter; numbers are never reused, and a failed insert may leave a gap.
- Priority sort ranks Critical to Low; unclassified tickets come last in both directions.
- Search is case-insensitive substring matching with the input escaped, so it can never act as a regular expression.
- Delete removes comparisons, AI runs and labels first, then the ticket. It returns 204 even if the ticket is already gone, which makes repeats safe; a failure returns 500 and keeps the ticket.
- Times are cut to milliseconds (`core/clock.py`), the precision MongoDB stores.
- Simple reads, search and delete go straight from the API to the repository; the service layer holds only real logic (building documents, updates, notes, classification).

## Phase 5 notes (2026-11-07)

**Files:** `frontend/src/main.tsx`, `frontend/src/app/AppShell.tsx`, `frontend/src/app/router.tsx`,
`frontend/src/app/PlaceholderPage.tsx` (replaces `src/app/App.tsx`), `frontend/src/components/states.tsx`,
`frontend/src/components/ConfirmDialog.tsx`, `frontend/src/components/ui/` (shadcn: alert-dialog, badge, card,
input, label, select, sheet, sonner, table, textarea), `frontend/src/services/api.ts`,
`frontend/src/services/queries.ts`, `frontend/src/types/api.ts`, `frontend/package.json` and `package-lock.json`
(`sonner`, `next-themes`), `backend/app/api/providers.py`, `backend/app/main.py` (CORS and providers router),
`backend/tests/test_shell_support.py`.

**Built:** sidebar (Overview, Tickets, Comparisons, AI Executions, Settings), header with page title, global
search, New Ticket, and Jev/GPT "Configured / Not configured" badges (booleans only); every design.md route;
light/dark toggle remembered in the browser, light by default; drawer navigation below the `md` breakpoint;
skip link; shared loading, error, empty and confirm components and toasts; one API client; TanStack Query.
Pages from later phases show an honest "Not built yet" state, never fake data.

**Checks:** lint and production build pass; all routes serve the app; CORS allows only `http://localhost:5173`
(backend tests); provider status never contains key values.
**Not verified:** no browser is available to the agent (only Safari, without automation enabled), so the pages
have not been rendered and looked at in light and dark, which the ponytail tailoring requires. No frontend unit
tests yet: a test runner (Vitest) is a new dependency planned for approval in Phase 16.

**Dependency review:** `sonner` 2.0.8 and `next-themes` 0.4.6 (added by shadcn): MIT, no dependencies, no install
scripts, no network calls (scan matched only SVG namespace strings and a code comment).

## Phase 6 notes (2026-11-07)

**Files:** `frontend/src/features/tickets/` (`hooks.ts`, `TicketForm.tsx`, `TicketListPage.tsx`,
`NewTicketPage.tsx`, `TicketDetailPage.tsx`), `frontend/src/lib/format.ts`, `frontend/src/app/router.tsx`.

**Built:** ticket list with search, category/priority/status filters and sort kept in the URL, pagination, empty
and no-match states; create form (React Hook Form + Zod mirroring the backend rules) showing the new ticket ID;
detail page with exact description text, status select, edit form, notes, final-classification panel, and delete
behind a confirmation. Changes appear only after the API confirms them (no optimistic updates).

**Checks:** lint (complexity 10) and build pass. Live API check through the browser origin: create, validation
error, delete.
**Not verified:** not clicked through in a real browser (see Phase 5).

## Phase 7 notes (2026-11-07)

**Files:** `backend/app/services/csv_import.py`, `backend/app/services/csv_export.py`, `backend/app/api/imports.py`,
`backend/app/repositories/labels.py`, `backend/app/repositories/database.py` (`find_all`),
`backend/app/repositories/tickets.py` (`fingerprint_exists`), `backend/app/services/tickets.py` (source and sample
flag), `backend/app/schemas/imports.py`, `backend/tests/test_csv.py`, `frontend/src/features/tickets/ImportExport.tsx`,
`frontend/src/components/ui/dialog.tsx`, plus small additions to `hooks.ts`, `TicketListPage.tsx`, `types/api.ts`,
`services/api.ts`.

**Built:** `GET /api/imports/template`; `POST /api/imports/tickets` (CSV body, `dry_run` to check without saving);
`GET /api/exports/{tickets|executions|comparisons}.csv`; an import dialog (template, check, import, counts, row
errors, preview) and export links.

**Tests run:** 139 at the time (mixed valid/invalid/duplicate file with exact counts and per-row fields, labels
stored separately, re-import skips all, dry run writes nothing, no AI runs, BOM/CRLF/multi-line cells, unreadable
and oversized files, the supplied 100-row sample is fully valid, exports valid with formula cells neutralised and
payloads left out). **Live check** on `ticketlens_test`: 100 imported with 100 labels, second import skipped 100.

**Choices:**
- The CSV is sent as the request body (`text/csv`), so no upload package (`python-multipart`) is needed.
- "Preview" is the backend's own dry run, so the browser never duplicates validation.
- Whitespace is normalised in short fields and enum values match case-insensitively; descriptions stay exact.
- Duplicates are detected by a SHA-256 fingerprint of title, description, email and order ID, within the file and against earlier imports.
- `expected_*` columns go to `evaluation_labels` (dataset `shopkart-synthetic-v1`); partly filled labels make the row invalid.
- Export cells starting with `=`, `+`, `-`, `@`, tab or CR get a leading `'` (spreadsheet formula injection).

## Phase 8 notes (2026-11-07)

**Files:** `backend/app/providers/base.py`, `backend/app/providers/mock.py`, `backend/app/providers/registry.py`,
`backend/app/core/redaction.py`, `backend/app/repositories/executions.py`, `backend/app/services/executions.py`,
`backend/app/core/settings.py` and `backend/.env.example` (`MOCK_PROVIDERS`), `backend/tests/test_providers.py`,
`README.md`.

**Built:** one adapter contract (`classify(ProviderInput) -> ProviderResult`); `build_input` passes only title,
description, order, product, channel and the taxonomy (never labels, notes, the final classification or contact
details); `ProviderFailure` kinds with the HTTP mapping from ai-evaluation.md section 12 (only 429 and 5xx are
retryable); recursive redaction of credential keys; deterministic mock Jev (no free text) and mock GPT, with
`[mock-fail]`, `[mock-timeout]` and `[mock-invalid]` title markers; `services/executions.run`, which writes a
Running record first and always completes it (Succeeded, Failed, Timed Out, Invalid Response).

**Tests run:** `pytest` 163 passed; ruff clean; frontend lint and build pass.

**Choices:**
- Mocks need `MOCK_PROVIDERS=true`, are named `mock-jev`/`mock-gpt`, and report usage as unavailable (never invented).
- A missing key, or a provider not yet built, is recorded as a Failed `not_configured` attempt, not an error page.
- Unexpected adapter crashes are logged and recorded as Failed with a generic message; they never stop the other provider.
- No run endpoint yet: running from the UI arrives with Phase 12, costs with Phase 11.

## Compare workbench, brought forward from Phase 12 (2026-11-07)

The owner asked for one screen to enter or load a ticket, run Jev and GPT together, and watch both answers side
by side with live timers (layout A: ticket on top, two result columns below). Built now on the fake providers;
the same screen will show real results once Phases 9 and 10 connect the real ones.

**Files:** `backend/app/api/runs.py`, `backend/app/services/comparisons.py`, `backend/app/repositories/comparisons.py`,
`backend/app/repositories/executions.py` (`get`, `link_comparison`), `backend/app/schemas/comparisons.py`
(`ComparisonCreate`), `backend/app/providers/mock.py` and `registry.py` (fake delay), `backend/app/core/settings.py`
and `backend/.env.example` (`MOCK_DELAY_SECONDS`), `backend/app/main.py` (router),
`backend/tests/test_runs_and_comparisons.py`, `frontend/src/features/compare/` (`ComparePage.tsx`,
`ProviderColumn.tsx`, `useCompareRun.ts`), `frontend/src/types/api.ts`, `frontend/src/features/tickets/hooks.ts`
(`useTicket` can wait for an ID), `frontend/src/features/tickets/TicketDetailPage.tsx` (link to Compare),
`frontend/src/app/router.tsx` and `AppShell.tsx` (Compare in the sidebar), `README.md`.

**Endpoints:** `POST /api/tickets/{id}/runs/{jev|gpt}` (one provider; always recorded) and `POST /api/comparisons`
(saves Jev vs GPT on the five shared fields: Completed, Partial or Unavailable; links both runs; no winner).

**Tests run:** `pytest` 171 passed; ruff clean; frontend lint and build pass. **Live check** on `ticketlens_test`:
Jev and GPT ran in parallel (3.04 s wall time for 1.5 s + 3.0 s fake runs), comparison saved.

**Choices:**
- The browser sends two separate run requests at once, so each column and its timer finish independently; the backend then compares, so agreement logic exists only on the server.
- In fake mode, Jev waits `MOCK_DELAY_SECONDS` (default 1.5) and GPT twice that, so the timers visibly run; tests use 0.
- Fake results carry a "Fake AI" badge; tokens show "not reported" and cost "not calculated yet (Phase 11)".
- Design deviation: a Compare item is added to the sidebar between Tickets and Comparisons; the Comparisons history page is still Phase 12.
- Phase 12 still owns: run history on the ticket page, the comparison list/detail pages, and choosing the final classification from a run.

**Not verified:** not viewed in a browser by the agent.

## Visual check with Playwright (2026-11-07)

A one-off Playwright walkthrough (headless Chromium, script kept outside the repo) ran against the isolated e2e
stack (`:5174` / `:8001`, database `ticketlens_e2e`, mock providers), which was already running. It covered the
overview, ticket list, create form (empty-submit validation and success), ticket detail, Compare (ready, running,
done), the import dialog, the dark theme, and phone width (412×915: list, navigation drawer, Compare). 16
screenshots were viewed.

**Passed:** every step completed; Compare ran in 3.3 s with independent timers (Jev 1.50 s, GPT 3.00 s); field
agreement shown with text and icons; "Fake AI" badges; "not supported by Jev" for free text; dark theme readable
and remembered; phone layout stacks cleanly; drawer opens with all navigation. No failed requests or HTTP errors.
This closes the "not verified visually" gap for Phases 5 and 6 and the Compare page.

**Found, not yet fixed:**
1. Header badges say "Jev/GPT: Not configured" even when the fake AI is on. They should show "Fake AI" in mock mode.
2. The ticket list's "Latest AI run" column always says "Not run", even for tickets with runs. It is a placeholder until Phase 11.
3. Console warning from `next-themes` with React 19 ("Encountered a script tag while rendering React component"). Harmless; the theme works.
4. The Compare page's top card has extra empty space above the Existing/New buttons.
5. At phone width, the page title in the header is cut to a few letters ("Co…", "Ti…") by the search box.

## Local models and test-run reports (2026-11-07)

**Decision:** both sides are switchable; local models are the default until API keys exist (see requirements.md section 5).
Jev side: AutoTrust JEV `autotrust-jev:9b` through Ollama's System One endpoint. LLM side: Ollama `qwen3:8b`.
Ollama was updated from 0.40.13 to 0.40.15, because the AutoTrust model needs a newer version. The update was
checksum- and signature-verified, and the old app is kept in the scratchpad.

**Built:** `providers/definitions.py` (one set of task definitions for both sides), `providers/http.py` (shared
HTTP call, timeouts, error mapping, no automatic retries), `providers/jev.py` (System One: four `choice` questions
plus a `noul` for escalation, with the configurable threshold), `providers/ollama.py` (structured JSON output, temperature 0),
`providers/registry.py` (picks mock, local or hosted per side, plus labels for the UI), new settings (`JEV_BASE_URL`,
`LLM_BACKEND`, `OLLAMA_BASE_URL`, `OLLAMA_MODEL`), and provider status with labels. The UI shows "LLM" instead of
"GPT" and names each side's model. The internal provider key stays `gpt` for now; renaming it is a later cleanup.

**Reports:** `backend/scripts/run_report.py` writes `reports/test-runs/<run-id>.html` and `<run-id>.json` from stored
comparisons (metrics in `services/run_metrics.py`, page in `services/run_report.py`). Metrics: agreement per field
with Cohen's kappa, exact matches, latency (mean, median, 90th percentile, min, max, side-by-side wall time),
reliability, tokens and output speed, cost when priced, Jev confidence split by agreement, label distributions,
disagreements, and a per-ticket table. There is no accuracy figure without human-verified labels.

**Runs:**
- Run 1 (`2026-11-07-run-1-fake-ai`): 10 tickets (SK-1002 to SK-1011) on the fake providers, all 10 at 5 of 5 agreement. Report: https://claude.ai/artifact/DNWqG53RmPnX6oRJYrjBLG
- Run 2 (`2026-11-08-run-2-local-models`): 10 tickets (SK-1012 to SK-1021) on `autotrust-jev:9b` and `qwen3:8b`, in a visible Playwright browser at desktop size, with a phone check on the first ticket. 9 comparisons complete and 1 partial (the LLM returned a mismatched category and subcategory on SK-1020, correctly recorded as Invalid Response). Mean agreement 78%; 2 of 9 agree on all five fields; median time Jev 1.43 s, LLM 2.74 s. Report: https://claude.ai/artifact/Y2SpdhvoUaGigawnxR34st

**Found in testing:** AutoTrust allows 2-16 options per `choice` question, so the Jev adapter asks in two steps: category and the other fields first, then only that category's subcategories. Tokens from both steps are added together, and both payloads are stored.

**Dashboard, brought forward from Phases 12 and 14:** `GET /api/dashboard`, `GET /api/comparisons`, `GET /api/comparisons/{id}`; the Overview page (counts, agreement, median times, charts by field and side, latest comparisons; refreshes every 5 s), the Comparisons list and a detail page that reopens stored results side by side. Fake-AI runs are excluded from dashboard metrics and the page says how many. The ticket list's "Latest AI run" column now shows real data. Phase 14 still owns the corrected labelled dataset and accuracy scores.

**Tests run:** `pytest` 197 passed; ruff clean; frontend lint and build pass.
**Not run:** the scripted `npm --prefix e2e test` suite: its screenshot baselines predate the Compare and dashboard changes and need the owner's review before updating. No frontend unit tests yet (Vitest is still a Phase 16 decision).

**Found earlier, now fixed:** header badges said "Not configured" in fake mode (they now show each side's label).

## Phase 11 notes (2026-11-08)

**Built:** `core/pricing.py` (rates and the cost formula), a rate snapshot and estimated cost saved on every run, `GET /api/executions` (filters: side, status, ticket, UTC date range; paged) and `GET /api/executions/{id}`, the AI Executions list and detail pages, and cost on Compare and Overview. The CSV export already existed and now carries real costs. `components/ListControls.tsx` holds the filter dropdown and pager shared with the ticket list.

**Decisions:**
- Money is stored as exact decimals (`Decimal128`), not floats or integer micro-units, because a hosted Jev call can cost a few millionths of a dollar. This replaces the plan's "integer micro-units".
- Local models are priced at $0 under the version `local-no-charge`. Hosted Jev uses the published input rate of $0.042 per million tokens, with free output. OpenAI has no rate yet, so it shows as not priced; rates are never guessed. The Settings page takes over rates in Phase 15.
- Older runs are not backfilled. They show "—", and Overview says how many runs are priced.
- Date filters use UTC, and the page says so, while the table shows local time. A run close to midnight can therefore fall under the neighbouring date.

**Tests run:** `pytest` 213 passed; ruff clean; frontend lint and build pass. Visible-browser check at desktop size: one real local run on SK-1012, then the list, paging, every filter, empty and not-found states, failed-run detail, copy button, ticket list and Overview. Dark mode was looked at on the list and the failed-run detail only.
**Credential check:** no credentials in the payloads of SK-1012's 4 runs. The browser check's first failure was a false match on the page text "SK-1012StatusSuccee".
**Not run:** the scripted `npm --prefix e2e test` suite (baselines still need the owner's review). No frontend unit tests yet. Hosted Jev pricing has never been exercised by a real paid call.
**Cleanup for the owner:** the old `.gitkeep` in `frontend/src/features/executions/` is no longer needed. (Done: it was gone by 2026-11-11.)

## Phase 12 notes (2026-11-08)

**Built:** `PUT /api/tickets/{id}/final-classification` now also takes `selected_from_execution_id`. It accepts only a successful run of the same ticket (otherwise 422), and the server works out `manually_edited` by comparing the five fields with that run. `GET /api/comparisons` takes `ticket_id`. On the ticket page: Run Jev, Run LLM and Compare both buttons, the ticket's run history with each answer and a "Use this answer" button, its comparison history, and a final-answer form (`features/tickets/AiResults.tsx`, `FinalClassification.tsx`). `components/Detail.tsx` replaces two copies.

**Decisions:**
- Deviation: there is no server-side "run both" endpoint. Compare runs both sides as two separate requests and then saves the comparison, so each column finishes and its timer stops on its own. Closing the browser mid-run therefore keeps the runs but saves no comparison.
- Running one side alone creates no comparison.
- Fake-AI answers can also be chosen as the final answer; the run shows its `mock-` model name.
- There is no "clear the final answer" action; it was not required. An edit replaces it.
- Editing an answer that came from a run keeps the link to that run and marks it edited.

**Tests run:** `pytest` 219 passed; ruff clean; frontend lint and build pass. Visible-browser check at desktop size on real local models, using new synthetic tickets SK-1023 and SK-1024: single-side runs, choosing and cancelling, saving unchanged, editing, subcategory clearing, setting by hand, reload, ticket list, compare both, failed-run display, and light and dark. No failed requests.
**Not run:** the scripted `npm --prefix e2e test` suite; phone width (the owner limits responsiveness checks to the first test of a run, and this run skipped it). No frontend unit tests yet.
**Worth checking in Phase 14:** an immediate repeat of a Jev run returned in 0.10 to 0.18 s against about 1 to 1.5 s for the first run (SK-1023, SK-1021), which looks like caching in the local model server. Repeat runs on one ticket can therefore pull the dashboard's Jev times down.

## Phase 13 notes (2026-11-08)

**Built:** `jobs/bulk.py`, `repositories/bulk_jobs.py`, and `POST/GET /api/bulk-jobs` plus `GET /api/bulk-jobs/{id}`. On screen: a selection toolbar and checkboxes on the ticket list with a confirmation before anything starts, a progress banner on every page, and a Bulk Runs list and detail page.

**Decisions (the spec does not define these):**
- "Eligible" means status Open or In Progress.
- In an all-eligible run, a side that already succeeded on a ticket with the same model is recorded as Skipped, so calls are not repeated. An explicit selection always runs, because the operator asked. A fake-AI success never causes a real model to be skipped.
- Only one bulk run at a time; a second gets 409. Repeated IDs or sides in a request run once.
- Concurrency is per ticket: at most `BULK_CONCURRENCY` tickets at once, each ticket's sides one after another. A ticket run on both sides gets a comparison, including a partial one.
- On startup, unfinished jobs become Interrupted and runs left Running become Cancelled. Neither is resumed.
- Design deviation: a Bulk Runs sidebar item, so finished runs stay reachable. The banner shows active runs and runs finished within 10 minutes of the page being opened.
- Stopping the backend normally waits for a running job to finish, because the job runs as a request background task. Only a hard kill leaves it Interrupted.

**Tests run:** `pytest` 235 passed (16 new); ruff clean; frontend lint and build pass. Visible-browser check at desktop size: fake AI on the isolated test stack (selection, cancel, failure summary, navigation, all-eligible skipping, refusing a second run, a real `kill -9` mid-run with no resume, dark mode), then one real local run on SK-1023 and SK-1024 (4 of 4 succeeded). That real run adds two comparisons to Overview.
**Not run:** the scripted `npm --prefix e2e test` suite; phone width. No frontend unit tests yet. A run with `BULK_CONCURRENCY` above 2 on real models has not been tried, and a large real run has not been timed.

## Phase 14 notes (2026-11-08)

**Built:**
- `.context/sample_tickets_100_v2.csv`: same 100 rows and identical labels (a test checks this), with new titles that no longer give away the answer, 37 non-English descriptions translated, 17 product fields fixed where they contradicted the text, and order and product cleared on Account & Login tickets. The supplied file stays unchanged, and `shopkart-synthetic-v1` stays the dataset version named in the spec.
- `services/evaluation.py`, `GET /api/evaluation` and `GET /api/imports/sample-dataset`.
- An accuracy section on Overview: tiles, a chart by field, a table with every denominator, head-to-head counts and a confusion matrix.
- An accuracy section in test-run reports.

**Decisions:**
- Each side is scored on its latest finished real run per ticket. Fake-AI runs are never scored.
- Failed runs are listed but not counted as wrong, so accuracy is "of the tickets answered", and coverage is shown next to it.
- Macro-F1 appears from 30 answered tickets up.
- The confusion matrix leaves out subcategory, because 36 by 36 is unreadable.

**Run 3 (`2026-11-08-run-3-labelled-100`):** the 100 tickets on `autotrust-jev:9b` and `qwen3:8b`, in a visible browser, on the isolated `ticketlens_e2e` database, so the real dashboard is untouched. About 5 minutes; 198 of 200 attempts succeeded, and the 2 failures were the LLM pairing a subcategory with the wrong category. Report: `reports/test-runs/2026-11-08-run-3-labelled-100.html`.

| | Jev | LLM |
|---|---|---|
| All 5 fields right | 34% (34/100) | 38% (37/98) |
| Category | 89% | 86% |
| Subcategory | 84% | 81% |
| Priority | 61% | 53% |
| Sentiment | 88% | 87% |
| Escalation | 71% | 93% |

**These results are preliminary:** the labels came with the supplied dataset and no person has verified them. The owner's review (ROADMAP item E) is still open. Rows suggested for that review: 4, 11, 30, 46, 52, 64, 81, 88, 95 and 100.

**Tests run:** `pytest` passed, ruff clean, frontend lint and build pass. The labelled data has not been imported into the real database, on purpose: that is the owner's choice.

## Phase 15 notes (2026-11-08)

**Built:** `services/app_settings.py`, `repositories/app_settings.py`, `schemas/app_settings.py`, `api/app_settings.py` (`GET` and `PATCH /api/settings`; `PUT .../prompt`, `.../taxonomy`, `.../pricing`; `GET .../models/{jev|llm}`) and the Settings page. Provider adapters, the CSV importer and evaluation now read the active taxonomy, and both sides receive the saved prompt.

**Decisions:**
- Saved settings overlay the environment defaults per run, through `app_settings.effective`. Environment values remain the starting point.
- Every prompt and taxonomy change makes a new version (1.0, 1.1, and so on) with history. Each run stores its prompt text and rate snapshot, so history never changes.
- A taxonomy edit needs 2 to 16 options at each level (Jev's limit) and unique subcategories. A label used by a ticket, run or evaluation answer cannot be removed or renamed (409).
- A model name is refused if the server is reachable and does not offer it. If the server is unreachable, the operator's choice is accepted. TypeSafe's `jev-latest` alias is always allowed.
- Update requests forbid unknown fields, so API keys and connection details cannot be set through this API.
- The active taxonomy is held per process (a recorded shortcut), which fits the documented single backend process.

**Tests and check:** see Phase 16's totals. Visible-browser check on the fake-AI stack (saving, refusals, prompt history, taxonomy, prices, dark mode), plus a read-only look at the real page. The real model lists return the 3 models on the local Ollama server.
**Found and fixed from screenshots:** the model note read "0 models" while loading, and "1 models".
**Not tried:** the TypeSafe model list against the real service (no key yet; the call is tested against a fake server).

## Phase 16 notes (2026-11-08)

**Built:** bounded retries in `providers/http.py`: at most 3 attempts, with growing delays plus jitter, honouring `Retry-After` up to 10 s. Only a refused connection, 429 and 5xx are retried. Other 4xx, timeouts and broken connections never are, because the provider may already have processed and charged for the call. `e2e/tests/workflow.spec.ts` covers the journey from creating a ticket through classify, compare, choosing a final answer and export to delete, plus partial failure, form validation, filters, backend-down errors and the absence of a key field.

**Tool choice:** frontend tests use the Playwright setup already installed rather than adding Vitest, so there is no new dependency.

**Tests run:**
- `pytest`: passed, including every provider failure (401, 402, 403, 400, 404, 422, 429, 5xx, timeout, malformed response). Final total is in the completion report below.
- `npm --prefix e2e test`: 14 passed on desktop and phone, in a visible browser.
- ruff, frontend lint and build pass.

**Baselines:** the `ticket-list` screenshots were regenerated after looking at old and new. Every difference was deliberate (real provider badges, the Bulk Runs link, the toolbar and checkboxes). They are in Source Control for review.

**Security checks, observed on the running system:**
- Ports 8000, 5173, 27017 and 11434 listen on 127.0.0.1 only.
- The browser bundle has no keys or key names; `VITE_API_BASE_URL` is its only environment variable.
- Git history: 26,205 added lines scanned for key shapes. The only match is a deliberately fake password in `backend/tests/test_health.py`, aimed at a dead local port.
- `backend/.env.example` is the only env file ever committed, and `backend/.env` is ignored.
- CORS refuses another origin (HTTP 400 on preflight).
- `GET /api/settings` and all three CSV exports contain no key text.
- 82 stored runs in the real database were checked: none holds credentials or labels.
- Log calls carry only provider names and IDs.

**Fixed:** the phone header squeezing the page title to "Ti…" (the header search is now hidden on phones; Tickets has its own), and the extra space on the Compare card.
**Still open:** the harmless `next-themes` script-tag console warning with React 19. Logs were reviewed by reading the code, not by capturing a live log of a hosted call.

## Phases 17 and 18 notes (2026-11-08)

**Phase 17:** `README.md` rewritten for someone new to the project: what each AI connection needs and its real state, setup, how to use the app, troubleshooting, and a local verification checklist. Followed in a clean copy on other ports and a separate database: fresh install, health checks, fake-AI start, importing the 100 tickets (100 valid; a second import skipped all 100 as duplicates), and a frontend build.

**Phase 18:** `.context/DEPLOYMENT_DECISIONS.md` now covers settings, build and run, HTTPS and proxy, MongoDB, backup, logging, and a readiness checklist. With `APP_ENV=production`, the backend refuses to start with a database on this computer, a non-https or wildcard origin, fake AI, or without `ACCESS_CONTROL_CONFIRMED=true`. Production turns off the interactive API docs. Errors never echo settings (checked with a test password). A production frontend build with `VITE_API_BASE_URL` was verified.

**Not run:** the owner following the README (ROADMAP item F); installing MongoDB or pulling Ollama models from scratch; any real host, proxy or HTTPS. No hosting was chosen or provisioned.

## Completion report (2026-11-08)

**Done and working on local models:** ticket management, CSV import and export, side-by-side runs, comparisons, choosing a final answer, execution logs with cost, bulk runs, the labelled dataset with accuracy, Settings, reports, and deployment documents.

**Final definition of done (`implementation.md`):**
- [x] Local workflows operate end to end.
- [ ] **Both provider integrations work with real credentials. Deferred by owner decision (2026-11-11):** hosted Jev is untested with a real key, and the OpenAI adapter does not exist. The working comparison is AutoTrust JEV against an Ollama LLM.
- [x] Every provider attempt is logged with usage and estimated cost.
- [x] 100 labelled synthetic tickets are available for manual import.
- [x] Evaluation and comparison dashboards work.
- [x] Tests pass.
- [x] The local setup is documented.
- [x] Production prerequisites are documented, without pretending local MongoDB can serve a cloud backend.

**Waiting on the owner** (updated 2026-11-11):
1. ~~API keys and OpenAI model~~: paid APIs are deferred by owner decision, so nothing is needed.
2. Review the corrected dataset (rows 4, 11, 30, 46, 52, 64, 81, 88, 95, 100). The accuracy figures stay preliminary until then.
3. Follow the README once.
4. Keep the local-model settings in `backend/.env` (see the README). Without them, a backend restart falls back to the hosted-Jev default, which needs a key.
5. Deployment decisions, only if going online.

**Final checks:** `pytest` 335 passed; ruff clean; frontend lint and build pass. A real `mongodump` and `mongorestore` round trip worked on a throwaway database. The real `ticketlens` database still has no saved settings and no labels; these phases only added the runs on SK-1023 and SK-1024 described above.

**Intermittent browser test failure, cause not proven:** one run of `npm --prefix e2e test` failed 3 of 14 tests and took 3.8 minutes instead of about 32 seconds. Runs before and after it passed 14 of 14. In the failed run a page load hung for over 30 seconds, and a page's elapsed timer sat at `00:00.00`, which suggests the visible browser window itself was stalled or throttled rather than an app fault. The phone screenshot failure followed from it: the failed journey never deleted its ticket, so the list had an extra row. That also shows a weakness: the `ticket-list` baseline depends on how many rows earlier tests leave behind. If this recurs, look there first.

**Known limits:** the active taxonomy and bulk jobs assume one backend process. The harmless `next-themes` console warning remains. Phone width was not checked for the newest screens beyond the scripted phone tests. Dataset labels were not independently verified.

## Documentation sync for handover (2026-11-11)

**Owner decision:** the paid APIs (hosted TypeSafe Jev and OpenAI) are deferred, and their architecture is kept.

**What changed:**
- `architecture.md` and `data-model.md` were rewritten from the code.
- `requirements.md`, `design.md` and `ai-evaluation.md` each gained an "As built" section.
- `implementation.md` is now marked historical, and `ROADMAP.md` was updated.
- New READMEs: `backend/`, `frontend/`, `reports/` and `.context/`.
- The e2e docs, the skill tailoring blocks and memory notes were updated.
- Stale code comments and UI copy were fixed. Comments only; no behaviour changed, except that the OpenAI `not_configured` message now says "deferred".

**Evidence:**
- Live `/openapi.json`: every `/api/...` route named in the docs exists.
- A visible-browser walkthrough of every page on the fake-AI stack: the navigation and page titles match `design.md` section 13.
- A path check of the backticked file names in the docs.

**Tests run:** `pytest` 335 passed; ruff clean; frontend lint and build pass; `npm --prefix e2e test -- --headed` 14 passed.

**Seen, not fixed:** during the e2e run, React logged "two children with the same key, `1.0`". It most likely comes from the prompt history list in `SettingsPage.tsx`, which uses `key={item.version}`. That means the test database held two history entries for version 1.0; the cause was not investigated. The "script tag" console error is the known `next-themes` warning.

## Code size requirement (2026-11-07)

The owner requires a small, clean codebase without losing functionality or security. Rules, evidence and enforcement are in `code-size-standards.md`. `ponytail` is installed and always on for coding tasks. Lint limits: ruff `C90` (complexity 10) and `SIM`; ESLint `complexity: 10`.

## Skills

36 skills are installed in `.claude/skills/`: 34 from Claude_Skills commit `058b511`, plus `agent-browser` and `persona-ui-testing`, copied by hand on 2026-11-07. `_templates/` holds skill templates, not a skill. Reasons for exclusions are in the `_orchestrator` tailoring block. Project-specific notes live only in tailoring blocks.

The skill drift hook is left out because `~/Projects/Claude_Skills` has 65 untracked `SKILL (1).md` files, which make its skill hashes differ. Run `skillpack` from a clean clone, or remove those files first.
