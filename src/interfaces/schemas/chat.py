"""Chat API request/response schemas."""

from uuid import UUID

from pydantic import BaseModel, Field

from src.domain.entities.chat import RouteType


class ChatRequest(BaseModel):
    """Incoming chat message."""

    query: str = Field(..., min_length=1, max_length=4000, description="User question")
    conversation_id: UUID | None = Field(default=None, description="Optional conversation ID")


class ChatResponseSchema(BaseModel):
    """Chat response returned to the client."""

    answer: str
    route: RouteType
    confidence: float = Field(ge=0.0, le=1.0)
    sources: list[str] = Field(default_factory=list)
    sql_query: str | None = None
    conversation_id: UUID | None = None

    model_config = {"from_attributes": True}
