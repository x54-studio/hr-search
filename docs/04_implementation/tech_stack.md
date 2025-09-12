# Technology Stack

## Frontend
- **React 18 + TypeScript** - Type safety, industry standard, great tooling
- **Vite** - Fast builds, HMR, zero config
- **Tailwind CSS** - Utility-first, rapid prototyping, mobile-responsive
- **Native fetch API** - No axios needed for simple GET requests

## Backend
- **Python 3.11+** - Native async/await, type hints
- **FastAPI** - Auto-generated OpenAPI docs, async by default, Pydantic validation
- **PostgreSQL 15** - Single database for everything
  - `pgvector` - Vector similarity search
  - `pg_trgm` - Fuzzy text matching
  - `unaccent` - Polish character normalization
- **asyncpg** - Fastest PostgreSQL driver, truly async
- **sentence-transformers** - Local embeddings (no API costs)
  - Model: `paraphrase-multilingual-MiniLM-L12-v2` (Polish + English support)

## Deployment
- **Docker** - Single container with both frontend and backend
- **mikr.us** - Free tier with PostgreSQL included
- **Architecture** - FastAPI serves React build from `/static` (no CORS issues)

## Why This Stack?

### Simplicity
- One database (PostgreSQL + extensions handles everything)
- One container (frontend + backend together)
- No external APIs (embeddings run locally)
- No authentication (internal tool behind VPN)

### Cost Effective
- **Our stack**: ~$1/month (domain only)
- **Alternative**: ~$100/month (Algolia + OpenAI + Pinecone)
- **Savings**: 99%

### Performance
- Search < 300ms (acceptable for users)
- Autocomplete < 100ms (feels instant)
- Memory < 512MB (fits free hosting)
- Bundle size < 500KB (loads fast on mobile)

## What We DON'T Use (and Why)

### Search
- ❌ **Elasticsearch** - Overkill for 1000 documents
- ❌ **Algolia** - Expensive ($50+/month) and external dependency
- ❌ **OpenAI Embeddings** - API costs and privacy concerns

### Infrastructure
- ❌ **Microservices** - Unnecessary complexity
- ❌ **Redis** - PostgreSQL is fast enough
- ❌ **Nginx** - FastAPI serves static files fine
- ❌ **Kubernetes** - Massive overkill

### Frontend
- ❌ **Next.js** - SSR unnecessary for internal tool
- ❌ **Redux** - Simple search doesn't need complex state
- ❌ **Component Libraries** - Generic look, large bundle

## Key Decisions Explained

**PostgreSQL + pgvector over dedicated vector DB**
- 1000 documents fit easily in PostgreSQL
- No need to manage multiple databases
- pgvector's HNSW index is fast enough

**Local embeddings over API**
- No per-request costs
- No network latency
- Data privacy (HR data stays internal)

**Single container deployment**
- Simpler to deploy and monitor
- No CORS configuration needed
- Fits within free tier limits

**No authentication**
- Internal tool accessed via company VPN
- Trusted users (HR employees)
- Reduces complexity significantly

## Performance Reality Check

| What We Promise | What's Realistic | Good Enough? |
|----------------|------------------|--------------|
| Search < 300ms | ~200ms average | ✅ Yes |
| 10 concurrent users | Handles 50+ | ✅ Yes |
| 99% uptime | ~95% on free tier | ✅ For internal tool |
| Mobile responsive | Works on all devices | ✅ Yes |
