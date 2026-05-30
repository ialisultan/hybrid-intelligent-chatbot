"""PostgreSQL-backed conversation history."""

from uuid import UUID, uuid4

import structlog
from sqlalchemy import select

from src.adapters.persistence.models import ConversationMessageRow
from src.application.ports.repository import ConversationRepositoryPort
from src.domain.entities.chat import ChatMessage
from src.infrastructure.database import get_session_factory

logger = structlog.get_logger(__name__)


class PostgresConversationRepository(ConversationRepositoryPort):
    """Persist conversation turns in PostgreSQL."""

    async def save_message(self, message: ChatMessage) -> None:
        row = ConversationMessageRow(
            id=uuid4(),
            conversation_id=message.conversation_id,
            role=message.role,
            content=message.content,
            created_at=message.created_at,
        )
        factory = get_session_factory()
        async with factory() as session:
            session.add(row)
            await session.commit()
        logger.debug(
            "conversation.saved",
            conversation_id=str(message.conversation_id),
            role=message.role,
        )

    async def get_history(self, conversation_id: UUID, limit: int = 10) -> list[ChatMessage]:
        factory = get_session_factory()
        stmt = (
            select(ConversationMessageRow)
            .where(ConversationMessageRow.conversation_id == conversation_id)
            .order_by(ConversationMessageRow.created_at.desc())
            .limit(limit)
        )
        async with factory() as session:
            result = await session.execute(stmt)
            rows = list(reversed(result.scalars().all()))

        return [
            ChatMessage(
                content=row.content,
                role=row.role,
                conversation_id=row.conversation_id,
                created_at=row.created_at,
            )
            for row in rows
        ]
