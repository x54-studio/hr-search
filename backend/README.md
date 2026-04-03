# Backend

FastAPI + asyncpg + Sentence Transformers.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.main    # Runs at http://localhost:8000
```

Requires PostgreSQL with pgvector running (`docker compose up -d` from project root).

## Structure

```
app/
  main.py           FastAPI app, routes, middleware
  config.py         Pydantic settings (env-based)
  dependencies.py   DI container
  repositories/     Data access (asyncpg, raw SQL)
  services/         Business logic (SearchService, EmbeddingService)
  cache/            In-memory cache with TTL/LRU
scripts/
  setup/            init.sql, seed.sql (auto-run by docker-compose)
  data/             Sample data generator
  maintenance/      Embedding generation, DB optimization
tests/
  unit/             Mocked DB, no infra needed
  integration/      Requires running database
```

## Tests

```bash
pip install -r requirements-dev.txt
python -m pytest tests/unit/ -v
python -m pytest tests/integration/ -v   # needs DB running
```
