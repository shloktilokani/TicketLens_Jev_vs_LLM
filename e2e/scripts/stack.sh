#!/usr/bin/env bash
# Starts an isolated copy of TicketLens for UI tests: backend on 127.0.0.1:8001 using database
# ticketlens_e2e (emptied on every start) and mock providers, frontend on localhost:5174.
# It never touches the dev servers (8000, 5173) or the real ticketlens database.
# Stop it with Ctrl-C or by killing this script; both servers stop with it.
set -euo pipefail
cd "$(dirname "$0")/../.."  # repository root

if [ "${E2E_PROVIDERS:-mock}" != "mock" ]; then
  # Paid APIs are deferred by owner decision; a run cap would be needed before enabling them.
  echo "Real-provider mode is not available: paid APIs are deferred (see e2e/README.md, 'Other provider modes')." >&2
  exit 1
fi

DB=ticketlens_e2e
backend/.venv/bin/python e2e/scripts/reset_db.py "$DB"

pids=()
trap 'kill "${pids[@]}" 2>/dev/null || true' EXIT INT TERM

# No --reload: a reloader leaves a child process that can outlive this script.
(cd backend && exec env MONGODB_DATABASE="$DB" MOCK_PROVIDERS=true \
  FRONTEND_ORIGIN=http://localhost:5174 \
  .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8001) &
pids+=($!)

# Start the frontend only once the backend reaches MongoDB, so "5174 is up" means "stack is ready".
for _ in $(seq 60); do
  curl -sf http://127.0.0.1:8001/api/health/ready >/dev/null && break
  sleep 1
done
curl -sf http://127.0.0.1:8001/api/health/ready >/dev/null || {
  echo "Backend on 8001 is not ready. Is MongoDB running? (README.md, 'Run locally')" >&2
  exit 1
}

# Vite directly, not through npm, so killing this PID really stops the server.
(cd frontend && exec env VITE_API_BASE_URL=http://127.0.0.1:8001 \
  node_modules/.bin/vite --port 5174) &
pids+=($!)

echo "UI test stack: http://localhost:5174 (API http://127.0.0.1:8001, database $DB, mock providers)"
wait
