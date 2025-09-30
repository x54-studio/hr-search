from pathlib import Path
from typing import List, Union
from pydantic import Field
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve the absolute path to backend/.env so it works regardless of CWD
ENV_FILE_PATH = str(Path(__file__).resolve().parent.parent / ".env")


class Settings(BaseSettings):
    DATABASE_URL: str = Field(..., description="PostgreSQL connection string")
    EMBEDDING_MODEL: str = Field(..., description="HuggingFace model name")
    HF_HOME: str = Field(default="./.models_cache", description="HuggingFace cache directory")
    API_HOST: str = Field(default="0.0.0.0")
    API_PORT: int = Field(default=8000)
    SEMANTIC_THRESHOLD: float = Field(default=0.3, description="Cosine similarity threshold for semantic search (0-1)")
    FUZZY_THRESHOLD: float = Field(default=0.2, description="pg_trgm similarity threshold for fuzzy fallback (0-1)")

    # CORS configuration (env-overridable). Accepts JSON array or comma-separated string.
    CORS_ALLOW_ORIGINS: List[str] = Field(default=["http://localhost:5173"], description="Allowed CORS origins")
    CORS_ALLOW_METHODS: List[str] = Field(default=["GET", "POST"], description="Allowed CORS methods")
    CORS_ALLOW_HEADERS: List[str] = Field(default=["*"], description="Allowed CORS headers")
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True, description="Whether to allow credentials in CORS")

    @field_validator("CORS_ALLOW_ORIGINS", "CORS_ALLOW_METHODS", "CORS_ALLOW_HEADERS", mode="before")
    @classmethod
    def _coerce_csv_to_list(cls, v: Union[str, List[str]]):
        if isinstance(v, str):
            # Split comma-separated values, trim whitespace, drop empties
            return [item.strip() for item in v.split(",") if item.strip()]
        return v

    # Pydantic Settings (v2): load env from backend/.env explicitly
    model_config = SettingsConfigDict(
        env_file=[ENV_FILE_PATH],
        env_file_encoding="utf-8",
    )

settings = Settings()