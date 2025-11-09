# HR Knowledge Search System

## 🎯 Problem & Solution

**Problem**: Company with 500+ HR webinars and PDFs has no effective search. HR employees waste 15-30 minutes finding relevant training materials.

**Solution**: Semantic search engine with Polish language support, autocomplete, and fuzzy matching for typos. Reduces search time to under 2 minutes.

## ⚡ Key Features

- **Spell-Correction Enhanced Semantic Search** - Automatically detects and corrects typos before semantic search
- **Semantic Search** - Finds conceptually similar content using ML embeddings
- **Speaker Name Search** - Search by speaker names (full name, first name, or last name)
- **Polish + English** - Handles mixed HR terminology ("exit interview", "zwolnienie lekarskie")
- **Instant Autocomplete** - Suggestions from webinars, speakers, and tags
- **Fuzzy Matching Fallback** - Fallback search when semantic search finds no results
- **Smart Filters** - Filter by category, speaker, tags (with OR logic for multiple tags), and date range
- **Date Range Filtering** - Filter webinars by last 30, 90, or 365 days
- **Keyboard Navigation** - Arrow keys to navigate suggestions, Enter to select, Escape to close
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
│   ├── api_documentation.md    # REST API endpoints
│   ├── CONFIGURATION.md        # Environment setup
│   ├── DEVELOPER_GUIDE.md      # Development workflow
│   ├── REFACTORED_ARCHITECTURE.md  # Clean architecture details
│   ├── SEARCH_IMPLEMENTATION.md    # Search algorithm details
│   ├── SECURITY.md             # Security considerations
│   ├── SPELL_CORRECTION.md     # Spell-correction feature
│   └── tech_stack.md           # Technology choices and rationale
│
├── glossary.md                 # Technical and HR terms
└── README.md                    # This file
```

## 🚀 How It Works

1. **User types query** → Frontend sends to API
2. **Spell correction check** → Quick fuzzy search to detect and correct typos
3. **Generate embedding** → Convert corrected query to 384-dim vector
4. **Semantic search** → Find similar vectors using cosine similarity
5. **Fallback to fuzzy** → If no semantic results, try fuzzy text matching
6. **Speaker search fallback** → If no fuzzy results, search by speaker names
7. **Return results** → Merge, rank, and return top 20 matches with correction info

## 📊 Performance

| Metric | Target | Why |
|--------|--------|-----|
| Search response | < 300ms | Fast enough for users |
| Autocomplete | < 100ms | Feels instant |
| Memory usage | < 512MB | Fits free hosting tier |
| Database size | ~10MB | 1000 webinars + embeddings |

## 🔍 API Endpoints

- `GET /api/search?q=motywacja` - Semantic search
- `GET /api/search?q=Agnieszka` - Speaker name search
- `GET /api/autocomplete?q=mot` - Real-time suggestions
- `GET /api/webinars/{id}` - Webinar details
- `GET /api/webinars?tags=rekrutacja,motywacja` - List with tag filters
- `GET /api/webinars?category=rekrutacja&date_range=last_30_days` - List with category and date filters
- `GET /api/webinars?speaker=Jan+Kowalski&date_range=last_90_days` - List with speaker and date filters
- `GET /api/webinars?date_range=last_365_days` - List filtered by date range (last_30_days, last_90_days, last_365_days)
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

## System Verification

To verify the system is working correctly:

```bash
cd backend
python scripts/verify_system.py
```

This checks:
- Database connectivity
- Sample data exists
- All API endpoints respond correctly
- ML model loaded successfully

## Performance Characteristics

**Observed Performance** (manual testing):
- Health check: ~10ms
- Metadata endpoints: ~30-50ms
- Semantic search: ~150-200ms
- Autocomplete: ~40-50ms
- Concurrent users: 100+ supported

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
# Enhanced spell-correction flow
fuzzy_suggestions = pg_trgm_search(query, limit=3)  # Quick spell check
if fuzzy_suggestions[0].similarity > 0.85:
    corrected_query = extract_correction(query, fuzzy_suggestions)
else:
    corrected_query = query

embedding = model.encode(corrected_query)  # Convert to vector
semantic_results = pgvector_search(embedding)  # Cosine similarity
if not semantic_results:
    fuzzy_results = pg_trgm_search(corrected_query)  # Fuzzy fallback
return rank_and_merge(results, corrected_query, original_query)
```

See [search_algorithms.md](docs/03_design/search_algorithms.md) for implementation.

For detailed spell-correction documentation, see [SPELL_CORRECTION.md](docs/04_implementation/SPELL_CORRECTION.md).

For recent improvements and cleanup summary, see [RECENT_IMPROVEMENTS.md](docs/04_implementation/RECENT_IMPROVEMENTS.md).

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

## 🔒 Security & Portfolio Context

**Important**: This is a **portfolio/demonstration project** with intentional simplifications:

- **No Authentication**: Intentionally omitted for portfolio simplicity. Production deployment would require proper authentication/authorization.
- **Environment Variables**: `.env` contains only local development settings with no sensitive data.
- **CORS Configuration**: Permissive settings for development; production would require stricter configuration.
- **Rate Limiting**: Not implemented as this is a demo tool, not a public API.

**Production Readiness**: This project demonstrates modern tech stack capabilities but is **not production-ready**. Real deployment would require:
- Authentication/authorization system
- Rate limiting and request validation
- Security audit and hardening
- Comprehensive monitoring and alerting
- Proper secrets management

## 📝 License

MIT

---

*This is a portfolio project demonstrating full-stack development with ML-powered search.*
