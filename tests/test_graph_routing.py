"""LangGraph routing tests — strict SQL vs Vector separation."""

import pytest

from src.application.graph import build_chat_graph
from src.domain.entities.chat import QueryRoute, RouteType

pytestmark = pytest.mark.unit


class FixedClassifier:
    def __init__(self, route: RouteType) -> None:
        self._route = route

    async def classify(self, query: str) -> QueryRoute:
        return QueryRoute(route=self._route, confidence=0.95, reasoning="test")


class RecordingSQLPipeline:
    async def run(self, query: str) -> dict:
        return {"answer": f"SQL answer for: {query}", "sql_query": "SELECT 1"}


class RecordingVectorPipeline:
    async def run(self, query: str) -> dict:
        return {"answer": f"Vector answer for: {query}", "sources": ["faq.md"]}


@pytest.mark.asyncio
async def test_graph_routes_to_sql_pipeline():
    graph = build_chat_graph(
        classifier=FixedClassifier(RouteType.SQL),
        sql_pipeline=RecordingSQLPipeline(),
        vector_pipeline=RecordingVectorPipeline(),
    )
    state = await graph.ainvoke({"query": "Total revenue this month?", "conversation_id": "1"})

    assert state["route"] == "sql"
    assert "SQL answer" in state["answer"]
    assert state["sql_query"] == "SELECT 1"
    assert state["sources"] == []


@pytest.mark.asyncio
async def test_graph_routes_to_vector_pipeline():
    graph = build_chat_graph(
        classifier=FixedClassifier(RouteType.VECTOR),
        sql_pipeline=RecordingSQLPipeline(),
        vector_pipeline=RecordingVectorPipeline(),
    )
    state = await graph.ainvoke({"query": "What is your return policy?", "conversation_id": "2"})

    assert state["route"] == "vector"
    assert "Vector answer" in state["answer"]
    assert state["sources"] == ["faq.md"]
    assert state["sql_query"] is None
