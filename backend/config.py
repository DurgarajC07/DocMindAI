"""Application configuration management."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "DocMind AI"
    app_version: str = "1.0.0"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    secret_key: str = Field(min_length=32)
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"]

    # Database
    database_url: str = "sqlite+aiosqlite:///./docmind.db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "mistral:7b-instruct-v0.3-q4_K_M"

    # Embeddings
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_device: Literal["cpu", "cuda", "mps"] = "cuda"

    # ChromaDB
    chroma_persist_dir: Path = Path("./data/chroma")
    chroma_collection_prefix: str = "business_"

    # File Upload
    upload_dir: Path = Path("./uploads")
    max_upload_size: int = 52428800  # 50MB
    allowed_extensions: list[str] = [".pdf", ".txt", ".doc", ".docx", ".html"]

    # JWT
    jwt_secret_key: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 10080  # 7 days

    # Rate Limiting
    rate_limit_enabled: bool = True

    # Plan Limits
    free_queries_per_month: int = 50
    free_max_documents: int = 1
    free_max_document_size: int = 5242880  # 5MB

    starter_queries_per_month: int = 1000
    starter_max_documents: int = 10
    starter_max_document_size: int = 10485760  # 10MB

    pro_queries_per_month: int = 10000
    pro_max_documents: int = 50
    pro_max_document_size: int = 52428800  # 50MB

    enterprise_queries_per_month: int = 999999
    enterprise_max_documents: int = 999999
    enterprise_max_document_size: int = 104857600  # 100MB

    # Logging
    log_level: str = "INFO"
    log_file: Path = Path("./logs/docmind.log")

    # API
    api_v1_prefix: str = "/api/v1"
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Parse CORS origins from comma-separated string or JSON list."""
        if isinstance(v, str):
            # If it's a string, try to parse as comma-separated
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v if isinstance(v, list) else [str(v)]

    @field_validator(
        "chroma_persist_dir", "upload_dir", "log_file", mode="before"
    )
    @classmethod
    def create_directories(cls, v: str | Path) -> Path:
        """Ensure directories exist."""
        path = Path(v)
        if path.suffix:  # It's a file
            path.parent.mkdir(parents=True, exist_ok=True)
        else:  # It's a directory
            path.mkdir(parents=True, exist_ok=True)
        return path

    def get_plan_limits(self, plan: str) -> dict[str, int]:
        """Get limits for a specific plan."""
        plan = plan.lower()
        return {
            "queries_per_month": getattr(self, f"{plan}_queries_per_month"),
            "max_documents": getattr(self, f"{plan}_max_documents"),
            "max_document_size": getattr(self, f"{plan}_max_document_size"),
        }


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
