"""LangGraph assessment matrix — all README demo queries end-to-end."""

import pytest

from src.adapters.llm.rule_classifier import RuleBasedClassifier
from src.application.graph import build_chat_graph
from src.domain.entities.chat import RouteType

pytestmark = pytest.mark.unit

ASSESSMENT_CASES = [
    ("Total revenue this month?", RouteType.SQL),
    ("Top 5 customers by spending", RouteType.SQL),
    ("Orders placed in the last 7 days", RouteType.SQL),
    ("What is your return policy?", RouteType.VECTOR),
    ("Explain product features", RouteType.VECTOR),
    ("Tell me about orders policy", RouteType.VECTOR),
    ("Customers refund issues", RouteType.VECTOR),
]


class RecordingSQLPipeline:
    async def run(self, query: str, *, config=None) -> dict:
        return {"answer": f"SQL answer for: {query}", "sql_query": "SELECT 1"}


class RecordingVectorPipeline:
    async def run(self, query: str, *, config=None) -> dict:
        return {"answer": f"Vector answer for: {query}", "sources": ["faq_support.md"]}


@pytest.fixture
def assessment_graph():
    return build_chat_graph(
        classifier=RuleBasedClassifier(),
        sql_pipeline=RecordingSQLPipeline(),
        vector_pipeline=RecordingVectorPipeline(),
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("query,expected", ASSESSMENT_CASES)
async def test_graph_assessment_routing(assessment_graph, query, expected):
    state = await assessment_graph.ainvoke({"query": query, "conversation_id": "test-id"})

    assert state["route"] == expected.value

    if expected == RouteType.SQL:
        assert "SQL answer" in state["answer"]
        assert state["sql_query"] == "SELECT 1"
        assert state["sources"] == []
    else:
        assert "Vector answer" in state["answer"]
        assert state["sql_query"] is None
        assert state["sources"] == ["faq_support.md"]
