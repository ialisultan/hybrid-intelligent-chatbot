"""Postgres conversation repository tests."""

import asyncio
from uuid import uuid4

import pytest
from sqlalchemy import text

from src.adapters.repositories.postgres_conversation_repository import (
    PostgresConversationRepository,
)
from src.domain.entities.chat import ChatMessage
from src.infrastructure.config import get_settings
from src.infrastructure.database import (
    check_postgres_connection,
    create_engine,
    dispose_engine,
    get_session_factory,
)

pytestmark = pytest.mark.integration


async def _conversation_table_ready() -> bool:
    try:
        factory = get_session_factory()
        async with factory() as session:
            await session.execute(text("SELECT 1 FROM conversation_messages LIMIT 1"))
        return True
    except Exception:
        return False


@pytest.fixture
async def postgres_repo():
    settings = get_settings()
    get_settings.cache_clear()
    try:
        create_engine(settings)
        if not await check_postgres_connection():
            pytest.skip("Postgres not available")
        if not await _conversation_table_ready():
            pytest.skip("Run migrations first: make migrate or make local-init")
        repo = PostgresConversationRepository()
        yield repo
    finally:
        await dispose_engine()
        get_settings.cache_clear()


@pytest.mark.asyncio
async def test_postgres_save_and_get_history(postgres_repo):
    conversation_id = uuid4()
    await postgres_repo.save_message(
        ChatMessage(content="What is the return policy?", conversation_id=conversation_id)
    )
    await postgres_repo.save_message(
        ChatMessage(
            content="30-day returns apply.",
            role="assistant",
            conversation_id=conversation_id,
        )
    )

    history = await postgres_repo.get_history(conversation_id, limit=10)
    assert len(history) == 2
    assert history[0].role == "user"
    assert history[1].role == "assistant"
    assert "return policy" in history[0].content


@pytest.mark.asyncio
async def test_postgres_get_history_respects_limit(postgres_repo):
    conversation_id = uuid4()
    for i in range(5):
        await postgres_repo.save_message(
            ChatMessage(content=f"message {i}", conversation_id=conversation_id)
        )
        await asyncio.sleep(0.01)

    history = await postgres_repo.get_history(conversation_id, limit=3)
    assert len(history) == 3
    contents = [m.content for m in history]
    assert contents == ["message 2", "message 3", "message 4"]
