"""Conversation repository port."""

from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.chat import ChatMessage


class ConversationRepositoryPort(ABC):
    """Persist and retrieve conversation history."""

    @abstractmethod
    async def save_message(self, message: ChatMessage) -> None:
        ...

    @abstractmethod
    async def get_history(self, conversation_id: UUID, limit: int = 10) -> list[ChatMessage]:
        ...
