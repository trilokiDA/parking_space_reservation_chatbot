"""Application settings and configuration management."""
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application configuration settings."""

    # OpenAI Configuration
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")

    # Groq Configuration (fallback)
    groq_api_key: Optional[str] = Field(default=None, env="GROQ_API_KEY")

    # Model Configuration
    embedding_model: str = Field(default="text-embedding-3-small", env="EMBEDDING_MODEL")
    llm_model: str = Field(default="gpt-3.5-turbo", env="LLM_MODEL")
    llm_temperature: float = Field(default=0.7, env="LLM_TEMPERATURE")
    max_tokens: int = Field(default=500, env="MAX_TOKENS")

    # Provider selection (auto-detected if not specified)
    llm_provider: Optional[str] = Field(default=None, env="LLM_PROVIDER")

    # Database Configuration
    database_url: str = Field(default="sqlite:///data/dynamic_data.db", env="DATABASE_URL")

    # Vector Store Configuration
    vector_store_path: str = Field(default="vectorstore/faiss_index", env="VECTOR_STORE_PATH")

    # Application Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    chunk_size: int = Field(default=500, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=50, env="CHUNK_OVERLAP")
    retrieval_k: int = Field(default=3, env="RETRIEVAL_K")

    # Admin API Configuration
    admin_api_url: str = Field(default="http://127.0.0.1:5000", env="ADMIN_API_URL")
    admin_api_port: int = Field(default=5000, env="ADMIN_API_PORT")

    # MCP Server Configuration (Stage 3)
    mcp_server_api_key: Optional[str] = Field(default=None, env="MCP_SERVER_API_KEY")
    mcp_server_url: str = Field(default="http://127.0.0.1:8001", env="MCP_SERVER_URL")
    mcp_server_port: int = Field(default=8001, env="MCP_SERVER_PORT")

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

    def get_active_provider(self) -> str:
        """Determine which LLM provider to use.

        Returns:
            'openai' or 'groq' based on available API keys

        Raises:
            ValueError: If no API key is configured
        """
        if self.llm_provider:
            return self.llm_provider.lower()

        if self.openai_api_key:
            return "openai"
        elif self.groq_api_key:
            return "groq"
        else:
            raise ValueError(
                "No LLM API key configured. Please set either OPENAI_API_KEY or GROQ_API_KEY in your .env file."
            )

    def get_active_api_key(self) -> str:
        """Get the API key for the active provider.

        Returns:
            API key string

        Raises:
            ValueError: If no API key is configured
        """
        provider = self.get_active_provider()
        if provider == "openai":
            return self.openai_api_key
        elif provider == "groq":
            return self.groq_api_key
        else:
            raise ValueError(f"Unknown provider: {provider}")


def get_settings() -> Settings:
    """Get application settings instance."""
    return Settings()
