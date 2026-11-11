# Setup and use

How to set up, run, use and check TicketLens, and what to do when something breaks. The overview of what the repository is for is in [README.md](README.md).

## What each AI connection needs

| Side | Option | What it needs | State |
|---|---|---|---|
| Jev | AutoTrust JEV, an open model run locally by Ollama | Ollama | Working, tested on 100 tickets |
| Jev | TypeSafe's hosted Jev | `TYPESAFE_API_KEY` | Built but never run with a real key; **deferred** (paid) |
| LLM | A local model through Ollama, such as `qwen3:8b` | Ollama | Working, tested on 100 tickets |
| LLM | OpenAI | `OPENAI_API_KEY` | **Not built; deferred** (paid) |
| Both | Fake AI (`MOCK_PROVIDERS=true`) | Nothing | Working. No cost, results labelled `mock-*`, never scored |

AutoTrust JEV is an open model, not TypeSafe's hosted Jev. Jev returns typed decisions only, so summary and suggested resolution are marked unsupported on that side.

**Paid APIs are deferred by owner decision (2026-11-11).** The supported setup is local models. The architecture for hosted Jev and OpenAI is kept, so either can be added later; see `.context/architecture.md`, section 4.

In the code and API, the LLM side's internal key is `gpt`, a name kept from the original plan; the UI calls it "LLM".

## Run it locally

You need Python 3.13, Node 22.12 or newer, and MongoDB Community Edition. Docker is not used. Run the commands below from the repository root unless a step says otherwise.

**Quick start on a Mac:** once MongoDB and Ollama are installed (and the setup in steps 2 to 4 has been done once), double-click `start-ticketlens.command`. It starts MongoDB, Ollama, the backend and the frontend, skips any that are already running, and opens http://localhost:5173 in your default browser. Closing its Terminal window stops the backend and frontend it started; MongoDB and Ollama keep running. If `backend/.env` sets no AI, it uses the local models. Logs are in `~/Library/Logs/TicketLens/`. The steps below do the same thing by hand.

### 1. Start MongoDB

