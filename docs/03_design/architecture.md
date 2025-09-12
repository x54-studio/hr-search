# System Architecture

## C4 Level 1: System Context

```mermaid
graph TB
    User[HR Employee<br/>Person]
    System[HR Knowledge Search<br/>Software System]
    WebinarDB[(Existing Webinar Files<br/>500+ videos and PDFs)]
    
    User -->|Search queries| System
    System -->|Search results| User
    System -->|Reads metadata from| WebinarDB
    
    style User fill:#08427b,color:#fff
    style System fill:#1168bd,color:#fff
    style WebinarDB fill:#999,color:#fff
```

## C4 Level 2: Container Diagram

```mermaid
graph TB
    User[HR Employee]
    
    subgraph "HR Knowledge Search System"
        SPA[React SPA<br/>Container: TypeScript<br/>Search UI]
        API[API Server<br/>Container: FastAPI/Python<br/>Search + Embeddings]
        DB[(PostgreSQL<br/>Container: Database<br/>Metadata + Vectors)]
    end
    
    User -->|HTTPS| SPA
    SPA -->|REST API| API
    API -->|SQL + Vectors| DB
    
    style User fill:#08427b,color:#fff
    style SPA fill:#1168bd,color:#fff
    style API fill:#1168bd,color:#fff
    style DB fill:#1168bd,color:#fff
```

## Search Flow

```mermaid
flowchart LR
    subgraph Browser
        UI[React App<br/>Search Input]
    end
    
    subgraph "API Server"
        FastAPI[FastAPI<br/>Endpoint]
        Search[Search Logic]
        Embed[Embedding<br/>Model]
    end
    
    subgraph Database
        PG[(PostgreSQL<br/>+ pgvector<br/>+ pg_trgm)]
    end
    
    UI -->|GET /search?q=...| FastAPI
    FastAPI --> Search
    Search -->|Generate embedding| Embed
    Search -->|Vector + Text search| PG
    PG -->|Results| Search
    Search -->|Ranked results| FastAPI
    FastAPI -->|JSON| UI
```

## Search Request Sequence

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant A as API
    participant DB as PostgreSQL
    
    U->>F: Types "motyw"
    F->>A: GET /api/autocomplete?q=motyw
    A->>DB: SELECT title WHERE title ILIKE 'motyw%'
    DB-->>A: Results
    A-->>F: ["motywacja", "motywowanie zespołu"]
    F-->>U: Show dropdown
    
    U->>F: Submits "motywacja"
    F->>A: GET /api/search?q=motywacja
    
    A->>A: Generate embedding
    
    par Parallel queries
        A->>DB: Vector search (cosine similarity)
    and
        A->>DB: Text search (to_tsquery)
    and
        A->>DB: Fuzzy search (pg_trgm)
    end
    
    DB-->>A: Combined results
    A->>A: Merge & rank
    A-->>F: JSON results
    F-->>U: Display results
```

## Component Details

### Frontend (React SPA)
- **Framework**: React 18 + TypeScript + Vite
- **HTTP Client**: Native fetch API (no axios needed)
- **Styling**: Tailwind CSS
- **No unnecessary libs** - keep it simple

### Backend (FastAPI)
- **Framework**: FastAPI
- **Model**: paraphrase-multilingual-MiniLM-L12-v2 (Polish + English)
- **Dependencies**:
  - sentence-transformers (embeddings)
  - asyncpg (PostgreSQL driver)
  - python-dotenv (config)

### Database (PostgreSQL)
- **Version**: PostgreSQL 15+
- **Extensions**: 
  - pgvector - vector similarity
  - pg_trgm - fuzzy matching
  - unaccent - Polish characters normalization
- **Indexes**:
  - HNSW on vectors
  - GIN on tsvector
  - text_pattern_ops on title

## Deployment

```mermaid
graph TB
    subgraph "mikr.us hosting"
        Container[Single Docker Container<br/>FastAPI + Static Files]
        PG[(PostgreSQL<br/>Managed Database)]
    end
    
    subgraph "Local Development"
        Dev[Docker Compose<br/>All services]
    end
    
    User -->|HTTPS| Container
    Container -->|Connection string| PG
    Dev -.->|Deploy| Container
```

### Deployment Strategy
- **Development**: Docker Compose locally
- **Production**: Single container on mikr.us
  - Frontend: Built static files served by FastAPI
  - Backend: Same FastAPI instance
  - Database: Managed PostgreSQL from mikr.us
  - URL: https://hr-search.mikr.us

### Simplified Architecture Benefits
- One container to deploy (easier)
- No CORS issues (same origin)
- No separate hosting for frontend
- Minimal configuration

## Performance Targets

| Metric | Target | Why |
|--------|--------|-----|
| Search response | < 300ms | Acceptable for users |
| Autocomplete | < 100ms | Fast enough to feel instant |
| Concurrent users | 10 | Realistic for HR tool |
| Memory usage | < 512MB | Fits mikr.us free tier |

## Technology Decisions

### Why single container?
- Portfolio project - simplicity matters
- mikr.us has container limits
- No need for separate frontend hosting
- FastAPI can serve static files perfectly fine

### Why no React Query/Axios?
- Native fetch is enough for simple searches
- Less dependencies = smaller bundle
- Portfolio should show you can work without heavy libraries

### Why no rate limiting?
- Internal HR tool, not public API
- Adds complexity without real benefit
- Trust your users (it's an enterprise tool)

### What's NOT included (intentionally)
- Redis cache - PostgreSQL is fast enough for 1000 records
- Load balancer - single instance is fine
- Service mesh - overengineering
- API Gateway - FastAPI handles everything needed
