# Deployment readiness

The application is local-first. No hosting platform has been selected and nothing has been deployed. This document covers what is already prepared, what the owner must decide, and how to run it in production once those decisions are made.

## Non-negotiable constraints

- Do not point a cloud backend at `mongodb://127.0.0.1:27017`.
- Do not expose the local MongoDB port to the internet.
- Do not deploy the no-login demo publicly.
- Do not provision paid infrastructure without explicit approval.
- Keep API keys in server-side secret storage or environment variables.

## Decisions the owner must make

1. **Hosting** for the React frontend and the FastAPI backend.
2. **Production MongoDB** provider and its connection and security model.
3. **Access control:** real login in the app, or a proxy or VPN in front of it. Required before any exposure.
4. **Domain, HTTPS and allowed origin.**
5. **Backup, restore, retention and monitoring.**
6. **Expected monthly usage and budget,** including AI call costs.

## What the app already enforces

With `APP_ENV=production`, the backend refuses to start unless all of these hold:

| Setting | Rule |
|---|---|
| `MONGODB_URI` | Must not point to this computer |
| `FRONTEND_ORIGIN` | One exact `https://` address, no wildcard |
| `MOCK_PROVIDERS` | Must be false |
| `ACCESS_CONTROL_CONFIRMED` | Must be true |

`ACCESS_CONTROL_CONFIRMED=true` is the operator's statement that a proxy or VPN restricts who can reach the app. Setting it does not add any protection by itself. The API has no login, so anyone who can reach it can read and delete every ticket and spend AI credits.

Production also turns off the interactive API docs. Error messages never echo settings, so a bad value cannot print a database password. Tests: `backend/tests/test_production_config.py`.

## Development and production settings

| Setting | Development | Production |
|---|---|---|
| `APP_ENV` | `development` | `production` |
| `MONGODB_URI` | Local MongoDB | Injected secret; a managed or secured MongoDB reachable from the backend |
| `MONGODB_DATABASE` | `ticketlens` | Your production database |
| `FRONTEND_ORIGIN` | `http://localhost:5173` | Your exact `https://` frontend address |
| `TYPESAFE_API_KEY`, `OPENAI_API_KEY` | `backend/.env` | Injected by the platform's secret store, with no `.env` file on the server |
| `VITE_API_BASE_URL` | Default | Set at frontend build time to your `https://` API address. It is public, so never a secret |
| `LOG_LEVEL` | `INFO` | `INFO` |

Local AI models: `JEV_BASE_URL` and `OLLAMA_BASE_URL` must point to a server the backend can reach. A hosted backend cannot reach Ollama on your computer.

## Build and run

Frontend, which produces static files in `frontend/dist/` for any static host:

```bash
cd frontend
npm ci
VITE_API_BASE_URL=https://api.your-domain.example npm run build
```

Backend, behind an HTTPS proxy, with one worker:

```bash
cd backend
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1 \
  --proxy-headers --forwarded-allow-ips=127.0.0.1
```

- **One worker only.** The active taxonomy and running bulk jobs live in the backend process, and startup marks unfinished jobs as Interrupted, so a second worker would interrupt a running job. Moving to several workers needs job ownership and a shared taxonomy first. Both limits are marked as shortcuts in the code.
- **HTTPS** ends at the proxy, and the app itself serves plain HTTP. Bind to `127.0.0.1` when the proxy is on the same machine, and set `--forwarded-allow-ips` to the proxy's address, never `*`.
- **Health checks:** `/api/health` for liveness and `/api/health/ready` for readiness. The second returns 503 when the database is unreachable.
- **Pass secrets from the platform** as environment variables. The app reads them only in `core/settings.py`.

## Production MongoDB

- Must be reachable from the backend, with authentication and TLS on, and network access limited to the backend. A managed service such as MongoDB Atlas or a secured self-managed deployment both fit.
- Standalone MongoDB has no multi-document transactions. Ticket deletion is ordered so a retry can finish it, and it does not need them.
- Follow MongoDB's [security checklist](https://www.mongodb.com/docs/manual/administration/security-checklist/).

## Backup, restore and migration

Back up with [`mongodump`](https://www.mongodb.com/docs/database-tools/mongodump/) and restore with [`mongorestore`](https://www.mongodb.com/docs/database-tools/mongorestore/). Pass the URI through a config file, not the command line, so the password does not show in process lists:

```bash
mongodump --config=/secure/path/mongo.yaml --db=ticketlens --archive=ticketlens-YYYY-MM-DD.gz --gzip
mongorestore --config=/secure/path/mongo.yaml --archive=ticketlens-YYYY-MM-DD.gz --gzip --nsInclude='ticketlens.*'
```

- Collections: `tickets`, `ai_executions`, `comparisons`, `evaluation_labels`, `bulk_jobs`, `app_settings`, `counters`.
- `counters` holds ticket numbering, so it must be restored with the tickets or IDs could repeat.
- Test a restore on a separate database before relying on it. Backups hold stored AI requests and responses, so protect them like the database.
- **Migrations:** there is no migration tool yet because no schema change has needed one. Indexes are created at startup, safely repeatable, with `python -m scripts.init_db` also available. Back up first and add a recorded, reversible script for any future change to stored documents.

## Logging and monitoring

- The backend logs to standard output through Python logging. Collect it with the platform's tool. Log lines carry provider names and IDs, never keys or request bodies.
- Stored AI payloads have credentials removed, but they do hold ticket text. Decide how long to keep them.
- Watch at minimum: readiness failures, the share of failed runs, provider 429 and 402 errors, spend from `estimated_cost`, and bulk runs that end Interrupted or Failed.

## Readiness checklist

Ready now:

- [x] Development and production settings are separated, and unsafe production settings stop startup.
- [x] Production builds work, and the backend has health and readiness checks.
- [x] CORS allows one exact origin, and secrets stay server-side.
- [x] Proxy, HTTPS, backup, restore, logging and MongoDB requirements are documented here.

Blocking any deployment:

- [ ] Owner decisions 1 to 6 above.
- [ ] Access control exists and has been tested. The app has none of its own.
- [ ] Production MongoDB exists, and a backup has been restored successfully.
- [ ] Real data handling is decided. The app is built for synthetic data only, so real customer data needs a privacy review first.
- [ ] Nothing here has been run on a real host: these steps are prepared, not proven.
