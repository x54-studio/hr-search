import asyncpg
from typing import List, Dict, Optional, Tuple
import logging
from sentence_transformers import SentenceTransformer
import asyncio
from .config import settings

_model: Optional[SentenceTransformer] = None

def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        # Allow overriding model and cache via settings for portability
        model_name = settings.EMBEDDING_MODEL or "paraphrase-multilingual-MiniLM-L12-v2"
        # Respect HF_HOME if provided (HuggingFace uses env var)
        import os
        if settings.HF_HOME:
            os.environ.setdefault("HF_HOME", settings.HF_HOME)
            os.environ.setdefault("TRANSFORMERS_CACHE", settings.HF_HOME)
            os.environ.setdefault("SENTENCE_TRANSFORMERS_HOME", settings.HF_HOME)
        _model = SentenceTransformer(model_name)
    return _model

def generate_embedding(text: str) -> List[float]:
    """Generate embedding for given text"""
    model = get_model()
    return model.encode(text, normalize_embeddings=True, show_progress_bar=False).tolist()

async def search(query: str, pool: asyncpg.Pool, limit: int = 20, debug: bool = False) -> List[Dict]:
    """
    Main search function - semantic search with fuzzy fallback
    """
    import time
    start_time = time.time()
    
    if not query or not query.strip():
        return []
    
    # Truncate very long queries
    query = query[:200].strip()
    logger = logging.getLogger("hr_search.search")
    log = logger.info if debug else logger.debug
    log(f"Searching for '{query}' (semantic_threshold={settings.SEMANTIC_THRESHOLD}, fuzzy_threshold={settings.FUZZY_THRESHOLD})")
    
    async with pool.acquire() as conn:
        # Generate embedding for query
        log("Generating embedding")
        embedding_start = time.time()
        query_embedding = generate_embedding(query)
        embedding_time = time.time() - embedding_start
        log(f"Embedding generated: duration_sec={round(embedding_time, 3)} dims={len(query_embedding)}")
        if debug:
            logger.info(f"Embedding preview: {[float(v) for v in query_embedding[:5]]}")
        
        # Try semantic search first
        log("Running semantic search")
        semantic_start = time.time()
        # Convert embedding to pgvector string format and cast in SQL
        embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
        results = await conn.fetch(
            """
            SELECT 
                w.id, w.title, w.description, w.duration_ms, w.recorded_date,
                w.video_url, w.pdf_url,
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
                AND 1 - (e.vector <=> $1::vector) > $3
            GROUP BY w.id, w.title, w.description, w.duration_ms, w.recorded_date,
                     w.video_url, w.pdf_url, c.name, e.vector
            ORDER BY similarity DESC
            LIMIT $2
            """,
            embedding_str,
            limit,
            settings.SEMANTIC_THRESHOLD
        )
        semantic_time = time.time() - semantic_start
        log(f"Semantic search done: duration_sec={round(semantic_time, 3)} results={len(results)}")
        if debug and results:
            logger.info("Top semantic results (id, similarity, title):")
            for r in results[:10]:
                logger.info(f"  {r['id']}  sim={float(r['similarity']):.3f}  title={r['title']}")
        
        # If no semantic results, try fuzzy search
        if not results:
            if debug:
                logger.warning(f"No semantic results (threshold={settings.SEMANTIC_THRESHOLD})")
            log("Trying fuzzy search")
            fuzzy_start = time.time()
            results = await conn.fetch(
                """
                SELECT 
                    w.id, w.title, w.description, w.duration_ms, w.recorded_date,
                    w.video_url, w.pdf_url,
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
                    similarity(lower(unaccent(w.title)), lower(unaccent($1))) > $3
                    AND w.status = 'published'
                GROUP BY w.id, w.title, w.description, w.duration_ms, w.recorded_date,
                         w.video_url, w.pdf_url, c.name
                ORDER BY similarity DESC
                LIMIT $2
                """,
                query,
                limit,
                settings.FUZZY_THRESHOLD
            )
            fuzzy_time = time.time() - fuzzy_start
            log(f"Fuzzy search done: duration_sec={round(fuzzy_time, 3)} results={len(results)}")
            if debug and results:
                logger.info("Top fuzzy results (id, similarity, title):")
                for r in results[:10]:
                    logger.info(f"  {r['id']}  sim={float(r['similarity']):.3f}  title={r['title']}")
        
        total_time = time.time() - start_time
        log(f"Search finished: total_duration_sec={round(total_time, 3)}")
        
        return [dict(r) for r in results]

