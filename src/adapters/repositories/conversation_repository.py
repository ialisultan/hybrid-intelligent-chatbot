"""In-memory conversation repository stub."""

from uuid import UUID

from src.application.ports.repository import ConversationRepositoryPort
from src.domain.entities.chat import ChatMessage


class InMemoryConversationRepository(ConversationRepositoryPort):
    """Stub repository — stores messages in process memory."""

    def __init__(self) -> None:
        self._store: dict[UUID, list[ChatMessage]] = {}

    async def save_message(self, message: ChatMessage) -> None:
        history = self._store.setdefault(message.conversation_id, [])
        history.append(message)

    async def get_history(self, conversation_id: UUID, limit: int = 10) -> list[ChatMessage]:
        history = self._store.get(conversation_id, [])
        return history[-limit:]
