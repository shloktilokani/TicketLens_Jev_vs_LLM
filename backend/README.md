# backend/

The FastAPI service: tickets, AI runs, comparisons, bulk runs, accuracy and settings, stored in MongoDB. How it fits together is in `.context/architecture.md`; the stored data is in `.context/data-model.md`.

## Files

| Path | Purpose |
|---|---|
| `app/main.py` | App factory and startup: database connection, indexes, interrupted work, saved taxonomy |
| `app/api/` | Route handlers, one file per area (tickets, runs, executions, bulk_jobs, evaluation, app_settings, …) |
| `app/services/` | Workflows: one AI run (`executions.py`), comparisons, CSV import and export, dashboard, accuracy, settings, reports |
| `app/jobs/bulk.py` | Bulk runs: a bounded worker pool, progress saved after every attempt |
| `app/providers/` | AI adapters: `jev.py` (System One), `ollama.py` (LLM), `mock.py` (fake AI), `registry.py` (picks one), `http.py` (shared call and retries), `base.py` (contract) |
| `app/repositories/` | The only code that talks to MongoDB |
| `app/schemas/` | Pydantic request and response models |
| `app/core/` | Settings (the only environment reader), taxonomy, pricing, redaction, clock |
| `scripts/init_db.py` | Creates the indexes; safe to repeat |
| `scripts/run_report.py` | Writes a test-run report to `reports/test-runs/` |
| `tests/` | pytest suite (335 tests). It uses the throwaway database `ticketlens_test` and skips if MongoDB is down |
| `.env.example` | Every setting, with comments. Copy it to `.env`, which git ignores |
| `pyproject.toml`, `requirements.txt` | ruff and pytest configuration; pinned dependencies |

## Run and check

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
.venv/bin/pytest -q && .venv/bin/ruff check .
```

The API docs are at http://127.0.0.1:8000/docs in development.

## Rules and gotchas

- **Settings** come only from `app/core/settings.py`. An unknown key in `.env` stops startup, so misspellings are caught. With `APP_ENV=production`, unsafe settings also stop startup.
- **Saved settings win.** Values saved on the Settings page (`app_settings` collection) override `.env` for models, threshold, concurrency, prompt, taxonomy and rates.
- **The provider key `gpt` means the LLM side,** whichever model serves it.
- **One process only** (`--workers 1`). The active taxonomy and bulk jobs live in memory, and startup marks unfinished jobs as Interrupted.
- **AI runs are always recorded.** A provider failure becomes a stored run with a safe message, never an exception to the caller.
- **Retries** happen only for a refused connection, 429 and 5xx, with at most 3 attempts. Timeouts and other errors are never retried, so paid calls are not repeated.
- **Tests skip the real waits:** `conftest.py` turns retry pauses off, and every test resets the active taxonomy to the built-in one.
- **Paid APIs are deferred.** Hosted Jev is built but untested with a real key. OpenAI has no adapter; `LLM_BACKEND=openai` records a `not_configured` run.