async def autocomplete(query: str, pool: asyncpg.Pool, limit: int = 10) -> List[Dict]:
    """
    Autocomplete suggestions from webinars, speakers, and tags
    """
    if not query or not query.strip():
        return []
    
    query = query.strip()
    
    async with pool.acquire() as conn:
        results = await conn.fetch(
            """
            (
                SELECT title as suggestion, 'webinar' as type, 1 as priority
                FROM webinars
                WHERE lower(title) LIKE lower($1) || '%' 
                AND status = 'published'
                LIMIT 3
            )
            UNION ALL
            (
                SELECT name as suggestion, 'speaker' as type, 2 as priority
                FROM speakers
                WHERE lower(name) LIKE lower($1) || '%'
                LIMIT 3
            )
            UNION ALL
            (
                SELECT name as suggestion, 'tag' as type, 3 as priority
                FROM tags
                WHERE lower(name) LIKE lower($1) || '%'
                LIMIT 3
            )
            ORDER BY priority, suggestion
            LIMIT $2
            """,
            query,
            limit
        )
        
        return [dict(r) for r in results]

async def search_by_category(category_slug: str, pool: asyncpg.Pool, offset: int = 0, limit: int = 20) -> Tuple[List[Dict], int]:
    """Search webinars by category with pagination and total count."""
    async with pool.acquire() as conn:
        total = await conn.fetchval(
            """
            SELECT COUNT(*)
            FROM webinars w
            JOIN categories c ON w.category_id = c.id
            WHERE c.slug = $1
              AND w.status = 'published'
            """,
            category_slug,
        )

        results = await conn.fetch(
            """
            SELECT 
                w.id, w.title, w.description, w.duration_ms, w.recorded_date,
                w.video_url, w.pdf_url,
                c.name as category_name,
                array_agg(DISTINCT s.name) FILTER (WHERE s.name IS NOT NULL) as speakers,
                array_agg(DISTINCT t.name) FILTER (WHERE t.name IS NOT NULL) as tags
            FROM webinars w
            JOIN categories c ON w.category_id = c.id
            LEFT JOIN webinar_speakers ws ON w.id = ws.webinar_id
            LEFT JOIN speakers s ON ws.speaker_id = s.id
            LEFT JOIN webinar_tags wt ON w.id = wt.webinar_id
            LEFT JOIN tags t ON wt.tag_id = t.id
            WHERE c.slug = $1 
              AND w.status = 'published'
            GROUP BY w.id, w.title, w.description, w.duration_ms, w.recorded_date,
                     w.video_url, w.pdf_url, c.name
            ORDER BY w.recorded_date DESC NULLS LAST
            LIMIT $2 OFFSET $3
            """,
            category_slug,
            limit,
            offset,
        )
        return ([dict(r) for r in results], int(total or 0))

async def search_by_speaker(speaker_name: str, pool: asyncpg.Pool, offset: int = 0, limit: int = 20) -> Tuple[List[Dict], int]:
    """Search webinars by speaker with pagination and total count."""
    async with pool.acquire() as conn:
        total = await conn.fetchval(
            """
            SELECT COUNT(DISTINCT w.id)
            FROM webinars w
            JOIN webinar_speakers ws ON w.id = ws.webinar_id
            JOIN speakers s ON ws.speaker_id = s.id
            WHERE lower(s.name) LIKE '%' || lower($1) || '%'
              AND w.status = 'published'
            """,
            speaker_name,
        )

        results = await conn.fetch(
            """
            SELECT 
                w.id, w.title, w.description, w.duration_ms, w.recorded_date,
                w.video_url, w.pdf_url,
                c.name as category_name,
                array_agg(DISTINCT s.name) FILTER (WHERE s.name IS NOT NULL) as speakers,
                array_agg(DISTINCT t.name) FILTER (WHERE t.name IS NOT NULL) as tags
            FROM webinars w
            JOIN webinar_speakers ws ON w.id = ws.webinar_id
            JOIN speakers s ON ws.speaker_id = s.id
            LEFT JOIN categories c ON w.category_id = c.id
            LEFT JOIN webinar_tags wt ON w.id = wt.webinar_id
            LEFT JOIN tags t ON wt.tag_id = t.id
            WHERE lower(s.name) LIKE '%' || lower($1) || '%'
              AND w.status = 'published'
            GROUP BY w.id, w.title, w.description, w.duration_ms, w.recorded_date,
                     w.video_url, w.pdf_url, c.name
            ORDER BY w.recorded_date DESC NULLS LAST
            LIMIT $2 OFFSET $3
            """,
            speaker_name,
            limit,
            offset,
        )
        return ([dict(r) for r in results], int(total or 0))

