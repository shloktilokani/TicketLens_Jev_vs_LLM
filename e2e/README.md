# UI testing

Functional and visual testing of TicketLens through its real UI, by scripted tests and by agents acting as different people. Self-contained: own `package.json`, own test copy of the app.

## The test stack

`npm --prefix e2e run stack` (from the repository root) starts an isolated copy of the app:

| | Test stack | Dev servers (untouched) |
|---|---|---|
| Frontend | http://localhost:5174 | :5173 |
| Backend | http://127.0.0.1:8001 | :8000 |
| Database | `ticketlens_e2e`, emptied on every start | `ticketlens` |
| Providers | fake AI on both sides (no cost) | as configured |

MongoDB must be running (root `README.md`, "Run locally"). `scripts/reset_db.py` refuses any database not ending in `_e2e`.

## Tools: one job each

| Tool | Job | How |
|---|---|---|
| Playwright MCP | Agent-driven persona runs (types, clicks, takes screenshots, visible browser) | `.mcp.json` → `playwright`; procedure in the `persona-ui-testing` skill |
| `@playwright/test` | Scripted regression and pixel baselines | `npm --prefix e2e test` |
| Chrome DevTools MCP | Diagnostics only: console, network, performance | `.mcp.json` → `chrome-devtools` |
| agent-browser | Fallback for long sessions where token cost matters | `npm --prefix e2e run browser -- open http://localhost:5174` |

Both MCP servers and agent-browser use Chrome for Testing from `~/.cache/chrome-for-testing/current` (a symlink to the installed version). Scripted tests use Playwright's own Chromium, so baselines come from a pinned browser build.

## Commands (from the repository root)

```bash
npm --prefix e2e test                       # starts and stops the stack itself
npm --prefix e2e run test:update-baselines  # after a deliberate UI change; look at every changed image first
npm --prefix e2e run report                 # HTML report of the last run
npm --prefix e2e run stack                  # stack only, for persona runs
```

Ask an agent for a persona run in plain words, for example: "Run TC-001 with the angry-impatient customer and the keyboard-only analyst." It follows `.claude/skills/persona-ui-testing` and writes `e2e/output/runs/<timestamp>-<TC-id>/` (manifest, screenshots, `failures.jsonl`, `report.md`).

## Scripted tests (`tests/`)

| File | What it checks |
|---|---|
| `smoke.spec.ts` | Create a ticket, find it in the list and open it; screenshot baselines of the form and the list |
| `workflow.spec.ts` | The full journey (create, run both sides, choose the final answer, export, delete); a failing side keeps the other's result; form validation; filters in the URL; backend-down errors with retry; no API-key field in Settings |

Each test runs on desktop (1280×800) and a Pixel 7 phone size: 14 tests in all. Every test shares one database (`workers: 1`). Baselines are in `tests/smoke.spec.ts-snapshots/`. The `ticket-list` baseline masks the rows, but its height still depends on how many rows earlier tests leave behind, so look there first if it fails unexpectedly.

## Demo recording (`demo/`)

A one-command screen recording of Jev vs LLM on three new tickets, for LinkedIn and the root README. Unlike the tests, it runs on the real app and creates real tickets. See `demo/README.md`.

## Writing test cases and personas

- Test cases: `test-cases/TC-NNN-slug.md`, copied from `test-cases/TEMPLATE.md`.
- Personas: `personas/customers/` (how the ticket is written) × `personas/analysts/` (how the app is used). See `personas/README.md`.

## Other provider modes

- **Paid APIs:** deferred by owner decision (2026-11-11). `stack.sh` refuses `E2E_PROVIDERS=real`. If paid runs ever return, add a small loopback proxy in front of the backend that counts paid requests and returns 429 after a cap (for example 10 tickets), so the limit holds even if an agent loops.
- **Local models, no cost:** `stack.sh` has no switch for them. Start the isolated backend yourself on port 8001, using `MONGODB_DATABASE=ticketlens_e2e`, `MOCK_PROVIDERS=false`, the local-model variables from the root README and `FRONTEND_ORIGIN=http://localhost:5174`. Then start the frontend with `VITE_API_BASE_URL=http://127.0.0.1:8001`. Run 3 in `reports/test-runs/` was made this way.

## Tool audit

Data-risk audit of every tool here: `../dependency_risk_audits/2026-11-07_ui-testing-tools/`. In short: chrome-devtools-mcp sends usage statistics and CrUX lookups to Google by default, and both are turned off in `.mcp.json`. agent-browser's Chrome version check is turned off with `AGENT_BROWSER_NO_VERSION_CHECK=1`. Never set `AI_GATEWAY_API_KEY` or cloud-browser keys for agent-browser.
