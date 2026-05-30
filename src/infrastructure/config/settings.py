"""Application configuration via pydantic-settings."""

from functools import lru_cache
from typing import Literal, Self

from pydantic import AliasChoices, Field, computed_field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

VectorStoreBackend = Literal["faiss", "qdrant", "pinecone"]


class Settings(BaseSettings):
    """Centralised, validated configuration loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="hybrid-chatbot-intelligent-routing", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    app_debug: bool = Field(default=False, alias="APP_DEBUG")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_json: bool = Field(default=False, alias="LOG_JSON")

    # Database — local dev defaults to SQLite (no Docker); Docker uses PostgreSQL via DATABASE_URL
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_user: str = Field(default="chatbot", alias="POSTGRES_USER")
    postgres_password: str = Field(default="chatbot_secret", alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(default="chatbot", alias="POSTGRES_DB")
    database_url: str | None = Field(default=None, alias="DATABASE_URL")
    sqlite_path: str = Field(default="data/local.db", alias="SQLITE_PATH")

    # LLM providers
    llm_provider: str = Field(default="auto", alias="LLM_PROVIDER")
    embedding_provider: str = Field(default="auto", alias="EMBEDDING_PROVIDER")
    llm_provider_priority: str = Field(
        default="openai,anthropic,google", alias="LLM_PROVIDER_PRIORITY"
    )

    # OpenAI
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    openai_embedding_model: str = Field(
        default="text-embedding-3-small", alias="OPENAI_EMBEDDING_MODEL"
    )

    # Anthropic
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(default="claude-3-5-haiku-latest", alias="ANTHROPIC_MODEL")

    # Google / Gemini
    google_api_key: str = Field(default="", alias="GOOGLE_API_KEY")
    google_model: str = Field(default="gemini-2.0-flash", alias="GOOGLE_MODEL")
    google_embedding_model: str = Field(
        default="models/text-embedding-004", alias="GOOGLE_EMBEDDING_MODEL"
    )

    # Vector store
    vector_store_backend: str = Field(default="faiss", alias="VECTOR_STORE_BACKEND")
    vector_top_k: int = Field(default=5, alias="VECTOR_TOP_K")
    faiss_index_path: str = Field(default="data/faiss", alias="FAISS_INDEX_PATH")
    qdrant_host: str = Field(default="localhost", alias="QDRANT_HOST")
    qdrant_port: int = Field(default=6333, alias="QDRANT_PORT")
    qdrant_url: str | None = Field(default=None, alias="QDRANT_URL")
    qdrant_collection: str = Field(default="documents", alias="QDRANT_COLLECTION")
    pinecone_api_key: str = Field(default="", alias="PINECONE_API_KEY")
    pinecone_index: str = Field(default="", alias="PINECONE_INDEX")
    pinecone_namespace: str = Field(default="", alias="PINECONE_NAMESPACE")

    # CORS (comma-separated origins; empty = none in production)
    cors_origins: str = Field(default="", alias="CORS_ORIGINS")

    # API rate limiting (/api/v1/chat)
    rate_limit_enabled: bool = Field(default=True, alias="RATE_LIMIT_ENABLED")
    rate_limit_requests: int = Field(default=10, alias="RATE_LIMIT_REQUESTS")
    rate_limit_window_seconds: int = Field(default=60, alias="RATE_LIMIT_WINDOW_SECONDS")

    # Routing
    classifier_confidence_threshold: float = Field(
        default=0.7, alias="CLASSIFIER_CONFIDENCE_THRESHOLD"
    )
    sql_pipeline_max_rows: int = Field(default=100, alias="SQL_PIPELINE_MAX_ROWS")
    conversation_history_limit: int = Field(default=10, alias="CONVERSATION_HISTORY_LIMIT")
    conversation_repository: str = Field(default="postgres", alias="CONVERSATION_REPOSITORY")

    # LangSmith tracing (opt-in)
    langsmith_tracing: bool = Field(default=False, alias="LANGSMITH_TRACING")
    langsmith_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("LANGSMITH_API_KEY", "LANGCHAIN_API_KEY"),
    )
    langsmith_project: str | None = Field(default=None, alias="LANGSMITH_PROJECT")
    langsmith_endpoint: str | None = Field(default=None, alias="LANGSMITH_ENDPOINT")
    langsmith_hide_inputs: bool = Field(default=False, alias="LANGSMITH_HIDE_INPUTS")
    langsmith_hide_outputs: bool = Field(default=False, alias="LANGSMITH_HIDE_OUTPUTS")
    langsmith_sampling_rate: float = Field(default=1.0, alias="LANGSMITH_SAMPLING_RATE")

    @field_validator("vector_store_backend")
    @classmethod
    def normalize_vector_backend(cls, value: str) -> str:
        return value.strip().lower()

    @model_validator(mode="after")
    def validate_vector_backend_config(self) -> Self:
        allowed: set[str] = {"faiss", "qdrant", "pinecone"}
        if self.vector_store_backend not in allowed:
            raise ValueError(
                f"VECTOR_STORE_BACKEND must be one of {sorted(allowed)}, "
                f"got {self.vector_store_backend!r}"
            )
        if self.vector_store_backend == "pinecone":
            if not self.pinecone_api_key.strip():
                raise ValueError("PINECONE_API_KEY is required when VECTOR_STORE_BACKEND=pinecone")
            if not self.pinecone_index.strip():
                raise ValueError("PINECONE_INDEX is required when VECTOR_STORE_BACKEND=pinecone")
        return self

    @computed_field  # type: ignore[prop-decorator]
    @property
    def async_database_url(self) -> str:
        if self.database_url:
            return str(self.database_url)
        # Docker Compose sets POSTGRES_HOST to the service name "postgres".
        if self.postgres_host == "postgres":
            return self._postgres_async_url()
        return f"sqlite+aiosqlite:///{self.sqlite_path}"

    def _postgres_async_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def is_sqlite(self) -> bool:
        return self.async_database_url.startswith("sqlite")

    @property
    def sql_dialect(self) -> str:
        return "SQLite" if self.is_sqlite else "PostgreSQL"

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def llm_priority_list(self) -> list[str]:
        return [p.strip().lower() for p in self.llm_provider_priority.split(",") if p.strip()]

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def langsmith_tracing_active(self) -> bool:
        return self.langsmith_tracing and bool(self.langsmith_api_key.strip())

    @property
    def langsmith_project_name(self) -> str:
        if self.langsmith_project and self.langsmith_project.strip():
            return self.langsmith_project.strip()
        return self.app_name


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
