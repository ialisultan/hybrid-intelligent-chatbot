"""ChatOrchestrator unit tests."""

from uuid import uuid4

import pytest

from src.application.graph import build_chat_graph
from src.application.orchestrator import ChatOrchestrator
from src.domain.entities.chat import ChatMessage, QueryRoute, RouteType
from src.domain.exceptions.base import ClassificationError

pytestmark = pytest.mark.unit


class FixedClassifier:
    async def classify(self, query: str) -> QueryRoute:
        return QueryRoute(route=RouteType.SQL, confidence=0.9, reasoning="test")


class RecordingSQLPipeline:
    async def run(self, query: str) -> dict:
        return {"answer": "SQL result", "sql_query": "SELECT 1"}


class RecordingVectorPipeline:
    async def run(self, query: str) -> dict:
        return {"answer": "Vector result", "sources": ["doc.md"]}


@pytest.mark.asyncio
async def test_orchestrator_maps_graph_state_to_response():
    graph = build_chat_graph(
        classifier=FixedClassifier(),
        sql_pipeline=RecordingSQLPipeline(),
        vector_pipeline=RecordingVectorPipeline(),
    )
    orchestrator = ChatOrchestrator(graph=graph)
    conversation_id = uuid4()

    response = await orchestrator.process(
        ChatMessage(content="Total revenue?", conversation_id=conversation_id)
    )

    assert response.answer == "SQL result"
    assert response.route == RouteType.SQL
    assert response.confidence == 0.9
    assert response.sql_query == "SELECT 1"
    assert response.sources == []
    assert response.conversation_id == conversation_id


@pytest.mark.asyncio
async def test_orchestrator_raises_when_classification_missing():
    class MockGraph:
        async def ainvoke(self, _state):
            return {"confidence": 0.0}

    orchestrator = ChatOrchestrator(graph=MockGraph())

    with pytest.raises(ClassificationError):
        await orchestrator.process(ChatMessage(content="test"))
