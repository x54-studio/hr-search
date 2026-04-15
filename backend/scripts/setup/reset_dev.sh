#!/bin/bash
set -e
echo "Resetting development environment..."

cd "$(dirname "$0")/../../.."

docker compose down -v
docker compose up -d
echo "Waiting for PostgreSQL..."
sleep 3

cd backend
source .venv/bin/activate
python scripts/data/generate_sample.py
python scripts/maintenance/generate_embeddings.py
python scripts/verify_system.py

echo "Done. Run 'python -m app.main' to start the backend."
