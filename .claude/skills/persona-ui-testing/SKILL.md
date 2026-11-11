---
name: persona-ui-testing
description: "SOP for testing a user-facing app, especially conversational UIs, through its real UI with simulated personas, screenshots, payload checks, and human review. Use for persona or exploratory UI test runs."
metadata:
  title: "Persona-Driven UI Testing"
  category: "Quality"
  tier: practice
  trigger_keywords: "persona testing, simulated user testing, test the chatbot ui, ui testing cycle, test with personas, exploratory ui test run, re-run the ui tests, verify the fix in the ui, playwright mcp session"
---

## Role Identity

A procedure, not a technical reference. It glues together: the persona library in `personas/` (what to ask and in whose voice), the mechanics in `references/ui-automation-mechanics.md` (selectors, waits, credentials), the browser tool (`playwright` or `agent-browser`), and the triage skills (`qa-test-engineer`, `testing-strategy`). Its purpose is to find what real, varied users would hit — confusing answers, misleading renders, broken flows — by exercising the **actual rendered UI**, not the API behind it.

## Responsibilities

### Standing rules (apply to every session, including a one-question ad-hoc check)

- **Keep this SOP current.** If a step doesn't match reality (a selector changed, a login screen differs, a wait is flaky), fix the SOP — or the project's tailoring notes for it — in the same session, dated. Anything you had to improvise is unfinished until it's written down here. The bar is a smooth next run.
- **Screenshot every meaningful interaction and save it** to the run folder — no "too small to bother" exception. Saving is mandatory; reading every image back is not (that's the expensive part — see Step 5).
- **Every session gets a run folder**, even a single ad-hoc check.
- **An API call is never a substitute for the UI pass.** Hitting the backend directly is a good fast sanity check for backend logic, but a fix is not verified until it has been exercised through the real UI (log in → open the feature → enter the real input → observe the rendered result → screenshot). Most user-visible bugs live in the rendering path an API call never touches.
- **Prefer direct tool calls over writing a bespoke test-runner script for this workflow**, unless the project has deliberately chosen a maintained harness — then use the harness and treat this SOP as its operating procedure.
- **Replay before re-asking.** If the goal is to look again at a specific past request (by run/request ID), use a replay/debug view if the project has one instead of re-running the flow — cheaper, and it shows exactly what happened then.

### Step 1 — Start the services

- Launch long-running services (backend, frontend dev server) through the harness's own background-process mechanism (e.g. the Bash tool's `run_in_background`), not a shell-level `nohup … &` inside a foreground call — shell-backgrounded children can be reaped when the calling session ends, and they then die silently.
- **Confirm each service is up by polling it**, not by waiting a fixed delay.
- **Verify port ownership by process command line, not by port number.** Another tool (an IDE extension, a stale dev server) may already be listening on the expected port; navigating there then shows the wrong app.
- **After stopping or restarting a service, check for orphaned children.** Reloaders and wrapper processes (auto-reload servers, build-tool wrappers around dev servers) often spawn a child that holds the socket and survives its parent — it keeps serving **old code**, silently. Before trusting any live result after a restart: list processes with their command lines, kill orphans whose parent is gone, and confirm the *current* process's own log shows your request arriving.

### Step 2 — Launch the automation browser

If the browser tool connects to an existing browser (e.g. over a CDP debug port), start that browser first — the tool usually can't launch it. When the cycle ends, **stop that browser process explicitly**; closing the tool session doesn't.

### Step 3 — Log in and open the feature

- Adapt to whichever login screen actually renders (dev stub vs SSO vs real form) — don't hard-code one.
- Use a **dedicated, low-privilege test account**, never a real person's identity. Handle credentials per `references/ui-automation-mechanics.md` (no plaintext, tracing off during login, masked screenshots).
- Elements without ARIA roles may be invisible to accessibility-tree snapshots — target them by stable CSS selector, and use snapshots only for the surrounding page.
- Screenshot to confirm the feature opened before starting.

### Step 4 — Generate this run's inputs (no browser involved)

- **Generate fresh inputs every run** — don't replay a fixed bank (reuse a specific input only to re-confirm one exact prior failure). The requester specifies the persona mix, count per persona, and any focus (e.g. "weight toward today's fixes").
- Load each chosen persona from `personas/` and write inputs in that persona's voice, grounded in the product's real data and capabilities.
- **Cover categories as a separate axis from personas.** If the project has a taxonomy of real input types with measured failure rates (built from production logs), spread the run across categories rather than letting persona voice alone choose topics. Refresh the taxonomy's numbers periodically.
  - Beware metric blind spots: a hard-failure rate that excludes soft outcomes (clarification requests, polite refusals) cannot detect a bug that manifests as a soft outcome. A fix's effect may be invisible to that metric and visible only in a live re-test.
- **Reserve ~20–25% of slots as wildcards generated by fresh, isolated sub-agents** — one per slot, given only the product's purpose and a persona's voice, and **not** the category taxonomy or the other planned inputs. The independence must be architectural (a separate context), not "try to be creative." Tag them `origin: wildcard`. After the run, check whether any wildcard doesn't fit the taxonomy — if so, propose it as a new category.
- Write the plan (persona → inputs, in send order) as the run manifest before sending anything.

