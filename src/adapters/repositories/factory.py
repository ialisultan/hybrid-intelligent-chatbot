"""Conversation repository factory."""

from src.adapters.repositories.conversation_repository import InMemoryConversationRepository
from src.adapters.repositories.postgres_conversation_repository import (
    PostgresConversationRepository,
)
from src.application.ports.repository import ConversationRepositoryPort
from src.infrastructure.config import Settings


def create_conversation_repository(settings: Settings) -> ConversationRepositoryPort:
    """Select in-memory or Postgres conversation storage."""
    backend = settings.conversation_repository.lower()
    if backend == "memory":
        return InMemoryConversationRepository()
    if backend == "postgres":
        return PostgresConversationRepository()
    raise ValueError(f"Unknown conversation repository backend: {backend}")
