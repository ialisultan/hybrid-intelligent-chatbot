"""Conversation repository factory tests."""

import pytest

pytestmark = pytest.mark.unit

from src.adapters.repositories.conversation_repository import InMemoryConversationRepository
from src.adapters.repositories.factory import create_conversation_repository
from src.adapters.repositories.postgres_conversation_repository import (
    PostgresConversationRepository,
)
from src.infrastructure.config import Settings


def test_factory_returns_memory():
    settings = Settings(CONVERSATION_REPOSITORY="memory")
    repo = create_conversation_repository(settings)
    assert isinstance(repo, InMemoryConversationRepository)


def test_factory_returns_postgres():
    settings = Settings(CONVERSATION_REPOSITORY="postgres")
    repo = create_conversation_repository(settings)
    assert isinstance(repo, PostgresConversationRepository)


def test_factory_unknown_raises():
    settings = Settings(CONVERSATION_REPOSITORY="redis")
    with pytest.raises(ValueError, match="Unknown conversation repository"):
        create_conversation_repository(settings)
