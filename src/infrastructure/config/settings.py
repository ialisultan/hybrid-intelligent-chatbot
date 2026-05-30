"""Application configuration via pydantic-settings."""

from functools import lru_cache

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


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

    # Database
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_user: str = Field(default="chatbot", alias="POSTGRES_USER")
    postgres_password: str = Field(default="chatbot_secret", alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(default="chatbot", alias="POSTGRES_DB")
    database_url: str | None = Field(default=None, alias="DATABASE_URL")

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

    # Routing
    classifier_confidence_threshold: float = Field(
        default=0.7, alias="CLASSIFIER_CONFIDENCE_THRESHOLD"
    )
    sql_pipeline_max_rows: int = Field(default=100, alias="SQL_PIPELINE_MAX_ROWS")
    conversation_history_limit: int = Field(default=10, alias="CONVERSATION_HISTORY_LIMIT")
    conversation_repository: str = Field(default="postgres", alias="CONVERSATION_REPOSITORY")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def async_database_url(self) -> str:
        if self.database_url:
            return str(self.database_url)
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def llm_priority_list(self) -> list[str]:
        return [p.strip().lower() for p in self.llm_provider_priority.split(",") if p.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
