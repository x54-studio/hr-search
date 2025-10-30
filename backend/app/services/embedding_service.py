"""
Embedding service for managing ML model and embedding generation.

Handles model loading, caching, and embedding generation operations
with proper error handling and performance monitoring.
"""

from typing import List
from sentence_transformers import SentenceTransformer
import asyncio

from ..exceptions import SearchError, ValidationError
from ..logging_config import LoggingMixin
from ..config import settings
from ..repositories import EmbeddingRepository
from ..cache import cached


class EmbeddingService(LoggingMixin):
    """Service for embedding-related operations."""

    def __init__(self, embedding_repo: EmbeddingRepository, model_manager):
        """Initialize embedding service with repository and model manager."""
        self.embedding_repo = embedding_repo
        self.model_manager = model_manager

    def get_model(self) -> SentenceTransformer:
        """
        Get the embedding model from the model manager.

        Returns:
            Loaded SentenceTransformer model

        Raises:
            SearchError: If model is not initialized
        """
        return self.model_manager.get_model()

    @cached(ttl=3600, key_prefix="embedding")
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for given text with proper error handling.

        Args:
            text: Text to generate embedding for

        Returns:
            List of embedding values

        Raises:
            ValidationError: If text is invalid
            SearchError: If embedding generation fails
        """
        if not text or not text.strip():
            raise ValidationError("Text cannot be empty", field="text", value=text)

        if len(text) > 200:
            raise ValidationError(
                "Text too long (max 200 characters)", field="text", value=len(text)
            )

        try:
            model = self.get_model()
            self.log_debug(
                "Generating embedding",
                extra={
                    "text_length": len(text),
                    "text_preview": (text[:100] + "..." if len(text) > 100 else text),
                },
            )

            # Run embedding generation in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None,
                lambda: model.encode(
                    text, normalize_embeddings=True, show_progress_bar=False
                ).tolist(),
            )

            self.log_debug(
                "Embedding generated successfully",
                extra={
                    "text_length": len(text),
                    "embedding_dimensions": len(embedding),
                },
            )

            return embedding

        except Exception as e:
            self.log_error(
                "Failed to generate embedding",
                exception=e,
                extra={
                    "text_length": len(text),
                    "text_preview": (text[:100] + "..." if len(text) > 100 else text),
                },
            )
            raise SearchError(
                "Failed to generate embedding for text",
                query=text[:100] + "..." if len(text) > 100 else text,
                search_type="embedding",
                cause=e,
            ) from e

    async def generate_all_embeddings(self) -> None:
        """
        Generate embeddings for all published webinars without embeddings.

        Raises:
            SearchError: If embedding generation fails
        """
        try:
            model = self.get_model()

            # Get all webinars without embeddings
            webinars = await self.embedding_repo.get_webinars_without_embeddings()

            if not webinars:
                self.log_info("All webinars already have embeddings")
                return

            self.log_info("Generating embeddings", extra={"count": len(webinars)})

            # Generate embeddings in batches
            batch_size = settings.EMBEDDING_BATCH_SIZE
            for i in range(0, len(webinars), batch_size):
                batch = webinars[i : i + batch_size]

                # Combine title and description for better context
                texts = [f"{w['title']}. {w['description'] or ''}"[:100] for w in batch]

                # Generate embeddings in thread pool
                loop = asyncio.get_event_loop()
                embeddings = await loop.run_in_executor(
                    None,
                    lambda: model.encode(
                        texts,
                        batch_size=batch_size,
                        normalize_embeddings=True,
                        show_progress_bar=False,
                    ),
                )

                # Store in database
                for webinar, embedding in zip(batch, embeddings):
                    await self.embedding_repo.insert_embedding(
                        webinar["id"], "title", embedding.tolist()
                    )

            self.log_info(
                "Embeddings generated successfully",
                extra={"count": len(webinars)},
            )

        except Exception as e:
            self.log_error(
                "Failed to generate embeddings",
                exception=e,
                extra={
                    "webinar_count": (len(webinars) if "webinars" in locals() else 0)
                },
            )
            raise SearchError(
                f"Failed to generate embeddings: {str(e)}",
                model_name=settings.EMBEDDING_MODEL,
            ) from e

    async def get_embedding_stats(self) -> dict:
        """
        Get statistics about embeddings in the database.

        Returns:
            Dictionary with embedding statistics
        """
        try:
            return await self.embedding_repo.get_embeddings_stats()
        except Exception as e:
            self.log_error("Failed to get embedding stats", exception=e)
            raise SearchError(
                f"Failed to get embedding stats: {str(e)}",
                model_name=settings.EMBEDDING_MODEL,
            ) from e

    async def clear_all_embeddings(self) -> None:
        """
        Clear all embeddings from the database.

        Warning: This will remove all vector data and require regeneration.
        """
        try:
            await self.embedding_repo.clear_all_embeddings()
            self.log_info("All embeddings cleared from database")
        except Exception as e:
            self.log_error("Failed to clear embeddings", exception=e)
            raise SearchError(
                f"Failed to clear embeddings: {str(e)}",
                model_name=settings.EMBEDDING_MODEL,
            ) from e
