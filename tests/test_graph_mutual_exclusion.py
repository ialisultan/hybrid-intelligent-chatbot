"""LangGraph invokes exactly one pipeline per query with valid output contracts."""

import pytest

from src.adapters.llm.rule_classifier import RuleBasedClassifier
from src.application.graph import build_chat_graph
from src.domain.entities.chat import RouteType

pytestmark = pytest.mark.unit


class RecordingSQLPipeline:
    called = False

    async def run(self, query: str, *, config=None) -> dict:
        RecordingSQLPipeline.called = True
        return {"answer": f"SQL: {query}", "sql_query": "SELECT 1"}


class RecordingVectorPipeline:
    called = False

    async def run(self, query: str, *, config=None) -> dict:
        RecordingVectorPipeline.called = True
        return {"answer": f"Vector: {query}", "sources": ["doc.md"]}


@pytest.fixture
def recording_graph():
    RecordingSQLPipeline.called = False
    RecordingVectorPipeline.called = False
    return build_chat_graph(
        classifier=RuleBasedClassifier(),
        sql_pipeline=RecordingSQLPipeline(),
        vector_pipeline=RecordingVectorPipeline(),
    )


@pytest.mark.asyncio
async def test_sql_query_invokes_only_sql_pipeline(recording_graph):
    state = await recording_graph.ainvoke(
        {"query": "Total revenue this month?", "conversation_id": "x"}
    )
    assert state["route"] == RouteType.SQL.value
    assert RecordingSQLPipeline.called
    assert not RecordingVectorPipeline.called
    assert state["sources"] == []
    assert state["sql_query"] == "SELECT 1"


@pytest.mark.asyncio
async def test_vector_query_invokes_only_vector_pipeline(recording_graph):
    state = await recording_graph.ainvoke(
        {"query": "Tell me about orders policy", "conversation_id": "x"}
    )
    assert state["route"] == RouteType.VECTOR.value
    assert RecordingVectorPipeline.called
    assert not RecordingSQLPipeline.called
    assert state["sql_query"] is None
    assert state["sources"] == ["doc.md"]
