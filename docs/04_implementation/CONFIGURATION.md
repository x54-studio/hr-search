# Configuration Guide

## Environment Variables

Create a `.env` file in the backend directory with the following variables:

```bash
# Database Configuration
DATABASE_URL=postgresql://postgres:postgres@localhost:5431/hr_search

# Embedding Model Configuration
EMBEDDING_MODEL=paraphrase-multilingual-MiniLM-L12-v2
HF_HOME=./.models_cache

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Search Thresholds (0-1, where 1 = perfect match)
SEMANTIC_THRESHOLD=0.3
FUZZY_THRESHOLD=0.2
```

## Search Thresholds Explained

### SEMANTIC_THRESHOLD
- **Range**: 0.0 - 1.0
- **Default**: 0.3 (recently lowered from 0.6)
- **Purpose**: Minimum cosine similarity for semantic search results
- **Recommendations**:
  - `0.2-0.3`: More permissive, catches more results (good for Polish HR terms)
  - `0.4-0.5`: Balanced approach
  - `0.6+`: Very strict, may miss relevant results

### FUZZY_THRESHOLD
- **Range**: 0.0 - 1.0
- **Default**: 0.2
- **Purpose**: Minimum similarity for fuzzy text matching (typo tolerance)
- **Recommendations**:
  - `0.1-0.2`: Allows many typos
  - `0.3-0.4`: Moderate typo tolerance
  - `0.5+`: Strict spelling requirements

## Quick Setup

1. **Create .env file**:
   ```bash
   cd backend
   echo "DATABASE_URL=postgresql://postgres:postgres@localhost:5431/hr_search" > .env
   echo "EMBEDDING_MODEL=paraphrase-multilingual-MiniLM-L12-v2" >> .env
   echo "SEMANTIC_THRESHOLD=0.3" >> .env
   echo "FUZZY_THRESHOLD=0.2" >> .env
   ```

2. **Test the configuration**:
   ```bash
   curl "http://localhost:8000/api/search?q=praca&debug=1"
   ```

## Troubleshooting

### No Semantic Results
If you see "No semantic results" in debug output:
1. Check if embeddings exist: `python scripts/check_database.py`
2. Generate embeddings: `python scripts/generate_embeddings.py`
3. Lower SEMANTIC_THRESHOLD to 0.2-0.3
4. Verify database connection

### Poor Search Quality
- **Too many irrelevant results**: Increase SEMANTIC_THRESHOLD
- **Too few results**: Decrease SEMANTIC_THRESHOLD
- **Typos not handled**: Decrease FUZZY_THRESHOLD
- **Too many typos accepted**: Increase FUZZY_THRESHOLD
