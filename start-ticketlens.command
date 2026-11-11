#!/usr/bin/env bash
# Double-click to start TicketLens (macOS): MongoDB, Ollama, the backend and the frontend, then open the app.
# Anything already running is reused. Close this window or press Ctrl-C to stop the backend and frontend
# this script started. MongoDB and Ollama keep running, so your data and models are never cut off mid-write.
# Set NO_BROWSER=1 to skip opening the browser. Logs: ~/Library/Logs/TicketLens/. Details: SETUP.md, "Run it locally".
cd "$(dirname "$0")" || exit 1  # repository root

APP_URL=http://localhost:5173
API_URL=http://127.0.0.1:8000
LOGS="$HOME/Library/Logs/TicketLens"
mkdir -p "$LOGS"

pids=()
trap 'kill "${pids[@]}" 2>/dev/null' EXIT  # only what this script started
trap 'exit 130' INT TERM HUP               # closing the Terminal window sends HUP

say() { printf '\n==> %s\n' "$*"; }
up() { curl -sf -o /dev/null "$1"; }
wait_for() {  # wait_for <url> <seconds>
  for _ in $(seq "$2"); do up "$1" && return 0; sleep 1; done
  return 1
}
fail() {
  printf '\nERROR: %s\n' "$*" >&2
  read -r -p "Press Enter to close." _
  exit 1
}

say "MongoDB"
if nc -z 127.0.0.1 27017 2>/dev/null; then
  echo "already running"
else
  MONGOD=$(command -v mongod)
  [ -z "$MONGOD" ] && MONGOD=$(ls -d /opt/homebrew/bin/mongod /usr/local/bin/mongod "$HOME"/mongodb-*/bin/mongod 2>/dev/null | head -1)
  [ -n "$MONGOD" ] || fail "mongod was not found. Install MongoDB Community Edition (SETUP.md, step 1), then try again."
  mkdir -p "$HOME/data/db"
  # 127.0.0.1 only: never expose MongoDB. --fork leaves it running after this script ends.
  "$MONGOD" --dbpath "$HOME/data/db" --bind_ip 127.0.0.1 --port 27017 \
    --logpath "$HOME/data/mongod.log" --logappend --fork >/dev/null || fail "MongoDB did not start. See ~/data/mongod.log"
  echo "started"
fi

say "Ollama (the local models)"
if up http://127.0.0.1:11434/api/version; then
  echo "already running"
else
  if [ -d /Applications/Ollama.app ]; then
    open -g -a Ollama
  elif command -v ollama >/dev/null; then
    nohup ollama serve >"$LOGS/ollama.log" 2>&1 &
  fi
  wait_for http://127.0.0.1:11434/api/version 30 && echo "started" \
    || echo "WARNING: Ollama is not running. Pages load, but Jev and LLM runs will fail until it is."
fi

say "Backend"
if up "$API_URL/api/health"; then
  echo "already running"
else
  # If backend/.env already picks the AI (local models or fake), leave it alone. Otherwise use the local models.
  # Only a yes/no check on two setting names: the file is never printed.
  if ! grep -qsE '^(JEV_BASE_URL|MOCK_PROVIDERS)=' backend/.env; then
    export JEV_BASE_URL=http://127.0.0.1:11434 JEV_MODEL=autotrust-jev:9b LLM_BACKEND=ollama
    export OLLAMA_MODEL=qwen3:8b PROVIDER_TIMEOUT_SECONDS=300
    echo "backend/.env sets no AI: using the local models (AutoTrust JEV and qwen3:8b)"
  fi
  if [ ! -x backend/.venv/bin/uvicorn ]; then
    echo "first run: installing backend packages"
    (cd backend && python3 -m venv .venv && .venv/bin/pip install -q -r requirements.txt) || fail "Backend install failed."
  fi
  # No --reload: a reloader leaves a child process that can outlive this script.
  (cd backend && exec .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 >"$LOGS/backend.log" 2>&1) &
  pids+=($!)
  wait_for "$API_URL/api/health/ready" 60 || fail "The backend did not become ready. See $LOGS/backend.log"
  echo "started"
fi

say "Frontend"
if up "$APP_URL/"; then
  echo "already running"
else
  if [ ! -d frontend/node_modules ]; then
    echo "first run: installing frontend packages"
    (cd frontend && npm install --silent) || fail "Frontend install failed."
  fi
  # Vite directly, not through npm, so killing this PID really stops the server.
  (cd frontend && exec node_modules/.bin/vite --port 5173 --strictPort >"$LOGS/frontend.log" 2>&1) &
  pids+=($!)
  wait_for "$APP_URL/" 30 || fail "The frontend did not start. See $LOGS/frontend.log"
  echo "started"
fi

say "TicketLens is ready: $APP_URL   (API docs: $API_URL/docs)"
[ -z "${NO_BROWSER:-}" ] && open "$APP_URL"  # opens your default browser

if [ "${#pids[@]}" -gt 0 ]; then
  echo "Leave this window open. Close it or press Ctrl-C to stop the servers started here."
  wait
else
  echo "Everything was already running, so there is nothing for this window to stop."
  read -r -p "Press Enter to close." _
fi
