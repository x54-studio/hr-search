#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"

# --- Don't run as root ---
if [ "$(id -u)" -eq 0 ]; then
    echo "Don't run as root. Docker should work without sudo."
    exit 1
fi

# --- Prerequisites ---
for cmd in docker node python3; do
    command -v "$cmd" >/dev/null 2>&1 || { echo "Missing: $cmd"; exit 1; }
done
docker compose version >/dev/null 2>&1 || { echo "Missing: docker compose"; exit 1; }

# --- Database ---
echo "Starting database..."
docker compose -f "$ROOT/docker-compose.yml" up -d
echo "Waiting for database..."
until docker compose -f "$ROOT/docker-compose.yml" exec -T db pg_isready -U postgres -d hr_search >/dev/null 2>&1; do
    sleep 1
done
echo "Database ready."

# --- Backend dependencies ---
VENV="$ROOT/backend/.venv"
if [ ! -d "$VENV" ]; then
    echo "Creating Python venv..."
    python3 -m venv "$VENV"
fi
source "$VENV/bin/activate"
pip install -q -r "$ROOT/backend/requirements.txt"

# --- Frontend dependencies ---
echo "Installing frontend dependencies..."
(cd "$ROOT/frontend" && npm install --silent)

# --- Sample data ---
echo "Loading sample data..."
(cd "$ROOT/backend" && python -m scripts.data.generate_sample)

# --- Embeddings ---
echo "Generating embeddings (first run downloads ~500MB model)..."
(cd "$ROOT/backend" && python -m scripts.maintenance.generate_embeddings)

echo ""
echo "Setup complete. Run ./start.sh to launch."
