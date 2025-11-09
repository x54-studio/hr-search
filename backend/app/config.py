"""
Application configuration using Pydantic Settings.

Simplified flat configuration for portfolio project.
"""

from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with simplified flat structure."""

    # Database
    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5431/hr_search",
        description="Database connection URL"
    )
    DB_POOL_MIN_SIZE: int = Field(default=5, description="Minimum pool size")
    DB_POOL_MAX_SIZE: int = Field(default=20, description="Maximum pool size")

    # ML Model
    EMBEDDING_MODEL: str = Field(
        default="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        description="Hugging Face model name"
    )
    HF_HOME: str = Field(default="./.models_cache", description="Model cache directory")

    # Search
    SEMANTIC_THRESHOLD: float = Field(default=0.3, description="Semantic search threshold")
    FUZZY_THRESHOLD: float = Field(default=0.2, description="Fuzzy search threshold")
    MAX_SEARCH_RESULTS: int = Field(default=50, description="Maximum search results")
    MAX_AUTOCOMPLETE_RESULTS: int = Field(default=10, description="Maximum autocomplete results")
    EMBEDDING_BATCH_SIZE: int = Field(default=32, description="Batch size for embedding generation")

    # API
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    CORS_ALLOW_ORIGINS: Union[List[str], str] = Field(
        default=["http://localhost:5173"],
        description="Allowed CORS origins (comma-separated string or list)"
    )
    
    @field_validator('CORS_ALLOW_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v: Union[List[str], str]) -> List[str]:
        """Parse CORS_ALLOW_ORIGINS from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # Ignore unknown fields from .env (e.g., DATABASE__POOL_MIN_SIZE)
    )


# Global settings instance
settings = Settings()