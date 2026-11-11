# Roadmap: phase status and owner inputs

This is the plain-language view of the build and of where the owner is needed. Acceptance criteria are in `implementation.md`, and detailed status, decisions and test results are in `PROGRESS.md`.

## Phase status (2026-11-11)

| # | Phase | In simple words | Status |
|---|---|---|---|
| 0-1 | Setup and scaffold | Repository, docs, an empty website and server that start | Done |
| 2 | Database connection | Server connects to MongoDB; health checks | Done |
| 3 | Rules and categories | Categories, priorities, statuses | Done |
| 4 | Tickets in the database | Create, edit, search and delete tickets; IDs like `SK-1001` | Done |
| 5-6 | App frame and ticket screens | Sidebar, theme, ticket list, form and detail page | Done |
| 7 | CSV import and export | Load tickets from a file; download data | Done |
| 8 | Fake AI | Pretend AIs for free testing | Done |
| 9 | Jev | Local AutoTrust JEV works. **Hosted TypeSafe Jev is deferred** | Local done; hosted deferred |
| 10 | LLM | A local Ollama LLM works. **OpenAI is deferred** | Local done; OpenAI deferred |
| 11 | Run history and cost | Every AI call logged with tokens and cost | Done |
| 12 | Side-by-side comparison | Run both and see where they agree; choose a final answer | Done |
| 13 | Bulk runs | Many tickets at once, with progress | Done |
| 14 | Sample data and scores | Corrected 100 tickets; accuracy on Overview | Done; dataset review open (E) |
| 15 | Settings page | Models, prompt, categories, prices, threshold, speed | Done |
| 16 | Testing and security | Full tests, failure cases, secret checks | Done |
| 17 | Final docs | README a newcomer can follow | Done; owner run-through open (F) |
| 18 | Deployment readiness | Prepared for hosting, not hosted | Done; decisions only if going online (G) |

**Paid APIs deferred (owner decision, 2026-11-11):** hosted Jev and OpenAI are not needed for now. Their architecture stays in place: the provider adapter contract, the hosted-Jev adapter, the `LLM_BACKEND=openai` setting, and rate snapshots. A future phase can add them without redesign. Items B, C and D below apply only then.

## Owner inputs

### A. MongoDB: done

MongoDB 9.0.4 is installed from the official archive, with mongosh, the database tools and Compass. It runs on `127.0.0.1` only, and the start command is in `SETUP.md`. Never start it with `sudo`, or the data folder becomes owned by root.

### B. API keys: deferred, needed only if paid APIs return

1. Create a key at TypeSafe or OpenAI. For OpenAI, set a monthly spending limit.
2. Put it in `backend/.env` (copied from `backend/.env.example`) after `TYPESAFE_API_KEY=` or `OPENAI_API_KEY=`.
3. Never paste a key into a chat, a commit or another file.

The OpenAI adapter must also be built first; only its setting and not-configured path exist.

### C. OpenAI model and prices: deferred

Pick the model, set `OPENAI_MODEL`, and enter its rates on the Settings page. Hosted Jev's default rate is $0.042 per million input tokens, with output free; check it against TypeSafe's current price list.

### D. Approve spending: deferred

Nothing paid runs without your approval, plus an estimate of the number of calls and the cost. Automated tests never call paid APIs.

### E. Review the corrected sample dataset: open

`.context/sample_tickets_100_v2.csv` has the same labels as the supplied file, with realistic titles and English text. Skim rows 4, 11, 30, 46, 52, 64, 81, 88, 95 and 100, and say whether the answers look right. Until then, accuracy figures are preliminary.

### F. Follow the README once: open

Set the app up from the README alone, and note any step that was unclear or failed.

### G. Deployment decisions: only before going online

The app has no login and must not be put online as it is. The decisions needed are in `DEPLOYMENT_DECISIONS.md`.

## Working rules

- **Git:** the coding agent never stages, commits or pushes. The owner reviews the changes in VS Code Source Control, then commits and pushes.
- **npm cache:** `~/.npm` may hold root-owned files. Fix them once with `sudo chown -R $(whoami) ~/.npm`, or pass `--cache` to npm.
- **Repository visibility:** check on GitHub that it is private if you want it private.
