#!/usr/bin/env bash
# Start PostgreSQL (Homebrew) if it is not running, run the app, and stop PostgreSQL on exit.
set -euo pipefail

PG_BIN=/opt/homebrew/opt/postgresql@18/bin
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

cd "$PROJECT_DIR"

db_running() {
  "$PG_BIN/pg_isready" -h localhost -p 5432 >/dev/null 2>&1
}

stop_db() {
  brew services stop postgresql@18
}
trap stop_db EXIT

if lsof -nP -iTCP:8000 -sTCP:LISTEN >/dev/null 2>&1; then
  echo "Port 8000 is already in use. Stop the other server first." >&2
  exit 1
fi

if db_running; then
  echo "PostgreSQL is already running."
else
  echo "Starting PostgreSQL..."
  brew services start postgresql@18
  until db_running; do sleep 1; done
fi

.venv/bin/uvicorn app.main:app --reload
