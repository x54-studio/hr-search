

```markdown
# Search Algorithms Design

## Overview
Search system based on semantic similarity using vector embeddings with fuzzy matching fallback for typos.

## 1. Semantic Search (Primary)

### Embedding Model
```python
# Model: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
# Dimensions: 384
# Supports: Polish + English (HR terminology)

from sentence_transformers import SentenceTransformer
from typing import List, Optional

_model: Optional[SentenceTransformer] = None

def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    return _model

def generate_embedding(text: str) -> List[float]:
    """Generate embedding for given text"""
    model = get_model()
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()
```

### Database Query
```sql
-- Semantic search using cosine similarity
SELECT 
    w.*,
    1 - (e.vector <=> $1::vector) as similarity
FROM webinars w
JOIN webinar_embeddings e ON w.id = e.webinar_id
WHERE 
    e.embedding_type = 'title'
    AND w.status = 'published'
    AND 1 - (e.vector <=> $1::vector) > 0.7
ORDER BY similarity DESC
LIMIT 20;
```

## 2. Fuzzy Search (Fallback)

### Using pg_trgm for typo tolerance
```sql
-- Fuzzy search for titles
SELECT 
    w.*,
    similarity(lower(unaccent(w.title)), lower(unaccent($1))) as score
FROM webinars w
WHERE 
    similarity(lower(unaccent(w.title)), lower(unaccent($1))) > 0.3
    AND w.status = 'published'
ORDER BY score DESC
LIMIT 20;
```

## 3. Autocomplete

### Simple prefix matching
```sql
-- Unified autocomplete for webinars, speakers, tags
(
    SELECT title as suggestion, 'webinar' as type
    FROM webinars
    WHERE lower(title) LIKE lower($1) || '%' 
    AND status = 'published'
    LIMIT 3
)
UNION ALL
(
    SELECT name as suggestion, 'speaker' as type
    FROM speakers
    WHERE lower(name) LIKE lower($1) || '%'
    LIMIT 3
)
UNION ALL
(
    SELECT name as suggestion, 'tag' as type
    FROM tags
    WHERE lower(name) LIKE lower($1) || '%'
    LIMIT 3
)
ORDER BY type, suggestion
LIMIT 10;
```

## 4. Main Search Implementation

```python
import asyncpg
from typing import Dict, List

async def search(query: str, pool: asyncpg.Pool) -> List[Dict]:
    """
    Main search function - semantic search with fuzzy fallback
    """
    if not query or not query.strip():
        return []
    
    # Truncate very long queries
    query = query[:200]
    
    async with pool.acquire() as conn:
        # Generate embedding for query
        query_embedding = generate_embedding(query)
        
        # Try semantic search first
        results = await conn.fetch(
            """
            SELECT 
                w.id, w.title, w.description, w.duration_ms,
                c.name as category_name,
                1 - (e.vector <=> $1::vector) as similarity,
                array_agg(DISTINCT s.name) FILTER (WHERE s.name IS NOT NULL) as speakers,
                array_agg(DISTINCT t.name) FILTER (WHERE t.name IS NOT NULL) as tags
            FROM webinars w
            JOIN webinar_embeddings e ON w.id = e.webinar_id
            LEFT JOIN categories c ON w.category_id = c.id
            LEFT JOIN webinar_speakers ws ON w.id = ws.webinar_id
            LEFT JOIN speakers s ON ws.speaker_id = s.id
            LEFT JOIN webinar_tags wt ON w.id = wt.webinar_id
            LEFT JOIN tags t ON wt.tag_id = t.id
            WHERE 
                e.embedding_type = 'title'
                AND w.status = 'published'
                AND 1 - (e.vector <=> $1::vector) > 0.7
            GROUP BY w.id, w.title, w.description, w.duration_ms, c.name, e.vector
            ORDER BY similarity DESC
            LIMIT 20
            """,
            query_embedding
        )
        
        # If no semantic results, try fuzzy search
        if not results:
            results = await conn.fetch(
                """
                SELECT 
                    w.id, w.title, w.description, w.duration_ms,
                    c.name as category_name,
                    similarity(lower(unaccent(w.title)), lower(unaccent($1))) as similarity,
                    array_agg(DISTINCT s.name) FILTER (WHERE s.name IS NOT NULL) as speakers,
                    array_agg(DISTINCT t.name) FILTER (WHERE t.name IS NOT NULL) as tags
                FROM webinars w
                LEFT JOIN categories c ON w.category_id = c.id
                LEFT JOIN webinar_speakers ws ON w.id = ws.webinar_id
                LEFT JOIN speakers s ON ws.speaker_id = s.id
                LEFT JOIN webinar_tags wt ON w.id = wt.webinar_id
                LEFT JOIN tags t ON wt.tag_id = t.id
                WHERE 
                    similarity(lower(unaccent(w.title)), lower(unaccent($1))) > 0.3
                    AND w.status = 'published'
                GROUP BY w.id, w.title, w.description, w.duration_ms, c.name
                ORDER BY similarity DESC
                LIMIT 20
                """,
                query
            )
        
        return [dict(r) for r in results]

