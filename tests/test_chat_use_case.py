"""ChatUseCase unit tests."""

from uuid import uuid4

import pytest

from src.adapters.repositories.conversation_repository import InMemoryConversationRepository
from src.application.graph import build_chat_graph
from src.application.orchestrator import ChatOrchestrator
from src.application.usecases.chat import ChatUseCase
from src.domain.entities.chat import QueryRoute, RouteType

pytestmark = pytest.mark.unit


class FixedVectorClassifier:
    async def classify(self, query: str, *, config=None) -> QueryRoute:
        return QueryRoute(route=RouteType.VECTOR, confidence=0.9, reasoning="test")


class StubVectorPipeline:
    async def run(self, query: str, *, config=None) -> dict:
        return {"answer": "Assistant reply", "sources": ["faq.md"]}


class StubSQLPipeline:
    async def run(self, query: str, *, config=None) -> dict:
        return {"answer": "SQL reply", "sql_query": "SELECT 1"}


@pytest.fixture
def use_case():
    graph = build_chat_graph(
        classifier=FixedVectorClassifier(),
        sql_pipeline=StubSQLPipeline(),
        vector_pipeline=StubVectorPipeline(),
    )
    repo = InMemoryConversationRepository()
    orchestrator = ChatOrchestrator(graph=graph)
    return ChatUseCase(orchestrator=orchestrator, conversation_repo=repo), repo


@pytest.mark.asyncio
async def test_use_case_saves_user_and_assistant_messages(use_case):
    chat_use_case, repo = use_case
    conversation_id = uuid4()

    response = await chat_use_case.execute(
        query="What is the return policy?",
        conversation_id=conversation_id,
    )

    history = await repo.get_history(conversation_id)
    assert len(history) == 2
    assert history[0].role == "user"
    assert history[0].content == "What is the return policy?"
    assert history[1].role == "assistant"
    assert history[1].content == "Assistant reply"
    assert response.conversation_id == conversation_id
    assert response.route == RouteType.VECTOR
