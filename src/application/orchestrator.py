"""High-level orchestrator — delegates to LangGraph pipeline."""

from uuid import uuid4

import structlog

from src.application.graph import build_chat_graph
from src.application.ports.classifier import ClassifierPort
from src.application.ports.repository import ConversationRepositoryPort
from src.application.ports.sql_pipeline import SQLPipelinePort
from src.application.ports.vector_pipeline import VectorPipelinePort
from src.domain.entities.chat import ChatMessage, ChatResponse, RouteType
from src.domain.exceptions.base import ClassificationError

logger = structlog.get_logger(__name__)


class ChatOrchestrator:
    """Coordinates query classification and strict pipeline routing via LangGraph."""

    def __init__(self, graph) -> None:
        self._graph = graph

    async def process(self, message: ChatMessage) -> ChatResponse:
        conversation_id = message.conversation_id or uuid4()
        logger.info(
            "orchestrator.process.start",
            conversation_id=str(conversation_id),
        )

        state = await self._graph.ainvoke(
            {
                "query": message.content,
                "conversation_id": str(conversation_id),
            }
        )

        route_value = state.get("route")
        if not route_value:
            raise ClassificationError("Query could not be classified")

        return ChatResponse(
            answer=state.get("answer", ""),
            route=RouteType(route_value),
            confidence=float(state.get("confidence", 0.0)),
            sources=state.get("sources", []),
            sql_query=state.get("sql_query"),
            conversation_id=conversation_id,
        )


def create_orchestrator(
    classifier: ClassifierPort,
    sql_pipeline: SQLPipelinePort,
    vector_pipeline: VectorPipelinePort,
    conversation_repo: ConversationRepositoryPort | None = None,
    history_limit: int = 10,
) -> ChatOrchestrator:
    """Factory — wire dependencies into the LangGraph orchestrator."""
    graph = build_chat_graph(
        classifier=classifier,
        sql_pipeline=sql_pipeline,
        vector_pipeline=vector_pipeline,
        conversation_repo=conversation_repo,
        history_limit=history_limit,
    )
    return ChatOrchestrator(graph=graph)
