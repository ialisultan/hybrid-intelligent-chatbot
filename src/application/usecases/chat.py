"""Chat use case — entry point for query processing."""

from uuid import UUID, uuid4

import structlog

from src.application.orchestrator import ChatOrchestrator
from src.application.ports.repository import ConversationRepositoryPort
from src.domain.entities.chat import ChatMessage, ChatResponse

logger = structlog.get_logger(__name__)


class ChatUseCase:
    """Process a user message through classification and strict routing."""

    def __init__(
        self,
        orchestrator: ChatOrchestrator,
        conversation_repo: ConversationRepositoryPort | None = None,
    ) -> None:
        self._orchestrator = orchestrator
        self._conversation_repo = conversation_repo

    async def execute(
        self,
        query: str,
        conversation_id: UUID | None = None,
    ) -> ChatResponse:
        message = ChatMessage(content=query, conversation_id=conversation_id or uuid4())
        logger.info(
            "chat.usecase.start",
            query_length=len(query),
            conversation_id=str(message.conversation_id),
        )

        if self._conversation_repo:
            await self._conversation_repo.save_message(message)

        response = await self._orchestrator.process(message)

        if self._conversation_repo and response.conversation_id:
            await self._conversation_repo.save_message(
                ChatMessage(
                    content=response.answer,
                    role="assistant",
                    conversation_id=response.conversation_id,
                )
            )

        logger.info(
            "chat.usecase.complete",
            route=response.route.value,
            confidence=response.confidence,
        )
        return response
