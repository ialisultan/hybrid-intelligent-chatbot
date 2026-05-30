"""Health check response schemas."""

from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Liveness probe response."""

    status: Literal["ok"] = "ok"
    chat_provider: str = Field(description="Active chat LLM provider")
    embedding_provider: str = Field(description="Active embedding provider")
    vector_backend: str = Field(description="Configured vector store backend")


class ReadyResponse(BaseModel):
    """Readiness probe response."""

    status: Literal["ready", "degraded"]
    postgres: Literal["ok", "down"]
    vector: Literal["ok", "down", "skipped"]
    chat_provider: str
    embedding_provider: str
    vector_backend: str
