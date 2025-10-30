"""
Embedding repository for database operations related to ML embeddings.

Handles SQL queries for embedding storage, retrieval, and management
including batch operations for embedding generation.
"""

import asyncpg
from typing import List, Dict


class EmbeddingRepository:
    """Repository for embedding-related database operations."""

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def _fetch(self, query: str, *args) -> List[Dict]:
        """Execute query and return results as list of dictionaries."""
        async with self.pool.acquire() as conn:
            results = await conn.fetch(query, *args)
            return [dict(r) for r in results]

    async def _fetch_one(self, query: str, *args) -> Dict:
        """Execute query and return single result as dictionary."""
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow(query, *args)
            return dict(result) if result else None

    async def _execute(self, query: str, *args) -> None:
        """Execute query without returning results."""
        async with self.pool.acquire() as conn:
            await conn.execute(query, *args)

    async def get_webinars_without_embeddings(self, embedding_type: str = 'title') -> List[Dict]:
        """
        Get all published webinars that don't have embeddings yet.

        Returns:
            List of webinar records without embeddings
        """
        query = """
        SELECT w.id, w.title, w.description 
        FROM webinars w
        WHERE w.status = 'published'
        AND NOT EXISTS (
            SELECT 1 FROM webinar_embeddings e 
            WHERE e.webinar_id = w.id 
            AND e.embedding_type = $1
        )
        ORDER BY w.created_at DESC
        """

        return await self._fetch(query, embedding_type)

    async def insert_embedding(
        self, webinar_id: str, embedding_type: str, embedding: List[float]
    ) -> None:
        """
        Insert or update an embedding for a webinar.

        Args:
            webinar_id: UUID of the webinar
            embedding_type: Type of embedding ('title', 'description', etc.)
            embedding: Embedding vector as list of floats
        """
        query = """
        INSERT INTO webinar_embeddings 
        (webinar_id, embedding_type, vector)
        VALUES ($1, $2, $3::vector)
        ON CONFLICT (webinar_id, embedding_type) 
        DO UPDATE SET vector = $3::vector
        """

        # Format embedding as string for PostgreSQL
        embedding_str = f"[{','.join(map(str, embedding))}]"
        await self._execute(query, webinar_id, embedding_type, embedding_str)

    async def get_embedding_by_webinar(
        self, webinar_id: str, embedding_type: str = "title"
    ) -> Dict:
        """
        Get embedding for a specific webinar.

        Args:
            webinar_id: UUID of the webinar
            embedding_type: Type of embedding to retrieve

        Returns:
            Embedding record
        """
        query = """
        SELECT id, webinar_id, embedding_type, vector, created_at
        FROM webinar_embeddings
        WHERE webinar_id = $1 AND embedding_type = $2
        """

        result = await self._fetch_one(query, webinar_id, embedding_type)
        if not result:
            raise ValueError(f"Embedding not found for webinar {webinar_id}")
        return result

    async def delete_embeddings_by_webinar(self, webinar_id: str) -> None:
        """
        Delete all embeddings for a specific webinar.

        Args:
            webinar_id: UUID of the webinar
        """
        query = """
        DELETE FROM webinar_embeddings
        WHERE webinar_id = $1
        """

        await self._execute(query, webinar_id)

    async def count_embeddings(self) -> int:
        """
        Count total number of embeddings in the database.

        Returns:
            Total count of embeddings
        """
        query = "SELECT COUNT(*) FROM webinar_embeddings"
        result = await self._fetch_one(query)
        return int(result['count']) if result else 0

    async def get_embeddings_stats(self) -> Dict:
        """
        Get statistics about embeddings in the database.

        Returns:
            Dictionary with embedding statistics
        """
        query = """
        SELECT 
            COUNT(*) as total_embeddings,
            COUNT(DISTINCT webinar_id) as webinars_with_embeddings,
            COUNT(DISTINCT embedding_type) as embedding_types,
            MIN(created_at) as oldest_embedding,
            MAX(created_at) as newest_embedding
        FROM webinar_embeddings
        """

        result = await self._fetch_one(query)
        return result or {}

    async def clear_all_embeddings(self) -> None:
        """
        Clear all embeddings from the database.

        Warning: This will remove all vector data and require regeneration.
        """
        query = "DELETE FROM webinar_embeddings"
        await self._execute(query)