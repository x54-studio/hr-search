# HR Knowledge Search

Domain-configurable semantic search engine. Handles Polish + English queries with typo correction, autocomplete, and filtering by category, speaker, tags, date range, and source type. Default domain: HR webinars and training materials.

Built as a learning project to explore Python, FastAPI, and Linux after years of working with C#. Mostly AI-assisted boilerplate, reviewed and understood by me.

## Quick Start

Prerequisites: Docker, Python 3.11+, Node.js 18+

```bash
# 1. Start the database
docker compose up -d

# 2. Start the backend (new terminal)
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.main

# 3. Start the frontend (new terminal)
cd frontend
npm install
npm run dev
```

Backend: http://localhost:8000 | Frontend: http://localhost:5173

## Tech Stack

| Layer | Stack |
|-------|-------|
| Frontend | React 18, TypeScript, Tailwind CSS, Vite |
| Backend | FastAPI, asyncpg, Pydantic |
| Database | PostgreSQL 15, pgvector, pg_trgm |
| ML | Sentence Transformers (paraphrase-multilingual-MiniLM-L12-v2) |

## How Search Works

1. Spell correction (pg_trgm fuzzy match)
2. Semantic search (pgvector cosine similarity on 384-dim embeddings)
3. Fuzzy fallback if no semantic results
4. Speaker name fallback

## API

| Endpoint | Description |
|----------|-------------|
| `GET /api/search?q=...` | Semantic search with spell correction |
| `GET /api/autocomplete?q=...` | Real-time suggestions |
| `GET /api/items` | List/filter by category, speaker, tags, date_range, source_type |
| `GET /api/items/{id}` | Item details |
| `GET /api/config` | Domain title and available source types |
| `GET /api/health` | Health check |

Full docs: [docs/04_implementation/api_documentation.md](docs/04_implementation/api_documentation.md)

## Project Structure

```
backend/    FastAPI app (Clean Architecture: repositories -> services -> API)
frontend/   React SPA (components, hooks, services)
docs/       Planning, requirements, design, implementation docs
```

## Running Tests

```bash
# Backend unit tests
cd backend && python -m pytest tests/unit/ -v

# Backend integration tests (requires running DB)
cd backend && python -m pytest tests/integration/ -v

# Frontend
cd frontend && npm run build && npm run lint
```

## License

MIT