Install it using the [official guide for your system](https://www.mongodb.com/docs/manual/administration/install-community/), then start it on this computer only. Create the data folder first, and do not use `sudo`, or later starts as your user will fail:

```bash
mkdir -p ~/data/db
nohup mongod --dbpath ~/data/db --bind_ip 127.0.0.1 --port 27017 --logpath ~/data/mongod.log --logappend >/dev/null 2>&1 &
mongosh --quiet --eval 'db.runCommand({ ping: 1 })'   # expect { ok: 1 }
```

If `mongod` is not on your `PATH`, use its full path. If you installed MongoDB as a system service, start the service instead. To stop it: `mongosh admin --quiet --eval 'db.shutdownServer()'`.

Never expose MongoDB to the internet.

### 2. Configure the backend

```bash
cp backend/.env.example backend/.env
```

Then choose one of these in `backend/.env`.

**Local models, no keys or cost.** Install [Ollama](https://ollama.com/download) 0.40.15 or newer, run `ollama pull autotrust-jev:9b` and `ollama pull qwen3:8b`, and set:

```bash
JEV_BASE_URL=http://127.0.0.1:11434
JEV_MODEL=autotrust-jev:9b
LLM_BACKEND=ollama
OLLAMA_MODEL=qwen3:8b
PROVIDER_TIMEOUT_SECONDS=300
```

**Fake AI, to try the app with no models.** Set `MOCK_PROVIDERS=true`.

**Hosted Jev (deferred, paid).** Not part of the current scope. If it is ever wanted: get a key from [TypeSafe](https://www.typesafe.ai), set `TYPESAFE_API_KEY`, and leave `JEV_BASE_URL` and `JEV_MODEL` at their defaults. Every hosted call costs money.

API keys belong only in `backend/.env`, which git ignores. Never put a key in frontend code or a `VITE_` variable. The app never shows keys and has no way to change them.

### 3. Start the backend

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The backend creates its database indexes when it starts. Check it at:

- http://127.0.0.1:8000/api/health: the process is up.
- http://127.0.0.1:8000/api/health/ready: MongoDB is reachable.
- http://127.0.0.1:8000/docs: the API documentation.

### 4. Start the frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. The header badges show which AI each side is using.

The frontend calls the backend at `http://127.0.0.1:8000`. To change that, set `VITE_API_BASE_URL` in `frontend/.env.local`.

## Use it

1. **Add tickets.** Use New Ticket, or Import CSV on the Tickets page. Importing checks the file first, reports valid, invalid and duplicate rows separately, and never starts AI. The import dialog offers a blank template and the 100 labelled sample tickets.
2. **Run the AI.** On Compare, load a ticket and press Run Jev + LLM. On a ticket's page, run one side alone. For many tickets, tick them on the Tickets page or choose Select all eligible (Open or In Progress). You confirm before a bulk run starts, and it shows progress on every page.
3. **Choose the final answer.** On a ticket's page, press Use this answer on a run, change anything you like, and save, or set it by hand.
4. **Review.** Comparisons shows both answers side by side. AI Executions lists every attempt with its cost and raw request and response. Bulk Runs lists past bulk runs.
5. **Measure accuracy.** Import `.context/sample_tickets_100_v2.csv`, run the tickets, and read the accuracy section on Overview. Labels are stored separately and never sent to a model. Scores use each side's latest finished real run. Failed runs are listed and not counted as wrong, and fake-AI runs are never scored.
6. **Export.** The Tickets page downloads tickets, AI executions and comparisons as CSV. Exports leave out raw payloads and secrets.

**Test-run reports** are in `reports/test-runs/`. To create one, run this from `backend/`:

```bash
.venv/bin/python -m scripts.run_report --run-id <id> --name "<name>" --note "<note>" --comparisons <cmp_a,cmp_b,...>
```

## Good to know

- **Paid calls are never repeated silently.** A refused connection, HTTP 429 or a 5xx error gets at most 3 attempts, with growing delays, and `Retry-After` is honoured up to 10 seconds. Other errors, timeouts and broken connections are not retried, because the provider may already have charged for the call.
- **Bulk runs:** one at a time. In an all-eligible run, a side that already succeeded on a ticket with the same model is skipped. If the backend is killed mid-run, the run is marked Interrupted on the next start and is not resumed.
- **Costs are estimates.** Each run keeps the rates it used, so changing a price never alters past costs. Local models cost nothing per call, and OpenAI has no default rate. Check hosted rates against the provider's current price list, and set them on the Settings page.
- **Categories:** labels already used by a record cannot be removed or renamed. Each level needs 2 to 16 options, the limit Jev accepts.
- **One backend process.** The active categories and bulk runs live in the backend process, so do not run several workers.
- **Dependency updates:** Dependabot (`.github/dependabot.yml`) opens a weekly pull request for the backend, frontend and e2e packages, and skips releases younger than 7 days. There is no CI, so run the checks in `CLAUDE.md` locally before merging one.

## Troubleshooting

| Problem | What to do |
|---|---|
| Pages say "Cannot reach the TicketLens backend" | Start the backend (step 3). If it runs on another address, set `VITE_API_BASE_URL`. |
| `/api/health/ready` returns 503, or pages say the database is unavailable | Start MongoDB (step 1) and check `mongosh --eval 'db.runCommand({ ping: 1 })'`. |
| `mongod` fails with a permissions error | The data folder was probably created with `sudo`. Give it back to your user: `sudo chown -R "$(whoami)" ~/data`. |
| The backend will not start and names an unknown setting | A variable in `backend/.env` is misspelt. Compare it with `backend/.env.example`. |
| A badge or run says "not configured" | The key is missing from `backend/.env`, or you meant to use local models and `JEV_BASE_URL` still points to TypeSafe. Restart the backend after changing it. |
| "Could not reach ... Is it running?" | Start Ollama, and check that `ollama list` shows the model. |
| A local model times out | The first run loads the model and can be slow. Raise `PROVIDER_TIMEOUT_SECONDS`, or lower the bulk speed in Settings. |
| Jev rejects the API key (401 or 403) | Check `TYPESAFE_API_KEY` in `backend/.env` and restart. Not retried. |
| Jev reports insufficient credits (402) | Add credits to your TypeSafe account. Not retried. |
| "is limiting requests" (429) | Quota or rate limit. Wait, lower the bulk speed in Settings, or check the provider account. |
| A run says the OpenAI connection is not built | OpenAI is deferred and has no adapter. Use `LLM_BACKEND=ollama`. |
| The browser console shows a CORS error | `FRONTEND_ORIGIN` must exactly match the address in your browser, and `localhost` and `127.0.0.1` count as different. Restart the backend after changing it. |
| Ports 8000 or 5173 are busy | Stop whatever is using them, or pass another port, then update `FRONTEND_ORIGIN` or `VITE_API_BASE_URL` to match. |

## Check it works

From the repository root:

```bash
backend/.venv/bin/pytest backend -q
backend/.venv/bin/ruff check backend
npm --prefix frontend run lint
npm --prefix frontend run build
npm --prefix e2e test    # browser tests on an isolated copy; first install them as in e2e/README.md
```

Local verification checklist:

- [ ] `/api/health/ready` reports ready.
- [ ] Create a ticket, then find it in the list.
- [ ] Run both sides on it from Compare, and see both answers and the agreement.
- [ ] Choose a final answer on its page, and see the source shown.
- [ ] See the run under AI Executions, and open its request and response.
- [ ] Import the sample CSV: 100 valid. Import it again: 100 duplicates and nothing added.
- [ ] Download the three CSV exports.
- [ ] Delete the ticket, and confirm its runs are gone too.
- [ ] Switch between light and dark.

## Documentation

- `README.md`: what the repository is for, what Jev is, and the demo.
- `.context/PROGRESS.md`: start here when taking over. It has the status, a handover summary, decisions and test results.
- `.context/README.md`: what each spec and status document is for.
- `backend/README.md`, `frontend/README.md`, `reports/README.md`: what each folder holds.
- `.context/DEPLOYMENT_DECISIONS.md`: deployment readiness, and what must be decided before going online.
- `.context/ROADMAP.md`: phase order in plain language, and the steps that need the owner.
- `.context/requirements.md`, `architecture.md`, `data-model.md`, `ai-evaluation.md`, `design.md`, `implementation.md`: the specification.
- `.context/code-size-standards.md`: code size and reuse rules.
- `e2e/README.md`: browser, visual and persona testing.
- `backend/.env.example`: every setting.
- `.github/dependabot.yml` and `dependency_risk_audits/`: dependency update config and the data-risk audits.
- `.context/sample_tickets_100_v2.csv`: the 100 labelled tickets to use. `sample_tickets_100.csv` is the file as first supplied, kept for reference. Do not evaluate with it, because its titles give away the answers.
- `AGENTS.md`, `CLAUDE.md`: instructions for coding agents.

## Scope

This is a local, single-user demo with no login. **Do not deploy it publicly as it is.** A MongoDB on your computer also cannot serve a cloud backend. See `.context/DEPLOYMENT_DECISIONS.md`.
