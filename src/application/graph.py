"""LangGraph state machine — strict SQL vs Vector routing (no overlap)."""

from typing import Literal, TypedDict

import structlog
from langgraph.graph import END, START, StateGraph

from src.application.ports.classifier import ClassifierPort
from src.application.ports.sql_pipeline import SQLPipelinePort
from src.application.ports.vector_pipeline import VectorPipelinePort
from src.domain.entities.chat import RouteType
from src.domain.exceptions.base import RoutingViolationError

logger = structlog.get_logger(__name__)


class ChatState(TypedDict, total=False):
    query: str
    conversation_id: str
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
):
    """Build the LangGraph with strict routing — each path is mutually exclusive."""

    async def classify_node(state: ChatState) -> ChatState:
        result = await classifier.classify(state["query"])
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
        logger.info("graph.sql_pipeline.start", query=state["query"][:80])
        result = await sql_pipeline.run(state["query"])
        return {
            **state,
            "answer": result["answer"],
            "sql_query": result.get("sql_query"),
            "sources": [],
        }

    async def vector_node(state: ChatState) -> ChatState:
        logger.info("graph.vector_pipeline.start", query=state["query"][:80])
        result = await vector_pipeline.run(state["query"])
        return {
            **state,
            "answer": result["answer"],
            "sources": result.get("sources", []),
            "sql_query": None,
        }

    builder = StateGraph(ChatState)
    builder.add_node("classify", classify_node)
    builder.add_node("sql_pipeline", sql_node)
    builder.add_node("vector_pipeline", vector_node)

    builder.add_edge(START, "classify")
    builder.add_conditional_edges("classify", route_query)
    builder.add_edge("sql_pipeline", END)
    builder.add_edge("vector_pipeline", END)

    return builder.compile()
