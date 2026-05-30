"""Chat API request/response schemas."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.domain.entities.chat import RouteType


class QuerySchema(BaseModel):
    """Validated user query input."""

    text: str = Field(..., min_length=1, max_length=4000, description="Natural language question")

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"text": "What is the total revenue this month?"}]}
    )


class ChatRequest(BaseModel):
    """Incoming chat message."""

    query: str = Field(..., min_length=1, max_length=4000, description="User question")
    conversation_id: UUID | None = Field(default=None, description="Optional conversation ID")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "query": "What is the total revenue this month?",
                    "conversation_id": None,
                }
            ]
        }
    )


class ChatResponseSchema(BaseModel):
    """Chat response returned to the client."""

    answer: str
    route: RouteType
    confidence: float = Field(ge=0.0, le=1.0)
    sources: list[str] = Field(default_factory=list)
    sql_query: str | None = None
    conversation_id: UUID | None = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "answer": "Total revenue this month is $12,450.",
                    "route": "sql",
                    "confidence": 0.92,
                    "sources": [],
                    "sql_query": "SELECT SUM(amount) FROM orders WHERE ...",
                    "conversation_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                }
            ]
        },
    )
