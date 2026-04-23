#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND_PID=""

cleanup() {
    echo ""
    [ -n "$BACKEND_PID" ] && kill "$BACKEND_PID" 2>/dev/null && echo "Backend stopped."
    exit 0
}
trap cleanup INT TERM

# --- Database ---
if ! docker compose -f "$ROOT/docker-compose.yml" ps --status running 2>/dev/null | grep -q db; then
    echo "Starting database..."
    docker compose -f "$ROOT/docker-compose.yml" up -d
fi
until docker compose -f "$ROOT/docker-compose.yml" exec -T db pg_isready -U postgres -d hr_search >/dev/null 2>&1; do
    sleep 1
done

# --- Backend ---
source "$ROOT/backend/.venv/bin/activate"
(cd "$ROOT/backend" && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload) &
BACKEND_PID=$!
echo "Backend starting (PID $BACKEND_PID)..."

# wait for backend to be ready
for i in $(seq 1 30); do
    curl -sf http://localhost:8000/api/health >/dev/null 2>&1 && break
    sleep 1
done

# --- Frontend ---
echo "Starting frontend..."
cd "$ROOT/frontend" && exec npm run dev