async def search_by_tags(tag_slugs: List[str], pool: asyncpg.Pool, offset: int = 0, limit: int = 20) -> Tuple[List[Dict], int]:
    """Search webinars by tags (OR logic) with pagination and total count."""
    if not tag_slugs:
        return ([], 0)
    
    async with pool.acquire() as conn:
        # Total count placeholders: $1..$N for tag slugs
        placeholders_count = ','.join([f'${i+1}' for i in range(len(tag_slugs))])
        total = await conn.fetchval(
            f"""
            SELECT COUNT(DISTINCT w.id)
            FROM webinars w
            JOIN webinar_tags wt ON w.id = wt.webinar_id
            JOIN tags t ON wt.tag_id = t.id
            WHERE t.slug IN ({placeholders_count})
              AND w.status = 'published'
            """,
            *tag_slugs,
        )

        # Data query placeholders: $1 limit, $2 offset, tags start from $3..$N
        placeholders_data = ','.join([f'${i+3}' for i in range(len(tag_slugs))])
        results = await conn.fetch(
            f"""
            SELECT 
                w.id, w.title, w.description, w.duration_ms, w.recorded_date,
                w.video_url, w.pdf_url,
                c.name as category_name,
                array_agg(DISTINCT s.name) FILTER (WHERE s.name IS NOT NULL) as speakers,
                array_agg(DISTINCT t.name) FILTER (WHERE t.name IS NOT NULL) as tags
            FROM webinars w
            JOIN webinar_tags wt ON w.id = wt.webinar_id
            JOIN tags t ON wt.tag_id = t.id
            LEFT JOIN categories c ON w.category_id = c.id
            LEFT JOIN webinar_speakers ws ON w.id = ws.webinar_id
            LEFT JOIN speakers s ON ws.speaker_id = s.id
            WHERE t.slug IN ({placeholders_data})
              AND w.status = 'published'
            GROUP BY w.id, w.title, w.description, w.duration_ms, w.recorded_date,
                     w.video_url, w.pdf_url, c.name
            ORDER BY w.recorded_date DESC NULLS LAST
            LIMIT $1 OFFSET $2
            """,
            limit,
            offset,
            *tag_slugs,
        )
        return ([dict(r) for r in results], int(total or 0))

async def get_webinar_details(webinar_id: str, pool: asyncpg.Pool) -> Optional[Dict]:
    """Get full details of a specific webinar"""
    async with pool.acquire() as conn:
        result = await conn.fetchrow(
            """
            SELECT 
                w.id, w.title, w.description, w.duration_ms, w.recorded_date,
                w.video_url, w.pdf_url, w.status,
                c.name as category_name,
                array_agg(DISTINCT s.name) FILTER (WHERE s.name IS NOT NULL) as speakers,
                array_agg(DISTINCT t.name) FILTER (WHERE t.name IS NOT NULL) as tags
            FROM webinars w
            LEFT JOIN categories c ON w.category_id = c.id
            LEFT JOIN webinar_speakers ws ON w.id = ws.webinar_id
            LEFT JOIN speakers s ON ws.speaker_id = s.id
            LEFT JOIN webinar_tags wt ON w.id = wt.webinar_id
            LEFT JOIN tags t ON wt.tag_id = t.id
            WHERE w.id = $1
            GROUP BY w.id, w.title, w.description, w.duration_ms, w.recorded_date,
                     w.video_url, w.pdf_url, w.status, c.name
            """,
            webinar_id
        )
        return dict(result) if result else None

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
            logging.getLogger("hr_search.search").info("All webinars already have embeddings")
            return
        
        logging.getLogger("hr_search.search").info("Generating embeddings", extra={"count": len(webinars)})
        
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
                show_progress_bar=False
            )
            
            # Store in database
            for webinar, embedding in zip(batch, embeddings):
                # Convert embedding to pgvector string format and cast in SQL
                embedding_str = '[' + ','.join(map(str, embedding.tolist())) + ']'
                await conn.execute(
                    """
                    INSERT INTO webinar_embeddings 
                    (webinar_id, embedding_type, vector)
                    VALUES ($1, $2, $3::vector)
                    ON CONFLICT (webinar_id, embedding_type) 
                    DO UPDATE SET vector = $3::vector
                    """,
                    webinar['id'],
                    'title',
                    embedding_str
                )
        
        logging.getLogger("hr_search.search").info("Embeddings generated", extra={"count": len(webinars)})