async def autocomplete(query: str, pool: asyncpg.Pool) -> List[Dict]:
    """
    Autocomplete suggestions from webinars, speakers, and tags
    """
    if not query:
        return []
    
    async with pool.acquire() as conn:
        results = await conn.fetch(
            """
            (
                SELECT title as suggestion, 'webinar' as type
                FROM webinars
                WHERE lower(title) LIKE lower($1) || '%' 
                AND status = 'published'
                LIMIT 3
            )
            UNION ALL
            (
                SELECT name as suggestion, 'speaker' as type
                FROM speakers
                WHERE lower(name) LIKE lower($1) || '%'
                LIMIT 3
            )
            UNION ALL
            (
                SELECT name as suggestion, 'tag' as type
                FROM tags
                WHERE lower(name) LIKE lower($1) || '%'
                LIMIT 3
            )
            ORDER BY type, suggestion
            LIMIT 10
            """,
            query
        )
        
        return [dict(r) for r in results]
```

## 5. Batch Embedding Generation

```python
async def generate_all_embeddings(pool: asyncpg.Pool):
    """
    Generate embeddings for all published webinars
    Run this after data import or when adding new webinars
    """
    model = get_model()
    
    async with pool.acquire() as conn:
        # Get all webinars without embeddings
        webinars = await conn.fetch(
            """
            SELECT w.id, w.title, w.description 
            FROM webinars w
            WHERE w.status = 'published'
            AND NOT EXISTS (
                SELECT 1 FROM webinar_embeddings e 
                WHERE e.webinar_id = w.id 
                AND e.embedding_type = 'title'
            )
            """
        )
        
        if not webinars:
            print("All webinars already have embeddings")
            return
        
        # Generate embeddings in batches
        batch_size = 32
        for i in range(0, len(webinars), batch_size):
            batch = webinars[i:i+batch_size]
            
            # Combine title and description for better context
            texts = [
                f"{w['title']}. {w['description'] or ''}"[:500] 
                for w in batch
            ]
            
            # Generate embeddings
            embeddings = model.encode(
                texts, 
                batch_size=batch_size,
                normalize_embeddings=True,
                show_progress_bar=True
            )
            
            # Store in database
            for webinar, embedding in zip(batch, embeddings):
                await conn.execute(
                    """
                    INSERT INTO webinar_embeddings 
                    (webinar_id, embedding_type, vector)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (webinar_id, embedding_type) 
                    DO UPDATE SET vector = $3
                    """,
                    webinar['id'],
                    'title',
                    embedding.tolist()
                )
        
        print(f"Generated embeddings for {len(webinars)} webinars")
```

## 6. Filter Queries

```python
async def search_by_category(
    category_id: str, 
    pool: asyncpg.Pool
) -> List[Dict]:
    """Search webinars by category"""
    async with pool.acquire() as conn:
        results = await conn.fetch(
            """
            SELECT w.*, c.name as category_name
            FROM webinars w
            JOIN categories c ON w.category_id = c.id
            WHERE w.category_id = $1 
            AND w.status = 'published'
            ORDER BY w.recorded_date DESC
            LIMIT 20
            """,
            category_id
        )
        return [dict(r) for r in results]

async def search_by_speaker(
    speaker_name: str, 
    pool: asyncpg.Pool
) -> List[Dict]:
    """Search webinars by speaker"""
    async with pool.acquire() as conn:
        results = await conn.fetch(
            """
            SELECT w.*, s.name as speaker_name
            FROM webinars w
            JOIN webinar_speakers ws ON w.id = ws.webinar_id
            JOIN speakers s ON ws.speaker_id = s.id
            WHERE lower(s.name) LIKE '%' || lower($1) || '%'
            AND w.status = 'published'
            ORDER BY w.recorded_date DESC
            LIMIT 20
            """,
            speaker_name
        )
        return [dict(r) for r in results]
```

## 7. Polish Language Support

### Known Limitations

**Bilingual HR terminology**: The embedding model may not recognize that 
"exit interview" and "rozmowa wyjściowa" refer to the same concept. This 
affects ~10% of searches where users mix languages.

**Workaround**: Users can search both terms if first search yields no results.

**Future solution**: Enrich embeddings with bilingual variants during indexing 
(not during search) to maintain performance.

### Common HR Terms Requiring Translation

| English | Polish |
|---------|---------|
| exit interview | rozmowa wyjściowa |
| onboarding | wdrażanie pracownika |
| sick leave / L4 | zwolnienie lekarskie |
| performance review | ocena pracownicza |
| KPI | wskaźniki efektywności |

Note: This table is for documentation only. Term expansion is not implemented 
in MVP to keep search latency under 100ms.

## 8. Performance Optimizations

### Connection Pool Setup
```python
import asyncpg

async def create_pool() -> asyncpg.Pool:
    """Create connection pool for PostgreSQL"""
    return await asyncpg.create_pool(
        host='localhost',
        port=5432,
        database='hr_search',
        user='postgres',
        password='postgres',
        min_size=2,
        max_size=10,
        command_timeout=10
    )
```

### Caching Strategy
```python
from functools import lru_cache
import hashlib

@lru_cache(maxsize=100)
def get_cached_embedding(text_hash: str) -> List[float]:
    """Cache frequently searched queries"""
    # In production, this would retrieve from cache
    return generate_embedding(text_hash)

def hash_query(query: str) -> str:
    """Generate hash for query caching"""
    return hashlib.md5(query.encode()).hexdigest()
```

## Notes

1. **Primary search**: Semantic search using embeddings (0.7 similarity threshold)
2. **Fallback**: Fuzzy search with pg_trgm (0.3 similarity threshold)
3. **No keyword search**: We don't use full-text search or search_vector
4. **Embedding type**: Always 'title' for consistency
5. **Model**: paraphrase-multilingual-MiniLM-L12-v2 for Polish/English support
6. **Performance**: All queries should be < 100ms with proper indexes
