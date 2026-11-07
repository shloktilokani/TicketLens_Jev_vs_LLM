# Progress

Build order and acceptance criteria: `implementation.md`. Update this file after every phase.

## Status

Phases 0 to 8 are complete. Phases 5 and 6 still need the owner's visual check in a browser (see Phase 5 notes). **Next: Phase 9** (real Jev), which needs the Jev API key for live calls.

Plain-language phase order and every step that needs the owner: `ROADMAP.md`.

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
- [ ] Phase 9: Jev integration
- [ ] Phase 10: GPT integration
- [ ] Phase 11: Execution history and cost logging
- [ ] Phase 12: Comparison workflow
- [ ] Phase 13: Bulk processing
- [ ] Phase 14: Evaluation dataset and analytics
- [ ] Phase 15: Settings page
- [ ] Phase 16: Testing, reliability, and security review
- [ ] Phase 17: Local release and documentation
- [ ] Phase 18: Deployment readiness

## Blockers

- **Phase 2:** none. MongoDB 9.0.4 is installed by the owner; starting it is delegated to the agent (loopback only).
- **Phases 9 and 10, real calls only:** `TYPESAFE_API_KEY` and `OPENAI_API_KEY` go in `backend/.env`. Mock mode covers development until then.
- **Phase 10:** `OPENAI_MODEL` has no default in `.env.example` and must be chosen.

## Required fix before any paid evaluation (Phase 14)

`sample_tickets_100.csv` is kept exactly as supplied, but it must not be used for evaluation yet:

- In all 100 rows, `title` is identical to `expected_subcategory`. Titles are sent to both providers, so this leaks a ground-truth label and breaks the rule in `AGENTS.md`.
- About 30 rows are romanised Hindi or Hinglish. The spec is now English only, so these rows are rewritten in English.

Create a corrected English dataset in Phase 14 with realistic titles, keeping the labels and the 100-row size. The owner reviews it before any paid run.

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
- The OpenAI SDK is added in Phase 10, when it is first used.

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

**Runs:** Run 1 (`2026-11-07-run-1-fake-ai`): 10 tickets (SK-1002 to SK-1011) on the fake providers, all 10 at
5 of 5 agreement, report published as an artifact. Run 2 uses the real local models; see its report.

**Tests run:** `pytest` 189 passed; ruff clean; frontend lint and build pass.

**Found earlier, now fixed:** header badges said "Not configured" in fake mode (they now show each side's label).

## Code size requirement (2026-11-07)

The owner requires a small, clean codebase without losing functionality or security. Rules, evidence and enforcement are in `code-size-standards.md`. `ponytail` is installed and always on for coding tasks. Lint limits: ruff `C90` (complexity 10) and `SIM`; ESLint `complexity: 10`.

## Skills

34 skills are installed in `.claude/skills/` from Claude_Skills commit `058b511`. Reasons for exclusions are in the `_orchestrator` tailoring block. Project-specific notes live only in tailoring blocks.

The skill drift hook is left out because `~/Projects/Claude_Skills` has 65 untracked `SKILL (1).md` files, which make its skill hashes differ. Run `skillpack` from a clean clone, or remove those files first.
