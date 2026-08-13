from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    APP_NAME: str = "ContractLens AI"
    ENV: Literal["local", "test", "staging", "production"] = "local"
    DEBUG: bool = True
    API_PREFIX: str = "/api"

    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # Database
    DATABASE_URL: str = (
        "postgresql+asyncpg://contractlens:contractlens@localhost:5433/contractlens"
    )

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Object storage
    STORAGE_BACKEND: Literal["local", "s3"] = "local"
    STORAGE_LOCAL_PATH: str = "./storage"
    S3_BUCKET: str = "contractlens-documents"
    S3_REGION: str = "us-east-1"
    S3_ENDPOINT_URL: str | None = None
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None

    # Uploads
    MAX_UPLOAD_SIZE_MB: int = 25
    ALLOWED_UPLOAD_MIME_TYPES: list[str] = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
    ]

    # AI providers (abstracted; demo mode used when keys absent)
    LLM_PROVIDER: Literal["openai", "anthropic", "mock"] = "mock"
    LLM_MODEL: str = "gpt-4o-mini"
    EMBEDDING_PROVIDER: Literal["openai", "mock"] = "mock"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSIONS: int = 1536
    RERANKER_PROVIDER: Literal["cohere", "mock"] = "mock"
    RERANKER_MODEL: str = "rerank-english-v3.0"
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    COHERE_API_KEY: str | None = None

    # Observability
    LANGFUSE_PUBLIC_KEY: str | None = None
    LANGFUSE_SECRET_KEY: str | None = None
    LANGFUSE_HOST: str = "http://localhost:3001"

    # Prompts (resolved relative to the process working directory; the
    # Docker Compose api service overrides this to an absolute path since
    # its working directory differs from local dev).
    PROMPTS_DIR: str = "../../prompts"

    # Retrieval
    RETRIEVAL_CANDIDATE_POOL_SIZE: int = 20
    RETRIEVAL_TOP_K: int = 5
    EVIDENCE_THRESHOLD: float = 0.15

    # Budgets
    MAX_LATENCY_MS: int = 8000
    MAX_INPUT_TOKENS: int = 12000
    MAX_OUTPUT_TOKENS: int = 3000
    MAX_COST_PER_REQUEST: float = 0.10

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    @property
    def is_demo_mode(self) -> bool:
        return self.LLM_PROVIDER == "mock"


@lru_cache
def get_settings() -> Settings:
    return Settings()
