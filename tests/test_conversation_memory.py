"""Conversation memory tests — multi-turn context in LangGraph."""

from uuid import uuid4

import pytest

pytestmark = pytest.mark.unit

from src.adapters.repositories.conversation_repository import InMemoryConversationRepository
from src.application.context import build_contextual_query, filter_current_turn
from src.application.graph import build_chat_graph
from src.domain.entities.chat import ChatMessage, QueryRoute, RouteType


class RecordingClassifier:
    def __init__(self) -> None:
        self.last_query: str = ""

    async def classify(self, query: str) -> QueryRoute:
        self.last_query = query
        return QueryRoute(route=RouteType.VECTOR, confidence=0.9, reasoning="test")


class RecordingVectorPipeline:
    def __init__(self) -> None:
        self.last_query: str = ""

    async def run(self, query: str) -> dict:
        self.last_query = query
        return {"answer": f"Vector answer for: {query}", "sources": ["faq.md"]}


class RecordingSQLPipeline:
    async def run(self, query: str) -> dict:
        return {"answer": f"SQL answer for: {query}", "sql_query": "SELECT 1"}


def test_build_contextual_query_includes_history():
    messages = [
        {"role": "user", "content": "What is the return policy?"},
        {"role": "assistant", "content": "30-day returns apply."},
    ]
    result = build_contextual_query("What about warranty?", messages)
    assert "return policy" in result
    assert "30-day returns" in result
    assert "What about warranty?" in result


def test_build_contextual_query_no_history_returns_query():
    assert build_contextual_query("Hello", []) == "Hello"


def test_filter_current_turn_excludes_matching_last_user_message():
    messages = [
        {"role": "user", "content": "prior question"},
        {"role": "assistant", "content": "prior answer"},
        {"role": "user", "content": "current question"},
    ]
    filtered = filter_current_turn(messages, "current question")
    assert len(filtered) == 2
    assert filtered[-1]["content"] == "prior answer"


@pytest.mark.asyncio
async def test_graph_loads_history_and_passes_context_to_pipeline():
    repo = InMemoryConversationRepository()
    conversation_id = uuid4()

    await repo.save_message(
        ChatMessage(content="What is the return policy?", conversation_id=conversation_id)
    )
    await repo.save_message(
        ChatMessage(
            content="30-day returns apply.",
            role="assistant",
            conversation_id=conversation_id,
        )
    )
    await repo.save_message(
        ChatMessage(content="What about warranty?", conversation_id=conversation_id)
    )

    classifier = RecordingClassifier()
    vector_pipeline = RecordingVectorPipeline()

    graph = build_chat_graph(
        classifier=classifier,
        sql_pipeline=RecordingSQLPipeline(),
        vector_pipeline=vector_pipeline,
        conversation_repo=repo,
        history_limit=10,
    )

    state = await graph.ainvoke(
        {
            "query": "What about warranty?",
            "conversation_id": str(conversation_id),
        }
    )

    assert len(state["messages"]) == 2
    assert "return policy" in state["contextual_query"]
    assert "30-day returns" in classifier.last_query
    assert "return policy" in vector_pipeline.last_query
    assert state["route"] == "vector"
    assert state["sql_query"] is None


@pytest.mark.asyncio
async def test_graph_follow_up_includes_prior_turn_in_classifier_input():
    """Multi-turn: classifier receives contextual query built from Postgres/history."""
    repo = InMemoryConversationRepository()
    classifier = RecordingClassifier()
    vector_pipeline = RecordingVectorPipeline()

    graph = build_chat_graph(
        classifier=classifier,
        sql_pipeline=RecordingSQLPipeline(),
        vector_pipeline=vector_pipeline,
        conversation_repo=repo,
        history_limit=10,
    )

    conversation_id = uuid4()
    await repo.save_message(
        ChatMessage(content="What is the return policy?", conversation_id=conversation_id)
    )
    await repo.save_message(
        ChatMessage(
            content="30-day returns apply.",
            role="assistant",
            conversation_id=conversation_id,
        )
    )

    await graph.ainvoke(
        {
            "query": "What about warranty?",
            "conversation_id": str(conversation_id),
        }
    )

    assert "return policy" in classifier.last_query
    assert "What about warranty?" in classifier.last_query
    assert "warranty" in vector_pipeline.last_query.lower() or "Warranty" in vector_pipeline.last_query


@pytest.mark.asyncio
async def test_graph_without_repo_uses_raw_query():
    classifier = RecordingClassifier()
    vector_pipeline = RecordingVectorPipeline()

    graph = build_chat_graph(
        classifier=classifier,
        sql_pipeline=RecordingSQLPipeline(),
        vector_pipeline=vector_pipeline,
    )

    await graph.ainvoke({"query": "What is your return policy?", "conversation_id": "1"})

    assert classifier.last_query == "What is your return policy?"
    assert vector_pipeline.last_query == "What is your return policy?"
