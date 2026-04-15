"""
Dependency injection container for HR Search application.

Provides factory functions for creating and managing dependencies
including database connections, repositories, and services.
"""

import asyncpg
from typing import TYPE_CHECKING, Optional, Dict
from contextlib import asynccontextmanager
import asyncio
from sentence_transformers import SentenceTransformer

if TYPE_CHECKING:
    from fastapi import FastAPI

from .config import settings
from .exceptions import SearchError
from .logging_config import get_logger
from .repositories import (
    ItemRepository,
    CategoryRepository,
    SpeakerRepository,
    TagRepository,
    AutocompleteRepository,
    EmbeddingRepository,
)
from .services import SearchService, EmbeddingService

logger = get_logger("dependencies")


class ModelManager:
    """Model lifecycle manager for ML models."""

    def __init__(self):
        self.model: Optional[SentenceTransformer] = None
        self.model_loading = False

    async def initialize_model(self) -> SentenceTransformer:
        """Initialize the embedding model during app startup."""
        if self.model is not None:
            return self.model

        if self.model_loading:
            raise SearchError(
                "Model is already being loaded",
                model_name=settings.EMBEDDING_MODEL,
            )

        self.model_loading = True
        try:
            logger.info(
                "Loading embedding model during startup",
                extra={
                    "model_name": settings.EMBEDDING_MODEL,
                    "hf_home": settings.HF_HOME,
                },
            )

            # Set HuggingFace cache directory
            import os

            if settings.HF_HOME:
                os.environ.setdefault("HF_HOME", settings.HF_HOME)
                os.environ.setdefault("TRANSFORMERS_CACHE", settings.HF_HOME)
                os.environ.setdefault(
                    "SENTENCE_TRANSFORMERS_HOME", settings.HF_HOME
                )

            self.model = SentenceTransformer(settings.EMBEDDING_MODEL)

            logger.info(
                "Embedding model loaded successfully during startup",
                extra={
                    "model_name": settings.EMBEDDING_MODEL,
                    "model_dimensions": getattr(
                        self.model,
                        "get_sentence_embedding_dimension",
                        lambda: 384,  # Default embedding dimensions
                    )(),
                },
            )

            return self.model

        except Exception as e:
            logger.error(
                "Failed to load embedding model during startup",
                exc_info=e,
                extra={
                    "model_name": settings.EMBEDDING_MODEL,
                    "hf_home": settings.HF_HOME,
                },
            )
            raise SearchError(
                f"Failed to load embedding model: {settings.EMBEDDING_MODEL}",
                model_name=settings.EMBEDDING_MODEL,
            )
        finally:
            self.model_loading = False

    def get_model(self) -> SentenceTransformer:
        """Get the initialized model."""
        if self.model is None:
            raise SearchError(
                "Model not initialized. Call initialize_model() first.",
                model_name=settings.EMBEDDING_MODEL,
            )
        return self.model

    async def cleanup_model(self) -> None:
        """Cleanup model resources."""
        if self.model is not None:
            logger.info("Cleaning up embedding model")

            # Move model to CPU and clear GPU cache if available
            try:
                import torch

                if hasattr(self.model, "to"):
                    self.model.to("cpu")
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except ImportError:
                # torch not available, skip GPU cleanup
                pass

            # Clear the reference
            self.model = None
            logger.info("Embedding model cleaned up")