async def get_categories(pool: asyncpg.Pool) -> List[Dict]:
    """Get all categories with webinar count"""
    async with pool.acquire() as conn:
        results = await conn.fetch(
            """
            SELECT 
              c.slug, c.name,
              COALESCE(COUNT(w.id), 0) AS count
            FROM categories c
            LEFT JOIN webinars w ON w.category_id = c.id AND w.status = 'published'
            GROUP BY c.slug, c.name
            ORDER BY c.name
            """
        )
        return [dict(r) for r in results]

async def get_speakers(pool: asyncpg.Pool, limit: int = 100) -> List[Dict]:
    """Get all speakers with webinar count"""
    async with pool.acquire() as conn:
        results = await conn.fetch(
            """
            SELECT s.name, s.bio, COALESCE(COUNT(ws.webinar_id), 0) AS count
            FROM speakers s
            LEFT JOIN webinar_speakers ws ON ws.speaker_id = s.id
            LEFT JOIN webinars w ON w.id = ws.webinar_id AND w.status = 'published'
            GROUP BY s.name, s.bio
            ORDER BY s.name
            LIMIT $1
            """,
            limit
        )
        return [dict(r) for r in results]

async def get_tags(pool: asyncpg.Pool, limit: int = 100) -> List[Dict]:
    """Get all tags with webinar count"""
    async with pool.acquire() as conn:
        results = await conn.fetch(
            """
            SELECT t.slug, t.name, COALESCE(COUNT(wt.webinar_id), 0) AS count
            FROM tags t
            LEFT JOIN webinar_tags wt ON wt.tag_id = t.id
            LEFT JOIN webinars w ON w.id = wt.webinar_id AND w.status = 'published'
            GROUP BY t.slug, t.name
            ORDER BY t.name
            LIMIT $1
            """,
            limit
        )
        return [dict(r) for r in results]

async def get_popular_tags(pool: asyncpg.Pool, limit: int = 20) -> List[Dict]:
    """Get most used tags"""
    async with pool.acquire() as conn:
        results = await conn.fetch(
            """
            SELECT t.slug, t.name, COUNT(wt.webinar_id) AS count
            FROM tags t
            JOIN webinar_tags wt ON wt.tag_id = t.id
            JOIN webinars w ON w.id = wt.webinar_id AND w.status = 'published'
            GROUP BY t.slug, t.name
            ORDER BY count DESC
            LIMIT $1
            """,
            limit
        )
        return [dict(r) for r in results]

async def list_recent_webinars(pool: asyncpg.Pool, offset: int = 0, limit: int = 20) -> Tuple[List[Dict], int]:
    """Return most recent published webinars with pagination and total count."""
    async with pool.acquire() as conn:
        total = await conn.fetchval(
            """
            SELECT COUNT(*)
            FROM webinars w
            WHERE w.status = 'published'
            """,
        )

        results = await conn.fetch(
            """
            SELECT 
                w.id, w.title, w.description, w.duration_ms, w.recorded_date,
                w.video_url, w.pdf_url,
                c.name as category_name,
                array_agg(DISTINCT s.name) FILTER (WHERE s.name IS NOT NULL) as speakers,
                array_agg(DISTINCT t.name) FILTER (WHERE t.name IS NOT NULL) as tags
            FROM webinars w
            LEFT JOIN categories c ON w.category_id = c.id
            LEFT JOIN webinar_speakers ws ON w.id = ws.webinar_id
            LEFT JOIN speakers s ON ws.speaker_id = s.id
            LEFT JOIN webinar_tags wt ON w.id = wt.webinar_id
            LEFT JOIN tags t ON wt.tag_id = t.id
            WHERE w.status = 'published'
            GROUP BY w.id, w.title, w.description, w.duration_ms, w.recorded_date,
                     w.video_url, w.pdf_url, c.name
            ORDER BY w.recorded_date DESC NULLS LAST, w.created_at DESC
            LIMIT $1 OFFSET $2
            """,
            limit,
            offset,
        )
        return ([dict(r) for r in results], int(total or 0))