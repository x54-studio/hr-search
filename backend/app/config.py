from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    DATABASE_URL: str = Field(..., description="PostgreSQL connection string")
    EMBEDDING_MODEL: str = Field(..., description="HuggingFace model name")
    HF_HOME: str = Field(default="./.models_cache", description="HuggingFace cache directory")
    API_HOST: str = Field(default="0.0.0.0")
    API_PORT: int = Field(default=8000)

    class Config:
        env_file = ".env"

settings = Settings()