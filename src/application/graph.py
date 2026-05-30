"""LangGraph state machine — strict SQL vs Vector routing (no overlap).

Flow: START → load_history → classify → [sql_pipeline | vector_pipeline] → END

Each query follows exactly one pipeline. The SQL node never returns sources;
the vector node never returns a sql_query.
"""

from typing import Literal, TypedDict
from uuid import UUID

import structlog
from langgraph.graph import END, START, StateGraph

from src.application.context import (
    build_contextual_query,
    filter_current_turn,
    serialize_messages,
)
from src.application.ports.classifier import ClassifierPort
from src.application.ports.repository import ConversationRepositoryPort
from src.application.ports.sql_pipeline import SQLPipelinePort
from src.application.ports.vector_pipeline import VectorPipelinePort
from src.application.routing.contracts import validate_pipeline_output
from src.domain.entities.chat import RouteType
from src.domain.exceptions.base import RoutingViolationError

logger = structlog.get_logger(__name__)


class ChatState(TypedDict, total=False):
    query: str
    conversation_id: str
    messages: list[dict]
    contextual_query: str
    route: str
    confidence: float
    reasoning: str
    answer: str
    sources: list[str]
    sql_query: str | None


def build_chat_graph(
    classifier: ClassifierPort,
    sql_pipeline: SQLPipelinePort,
    vector_pipeline: VectorPipelinePort,
    conversation_repo: ConversationRepositoryPort | None = None,
    history_limit: int = 10,
):
    """Build the LangGraph with strict routing — each path is mutually exclusive."""

    async def load_history_node(state: ChatState) -> ChatState:
        query = state["query"]
        messages: list[dict] = []

        if conversation_repo and state.get("conversation_id"):
            try:
                conversation_id = UUID(state["conversation_id"])
                history = await conversation_repo.get_history(
                    conversation_id, limit=history_limit
                )
                messages = serialize_messages(history)
                messages = filter_current_turn(messages, query)
            except (ValueError, TypeError) as exc:
                logger.warning("graph.load_history.invalid_id", error=str(exc))

        contextual_query = build_contextual_query(query, messages)
        logger.info(
            "graph.load_history",
            prior_turns=len(messages),
            has_context=contextual_query != query,
        )
        return {
            **state,
            "messages": messages,
            "contextual_query": contextual_query,
        }

    async def classify_node(state: ChatState) -> ChatState:
        contextual_query = state.get("contextual_query") or state["query"]
        result = await classifier.classify(contextual_query)
        logger.info(
            "graph.classify",
            route=result.route.value,
            confidence=result.confidence,
        )
        return {
            **state,
            "route": result.route.value,
            "confidence": result.confidence,
            "reasoning": result.reasoning,
        }

    def route_query(state: ChatState) -> Literal["sql_pipeline", "vector_pipeline"]:
        route = state.get("route")
        if route == RouteType.SQL.value:
            return "sql_pipeline"
        if route == RouteType.VECTOR.value:
            return "vector_pipeline"
        raise RoutingViolationError(f"Unknown route: {route}")

    async def sql_node(state: ChatState) -> ChatState:
        contextual_query = state.get("contextual_query") or state["query"]
        logger.info("graph.sql_pipeline.start", query=contextual_query[:80])
        result = await sql_pipeline.run(contextual_query)
        sources: list[str] = []
        sql_query = result.get("sql_query")
        validate_pipeline_output(
            RouteType.SQL.value,
            sources=sources,
            sql_query=sql_query,
        )
        return {
            **state,
            "answer": result["answer"],
            "sql_query": sql_query,
            "sources": sources,
        }

    async def vector_node(state: ChatState) -> ChatState:
        contextual_query = state.get("contextual_query") or state["query"]
        logger.info("graph.vector_pipeline.start", query=contextual_query[:80])
        result = await vector_pipeline.run(contextual_query)
        sources = result.get("sources", [])
        sql_query = None
        validate_pipeline_output(
            RouteType.VECTOR.value,
            sources=sources,
            sql_query=sql_query,
        )
        return {
            **state,
            "answer": result["answer"],
            "sources": sources,
            "sql_query": sql_query,
        }

    builder = StateGraph(ChatState)
    builder.add_node("load_history", load_history_node)
    builder.add_node("classify", classify_node)
    builder.add_node("sql_pipeline", sql_node)
    builder.add_node("vector_pipeline", vector_node)

    builder.add_edge(START, "load_history")
    builder.add_edge("load_history", "classify")
    builder.add_conditional_edges("classify", route_query)
    builder.add_edge("sql_pipeline", END)
    builder.add_edge("vector_pipeline", END)

    return builder.compile()