### Step 5 — Execute, one input at a time

- **Never send the next input while one is in flight** (unless deliberately testing concurrency — below). Local latency can be long; overlapping requests corrupt which response belongs to which input.
- Per input: type it → submit (if a click times out, don't block — fall back to pressing Enter or a scripted `.click()`, then confirm the send registered via the backend's log or run record) → wait using the layered strategy in the mechanics reference → **screenshot to the run folder** → record the run/request ID.
- **Confirm outcomes from structured records** (run tables, JSONL request logs — which often include intermediate artefacts like generated queries) rather than reading every screenshot back; fall back to file logs if database access is flaky.
- **On failure**: don't silently retry. Append one JSON line to `failures.jsonl` (input id, persona, input text, timestamp, error shown, run ID if any) and save the screenshot with a `_FAILED` suffix.
- **If the UI supports queueing or concurrent submissions**, include one deliberate test per run: submit A, immediately submit B, screenshot B's pending state, then verify from backend timestamps that A finished before B started and that each answer rendered under its own input.
- **Payload-level compliance checks**: for every response, check the rendered-output rules the project defines (e.g. `data-presentation-standards` — no dual axes, labels carry units, no fabricated comparisons, correct table sub-format) against the recorded payload, and where a rule is only visible in the rendered DOM (label text, units), inspect the live DOM/chart objects via the browser tool's evaluate function. Log violations separately from hard errors: a response can be data-correct *and* format-non-compliant — report both.

### Step 5a — Run folder

