from pathlib import Path
from pydantic import Field
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

    # Pydantic Settings (v2): load env from backend/.env explicitly
    model_config = SettingsConfigDict(
        env_file=[ENV_FILE_PATH],
        env_file_encoding="utf-8",
    )

settings = Settings()