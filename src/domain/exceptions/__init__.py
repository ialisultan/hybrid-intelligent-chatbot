"""Domain exceptions."""

from src.domain.exceptions.base import (
    ChatbotError,
    ClassificationError,
    DatabaseError,
    PipelineError,
    RoutingViolationError,
    VectorStoreError,
)

__all__ = [
    "ChatbotError",
    "ClassificationError",
    "DatabaseError",
    "PipelineError",
    "RoutingViolationError",
    "VectorStoreError",
]
