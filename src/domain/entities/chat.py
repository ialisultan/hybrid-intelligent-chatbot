"""Domain entity models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4


class RouteType(StrEnum):
    """Strict routing destinations — SQL and VECTOR must never overlap."""

    SQL = "sql"
    VECTOR = "vector"


@dataclass(frozen=True, slots=True)
class QueryRoute:
    """Classification result for an incoming user query."""

    route: RouteType
    confidence: float
    reasoning: str = ""


@dataclass(frozen=True, slots=True)
class ChatMessage:
    """A single message in a conversation."""

    content: str
    role: str = "user"
    conversation_id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True, slots=True)
class ChatResponse:
    """Final response returned to the caller."""

    answer: str
    route: RouteType
    confidence: float
    sources: list[str] = field(default_factory=list)
    sql_query: str | None = None
    conversation_id: UUID | None = None
