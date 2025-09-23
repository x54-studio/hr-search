# HR Knowledge Search System

## 🎯 Problem & Solution

**Problem**: Company with 500+ HR webinars and PDFs has no effective search. HR employees waste 15-30 minutes finding relevant training materials.

**Solution**: Semantic search engine with Polish language support, autocomplete, and fuzzy matching for typos. Reduces search time to under 2 minutes.

## ⚡ Key Features

- **Semantic Search** - Finds conceptually similar content using ML embeddings
- **Polish + English** - Handles mixed HR terminology ("exit interview", "zwolnienie lekarskie")
- **Instant Autocomplete** - Suggestions from webinars, speakers, and tags
- **Fuzzy Matching** - Tolerates typos (e.g., "rekrutcja" → "rekrutacja")
- **Smart Filters** - By category, speaker, tags (with OR logic for multiple tags)
- **Mobile First** - Responsive design, touch-friendly interface

## 🛠 Tech Stack

**Frontend**
- React 18 + TypeScript + Vite
- Tailwind CSS
- Native fetch API (no axios needed)

**Backend**
- FastAPI (Python 3.11)
- PostgreSQL 15 with pgvector extension
- Sentence Transformers (paraphrase-multilingual-MiniLM-L12-v2)

**Infrastructure**
- Docker (single container)
- mikr.us hosting (free tier)

## 📂 Documentation Structure

```
docs/
├── 01_planning/
│   ├── project_scope.md        # Problem, goals, constraints
│   └── tech_feasibility.md     # Why these algorithms?
│
├── 02_requirements/
│   ├── functional_requirements.md  # What the search must do
│   └── search_scenarios.md        # Example queries and expected results
│
├── 03_design/
│   ├── architecture.md         # System components + data flow
│   ├── database_schema.md      # Tables, indexes, queries
│   ├── database_erd.md         # Visual database relationships
│   └── search_algorithms.md    # Semantic, fuzzy, autocomplete logic
│
├── 04_implementation/
│   ├── tech_stack.md           # Technology choices and rationale
│   └── api_documentation.md    # REST API endpoints
│
├── glossary.md                 # Technical and HR terms
└── README.md                    # This file
```

## 🚀 How It Works

1. **User types query** → Frontend sends to API
2. **Generate embedding** → Convert query to 384-dim vector
3. **Semantic search** → Find similar vectors using cosine similarity
4. **Fallback to fuzzy** → If no results, try fuzzy text matching
5. **Return results** → Merge, rank, and return top 20 matches

## 📊 Performance

| Metric | Target | Why |
|--------|--------|-----|
| Search response | < 300ms | Fast enough for users |
| Autocomplete | < 100ms | Feels instant |
| Memory usage | < 512MB | Fits free hosting tier |
| Database size | ~10MB | 1000 webinars + embeddings |

## 🔍 API Endpoints

- `GET /api/search?q=motywacja` - Semantic search
- `GET /api/autocomplete?q=mot` - Real-time suggestions
- `GET /api/webinars/{id}` - Webinar details
- `GET /api/webinars?tags=rekrutacja,motywacja` - List with filters
- `GET /api/categories` - All categories
- `GET /api/speakers` - All speakers

Full API documentation: [api_documentation.md](docs/04_implementation/api_documentation.md)

## 💡 Design Decisions

### Why PostgreSQL + pgvector?
- Single database for everything (simpler ops)
- Handles 1000 documents easily
- No need for Elasticsearch or Pinecone

### Why no authentication?
- Internal HR tool deployed within company VPN
- Trusted users, no public access

### Why offset/limit instead of pages?
- Modern UX with infinite scroll
- Simpler API and frontend code
- Better for mobile users

### What's NOT included (intentionally)
- Redis cache - PostgreSQL is fast enough for 1000 records
- Microservices - unnecessary complexity
- Rate limiting - trusted internal users
- Full-text search_vector - embeddings handle search better

## 🏗 Database Schema

**7 normalized tables:**
- `webinars` - Core content
- `categories` - HR domains
- `speakers` - Presenter info
- `tags` - Searchable labels
- `webinar_speakers` - Many-to-many
- `webinar_tags` - Many-to-many
- `webinar_embeddings` - ML vectors

See [database_schema.md](docs/03_design/database_schema.md) for details.

Or [database_erd.md](docs/03_design/database_erd.md) for diagrams.

## 🧠 Search Algorithm

```python
# Simplified flow
embedding = model.encode(query)  # Convert to vector
semantic_results = pgvector_search(embedding)  # Cosine similarity
if not semantic_results:
    fuzzy_results = pg_trgm_search(query)  # Fuzzy fallback
return rank_and_merge(results)
```

See [search_algorithms.md](docs/03_design/search_algorithms.md) for implementation.

## 📈 Future Improvements

- **Audio transcriptions** - Search within webinar content
- **RAG implementation** - Generate answers from content
- **User personalization** - Track favorites and history
- **Analytics** - Which webinars are most useful

## 🛡 Why This Stack for Portfolio?

1. **Practical problem** - Real business value, not another TODO app
2. **Modern tech** - FastAPI, TypeScript, vector embeddings
3. **Polish language** - Shows handling of non-English content
4. **Simple deployment** - Actually deployable on free tier
5. **Clean documentation** - Structured SDLC approach

## 📝 License

MIT

---

*This is a portfolio project demonstrating full-stack development with ML-powered search.*