class DatabaseManager:
    """Database connection manager."""

    def __init__(self):
        self.connection_attempts = 0
        self.max_retries = 10
        self.retry_delay = 0.3

    async def create_pool(self) -> asyncpg.Pool:
        """Create database connection pool with retry logic."""
        logger.info(
            "Creating database connection pool",
            extra={
                "database_url": settings.DATABASE_URL.split("@")[
                    -1
                ],  # Hide credentials
                "min_size": settings.DB_POOL_MIN_SIZE,
                "max_size": settings.DB_POOL_MAX_SIZE,
                "command_timeout": 10,
            },
        )

        async def _init_connection(conn):
            """Initialize connection with vector codec if available."""
            try:
                # Check if pgvector extension is available
                await conn.fetchval("SELECT 1 FROM pg_type WHERE typname = 'vector'")
                
                # Encode Python list[float] -> vector text "[v1,v2,...]"
                def encode_vector(values: list[float]) -> str:
                    return "[" + ",".join(map(str, values)) + "]"

                # Decode vector text -> list[float]
                def decode_vector(text: str) -> list[float]:
                    return [float(x) for x in text.strip("[]").split(",") if x]

                await conn.set_type_codec(
                    "vector",
                    schema="pg_catalog",
                    encoder=encode_vector,
                    decoder=decode_vector,
                    format="text",
                )
                logger.debug("Vector codec registered successfully")
            except Exception as e:
                logger.warning(f"Could not register vector codec: {e}. Using string formatting instead.")

        for attempt in range(self.max_retries):
            try:
                pool = await asyncpg.create_pool(
                    dsn=settings.DATABASE_URL,
                    min_size=settings.DB_POOL_MIN_SIZE,
                    max_size=settings.DB_POOL_MAX_SIZE,
                    command_timeout=10,
                    init=_init_connection,
                )

                # Test the connection
                async with pool.acquire() as conn:
                    await conn.fetchval("SELECT 1")

                logger.info(
                    "Database pool created successfully",
                    extra={
                        "attempt": attempt + 1,
                        "pool_size": pool.get_size(),
                        "idle_size": pool.get_idle_size(),
                    },
                )

                return pool

            except Exception as e:
                self.connection_attempts = attempt + 1
                logger.error(
                    f"Database connection attempt {attempt + 1} failed",
                    exc_info=e,
                    extra={
                        "attempt": attempt + 1,
                        "max_retries": self.max_retries,
                        "retry_delay": self.retry_delay,
                    },
                )

                if attempt == self.max_retries - 1:
                    raise SearchError(
                        f"Failed to create database pool after {self.max_retries} attempts",
                    )

                await asyncio.sleep(self.retry_delay)

        raise SearchError("Unexpected error in pool creation")

    async def close_pool(self, pool: asyncpg.Pool) -> None:
        """Close database connection pool."""
        if pool:
            try:
                # Check if pool is already closed
                if hasattr(pool, "is_closed") and pool.is_closed():
                    return

                logger.info("Closing database connection pool")
                await pool.close()
                logger.info("Database connection pool closed")
            except Exception as e:
                logger.error("Error closing database pool", exc_info=e)


# Dependency factory functions
def get_database_pool(app: "FastAPI") -> asyncpg.Pool:
    """Get database connection pool from app state."""
    if not hasattr(app.state, "pool") or app.state.pool is None:
        raise SearchError(
            "Database pool not initialized"
        )
    return app.state.pool


def get_model_manager(app: "FastAPI") -> ModelManager:
    """Get model manager from app state."""
    if (
        not hasattr(app.state, "model_manager")
        or app.state.model_manager is None
    ):
        raise SearchError(
            "Model manager not initialized",
            model_name=settings.EMBEDDING_MODEL,
        )
    return app.state.model_manager


async def get_pool_stats(pool: asyncpg.Pool) -> Dict[str, int]:
    """Get connection pool statistics."""
    return {
        "size": pool.get_size(),
        "idle": pool.get_idle_size(),
        "max_size": pool.get_max_size(),
        "min_size": pool.get_min_size(),
    }


async def warmup_pool(pool: asyncpg.Pool, target_size: int = 5) -> None:
    """Pre-create connections to avoid cold start."""
    connections = []
    try:
        for _ in range(target_size):
            conn = await pool.acquire()
            connections.append(conn)
        logger.info(f"Warmed up {len(connections)} connections")
    finally:
        for conn in connections:
            await pool.release(conn)


def get_item_repository(pool: asyncpg.Pool) -> ItemRepository:
    """Create ItemRepository instance."""
    return ItemRepository(pool)


def get_category_repository(pool: asyncpg.Pool) -> CategoryRepository:
    """Create CategoryRepository instance."""
    return CategoryRepository(pool)


def get_speaker_repository(pool: asyncpg.Pool) -> SpeakerRepository:
    """Create SpeakerRepository instance."""
    return SpeakerRepository(pool)


def get_tag_repository(pool: asyncpg.Pool) -> TagRepository:
    """Create TagRepository instance."""
    return TagRepository(pool)