Create it **before** the first screenshot (some screenshot tools refuse paths under a missing folder): `ui-testing/<env>/<YYYYMMDD_HHMMSS>/` (or the project's established equivalent). `<env>` names the real target — don't label local services as `uat`/`prod`. Screenshots and logs may contain real business data: keep run folders git-ignored and don't copy artefacts elsewhere in the repo.

### Step 6 — Post-run analysis

1. Read back `failures.jsonl` and the manifest.
2. **Human-eyes visual review (mandatory every run)** — a separate pass from Step 5's payload checks, which catches a different class of defect. Open every saved screenshot and read every number, label, axis, and legend: truncated or overlapping text, inconsistent precision within one response, units present in one place and missing in another. While the browser is still open, cross-check live DOM/chart state for what a static image can't show (tooltip-only content, true series values, label text vs configured format). Ask of each: *"Seeing only this, would a real user read it correctly?"*
3. Triage everything — hard errors, compliance violations, and visual findings together — with `qa-test-engineer` and `testing-strategy`: regression vs known limitation vs persona-specific edge case, with severity.
4. Optionally, for a deeper challenge, run `system-analysis-testing-expert` on the pattern of failures.
5. Write `report.md` in the run folder: persona × input × outcome × severity, plus a short recommended-fixes list.

### Step 7 — Iterate

Run → fix the highest-priority findings (through the project's normal skills and conventions) → re-run with **freshly generated** inputs → keep every run folder, so trends across cycles are visible.

## Technical Skill Set

Browser automation via MCP/CLI tools (Playwright MCP, `agent-browser`) or a maintained Playwright/Selenium harness; process inspection on the host OS (`Get-CimInstance Win32_Process` / `ps -ef`, `netstat -ano` / `ss -ltnp`); structured run logs; DOM and chart-object inspection via in-page evaluation; JSONL result logging; CTRF/JUnit result formats when integrating with dashboards; sub-agent spawning for isolated wildcard generation.

**Quick runbook — recurring environment incidents**

| Symptom | Likely cause | Mitigation | Verify |
|---|---|---|---|
| Live checks keep showing pre-fix behaviour after a restart | Orphaned server child still serving old code | Find children whose parent PID is dead; kill them | Your request appears in the *current* process's log |
| Navigating to the app shows a different app | Another process owns the port | Identify the real server by command line; stop the squatter | Expected login screen renders |
| Every request fails "connection refused" minutes after a good start | Service started via shell `&` was reaped | Relaunch through the harness's background mechanism | Port listening; request lands in the log |
| Backend fails at startup fetching secrets | Expired local cloud credentials | Re-authenticate (e.g. application-default login) | Startup log completes |
| Clicks time out on stable-looking elements | Environment-wide actionability flakiness | Fall back to Enter / scripted click | Confirm via URL, new DOM node, or backend log — not the click's own success |

## Decision-Making Lens

Optimises for **finding what a real user would experience**, so the rendered UI and a human reading of it are the final authority — above API responses, above payload checks, above a green log. Cheaper checks are used to go fast, never to declare done.

## Trigger Signals

- **Keywords**: test the UI, persona testing, simulated users, run a testing cycle, re-run the tests, verify the fix in the app, check how it renders.
- **File/path signals**: UI-testing run folders, persona files, browser-tool configuration (`.mcp.json` with a Playwright server), frontend widget code.
- **Project-context signals**: a user-facing app — particularly a chat or natural-language interface — with a local dev setup; any use of browser-automation tools in the project (this SOP's screenshot and run-folder rules apply to *all* such use).

## Collaboration Behavior

- **Delegates mechanics** to `playwright` / `agent-browser` and `references/ui-automation-mechanics.md`.
- **Hands findings** to `qa-test-engineer` and `testing-strategy` for triage, and optionally `system-analysis-testing-expert`.
- **Checks the rules of** `data-presentation-standards` (or the project's equivalent) on real output.
- **Serves** `llm-model-evaluation` (the real-UI passes) and `core-logic-change-visualizer` (evidence for before/after records).
- **Sibling of `test-automation-engineer`**, which owns general-purpose end-to-end automation across target types; this skill is the persona-driven exploratory procedure specifically.

## Output Style / Conventions

- Run folder contents: manifest, screenshots (`qNN_<slug>.png`, `_FAILED` suffix on failures), `failures.jsonl`, optional `formatting_violations.jsonl`, `report.md`.
- Reports distinguish hard errors, compliance violations, and visual findings — none averaged into another.
- Every finding cites a run/request ID.

## Anti-Patterns

- Declaring a fix verified from an API call alone.
- Skipping screenshots on "quick" checks.
- Sending overlapping inputs unintentionally.
- Replaying the same input set to "confirm" fixes.
- Trusting a restart without checking for orphaned processes.
- Generating wildcards in the same context that holds the taxonomy.
- Leaving the automation browser running after the cycle.
- Using a real employee's identity for automated login.

## Stack Detection & Adaptation

Identify the app's services and how each is started locally, the ports they use, the login flow(s), the browser tool configured in the project, where request/run logs are written, whether a replay/debug view exists, and whether a real-input taxonomy exists. Record project-specific values (commands, ports, selectors, login steps, known gotchas) in a clearly marked project-tailoring section of this skill or in the project's memory notes — keep this file's procedure generic.

## Files

| Path | Contents |
|---|---|
| `personas/*.md` | Ten reusable personas (voice, concerns, input-generation guidance) |
| `references/ui-automation-mechanics.md` | Selector discovery, layered wait strategy, response-type awareness, output conventions, credential handling |

<!-- project-tailoring:begin -->
## Project tailoring

TicketLens: local single-user app, no login. Everything lives in `e2e/` (start with `e2e/README.md`).

**Stack.** Start it with `npm --prefix e2e run stack` through Bash `run_in_background`. Wait for http://localhost:5174 to respond. The frontend is on :5174, the backend on 127.0.0.1:8001, the database is `ticketlens_e2e` (emptied on every start), and providers are mocked. Never test against the dev servers (5173, 8000) or the `ticketlens` database; they hold the owner's real data. Stop the stack when the run ends, and check that nothing is still listening on 5174 or 8001.

**Which tool does what** (one job each, so runs stay comparable):
- Playwright MCP (`playwright` in `.mcp.json`): the default for persona runs. Visible browser, isolated profile. Locators come from `browser_snapshot` refs, passed as `target`.
- `@playwright/test` (`npm --prefix e2e test`): scripted regression and pixel baselines. Turn a persona finding worth keeping into a spec in `e2e/tests/`.
- Chrome DevTools MCP (`chrome-devtools`): diagnostics only (console errors, network requests, performance traces). Never use it to drive a test.
- agent-browser (`npm --prefix e2e run browser -- <command>`): a fallback for long sessions where token cost matters. Run `npm --prefix e2e run browser -- skills get core` first.

**Personas: two axes.** Pair one `e2e/personas/customers/*` voice (writes the ticket text) with one `e2e/personas/analysts/*` behaviour (operates the UI). Each run, the customer persona rephrases the test case's ticket intent in its voice with the same intent, as fresh text. Record the exact text typed in the manifest. These persona files replace the generic library in `personas/` for this project.

**Test cases.** These are `e2e/test-cases/TC-*.md` (format in `TEMPLATE.md`). Expected labels in a test case are for checking results only. Never type them, or hints toward them, into the app.

**Modes.**
- Mock is the default: free and repeatable.
- Local models (no cost) are possible by starting the isolated backend with the local-model settings; see `e2e/README.md`, "Other provider modes".
- Paid modes (hosted Jev, OpenAI) are deferred by owner decision (2026-11-11), and `stack.sh` refuses them. If they return, run them only when the owner asks by name, at most 10 tickets per run, ending with a cost summary from the AI Executions log.

**Run folders.** Use `e2e/output/runs/<YYYYMMDD_HHMMSS>-<TC-id>/` (git-ignored), containing `manifest.md`, the screenshots, `failures.jsonl` and `report.md`. Playwright MCP's own snapshots and console logs land in `e2e/output/mcp/`.

**Known gotchas (2026-11-07).** In `@playwright/mcp` 0.0.84 the element argument is `target`, not `ref`. In chrome-devtools-mcp 1.12.0, `list_console_messages` and `list_network_requests` need the `pageId` from `list_pages` or `new_page`. Radix Select is a `combobox`: click it, then pick the `option` by name.
<!-- project-tailoring:end -->
