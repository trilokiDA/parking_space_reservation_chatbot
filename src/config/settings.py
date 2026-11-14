"""Application settings and configuration management."""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application configuration settings."""

    # OpenAI Configuration
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    embedding_model: str = Field(default="text-embedding-3-small", env="EMBEDDING_MODEL")
    llm_model: str = Field(default="gpt-3.5-turbo", env="LLM_MODEL")
    llm_temperature: float = Field(default=0.7, env="LLM_TEMPERATURE")
    max_tokens: int = Field(default=500, env="MAX_TOKENS")

    # Database Configuration
    database_url: str = Field(default="sqlite:///data/dynamic_data.db", env="DATABASE_URL")

    # Vector Store Configuration
    vector_store_path: str = Field(default="vectorstore/faiss_index", env="VECTOR_STORE_PATH")

    # Application Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    chunk_size: int = Field(default=500, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=50, env="CHUNK_OVERLAP")
    retrieval_k: int = Field(default=3, env="RETRIEVAL_K")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @property
    def base_dir(self) -> Path:
        """Get base directory of the project."""
        return Path(__file__).parent.parent.parent

    @property
    def data_dir(self) -> Path:
        """Get data directory."""
        return self.base_dir / "data"

    @property
    def static_data_dir(self) -> Path:
        """Get static data directory."""
        return self.data_dir / "static_data"


def get_settings() -> Settings:
    """Get application settings instance."""
    return Settings()
