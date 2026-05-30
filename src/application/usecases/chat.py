"""Chat use case — entry point for query processing."""

from uuid import UUID, uuid4

import structlog

from src.application.orchestrator import ChatOrchestrator
from src.domain.entities.chat import ChatMessage, ChatResponse

logger = structlog.get_logger(__name__)


class ChatUseCase:
    """Process a user message through classification and strict routing."""

    def __init__(self, orchestrator: ChatOrchestrator) -> None:
        self._orchestrator = orchestrator

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
        response = await self._orchestrator.process(message)
        logger.info(
            "chat.usecase.complete",
            route=response.route.value,
            confidence=response.confidence,
        )
        return response