def get_autocomplete_repository(pool: asyncpg.Pool) -> AutocompleteRepository:
    """Create AutocompleteRepository instance."""
    return AutocompleteRepository(pool)


def get_embedding_repository(pool: asyncpg.Pool) -> EmbeddingRepository:
    """Create EmbeddingRepository instance."""
    return EmbeddingRepository(pool)


# Service factory functions
def get_search_service(
    item_repo: ItemRepository,
    category_repo: CategoryRepository,
    speaker_repo: SpeakerRepository,
    tag_repo: TagRepository,
    autocomplete_repo: AutocompleteRepository,
    embedding_repo: EmbeddingRepository,
    embedding_service: EmbeddingService,
) -> SearchService:
    """Create SearchService instance with all dependencies."""
    return SearchService(
        item_repo=item_repo,
        category_repo=category_repo,
        speaker_repo=speaker_repo,
        tag_repo=tag_repo,
        autocomplete_repo=autocomplete_repo,
        embedding_repo=embedding_repo,
        embedding_service=embedding_service,
    )


def get_embedding_service(
    embedding_repo: EmbeddingRepository, app: "FastAPI"
) -> EmbeddingService:
    """Create EmbeddingService instance with shared model."""
    model_manager = get_model_manager(app)
    return EmbeddingService(embedding_repo, model_manager)


# FastAPI dependency functions for services
def get_search_service_dependency(app: "FastAPI") -> SearchService:
    """FastAPI dependency for SearchService."""
    pool = get_database_pool(app)

    # Create all repositories
    item_repo = get_item_repository(pool)
    category_repo = get_category_repository(pool)
    speaker_repo = get_speaker_repository(pool)
    tag_repo = get_tag_repository(pool)
    autocomplete_repo = get_autocomplete_repository(pool)
    embedding_repo = get_embedding_repository(pool)

    # Create embedding service
    embedding_service = get_embedding_service(embedding_repo, app)

    # Create search service
    return get_search_service(
        item_repo=item_repo,
        category_repo=category_repo,
        speaker_repo=speaker_repo,
        tag_repo=tag_repo,
        autocomplete_repo=autocomplete_repo,
        embedding_repo=embedding_repo,
        embedding_service=embedding_service,
    )


# FastAPI dependency wrappers
def create_search_service_dependency(app: "FastAPI"):
    """Create a dependency function for SearchService."""

    def _get_search_service() -> SearchService:
        return get_search_service_dependency(app)

    return _get_search_service


def create_embedding_service_dependency(app: "FastAPI"):
    """Create a dependency function for EmbeddingService."""

    def _get_embedding_service() -> EmbeddingService:
        pool = get_database_pool(app)
        embedding_repo = get_embedding_repository(pool)
        return get_embedding_service(embedding_repo, app)

    return _get_embedding_service


# Lifespan management
@asynccontextmanager
async def dependency_lifespan(app: "FastAPI"):
    """Manage dependency lifecycle."""
    logger.info("Initializing dependencies")

    # Initialize database pool
    try:
        db_manager = DatabaseManager()
        app.state.pool = await db_manager.create_pool()
        app.state.db_manager = db_manager
        
        # Warm up the pool
        await warmup_pool(app.state.pool, target_size=5)
        
        logger.info("Database pool initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize database pool", exc_info=e)
        raise SearchError(f"Database initialization failed: {str(e)}")

    # Initialize model
    try:
        model_manager = ModelManager()
        await model_manager.initialize_model()
        app.state.model_manager = model_manager
        logger.info("Model initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize model", exc_info=e)
        raise SearchError(f"Model initialization failed: {str(e)}")

    logger.info("Dependencies initialized successfully")

    yield

    # Cleanup
    logger.info("Cleaning up dependencies")
    try:
        # Cleanup model
        if hasattr(app.state, "model_manager") and app.state.model_manager:
            await app.state.model_manager.cleanup_model()

        # Cleanup database pool
        if (
            hasattr(app.state, "db_manager")
            and app.state.db_manager
            and hasattr(app.state, "pool")
            and app.state.pool
        ):
            await app.state.db_manager.close_pool(app.state.pool)

        logger.info("Dependencies cleaned up successfully")
    except Exception as e:
        logger.error("Error during dependency cleanup", exc_info=e)
