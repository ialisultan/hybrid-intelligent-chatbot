"""Health check response schemas."""

from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Liveness probe response."""

    status: Literal["ok"] = "ok"
    chat_provider: str = Field(description="Active chat LLM provider")
    embedding_provider: str = Field(description="Active embedding provider")


class ReadyResponse(BaseModel):
    """Readiness probe response."""

    status: Literal["ready", "degraded"]
    postgres: Literal["ok", "down"]
    chat_provider: str
    embedding_provider: str
