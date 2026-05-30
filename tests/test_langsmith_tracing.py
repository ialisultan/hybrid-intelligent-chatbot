"""LangSmith tracing configuration tests."""

import os
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.application.orchestrator import ChatOrchestrator, create_orchestrator
from src.domain.entities.chat import ChatMessage, RouteType
from src.infrastructure.config.settings import Settings
from src.infrastructure.logging import bind_request_context
from src.infrastructure.tracing.langsmith import (
    build_child_run_config,
    build_graph_invoke_config,
    configure_langsmith,
    make_graph_invoke_config_builder,
)

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def _clear_tracing_env(monkeypatch):
    """Reset tracing-related env vars between tests."""
    for key in (
        "LANGCHAIN_TRACING_V2",
        "LANGCHAIN_API_KEY",
        "LANGCHAIN_PROJECT",
        "LANGSMITH_TRACING",
        "LANGSMITH_API_KEY",
        "LANGSMITH_PROJECT",
    ):
        monkeypatch.delenv(key, raising=False)


def test_configure_langsmith_enables_env_when_active(monkeypatch):
    settings = Settings(
        _env_file=None,
        LANGSMITH_TRACING=True,
        LANGSMITH_API_KEY="ls-test-key",
        LANGSMITH_PROJECT="test-project",
        APP_ENV="development",
    )
    configure_langsmith(settings)

    assert os.environ["LANGCHAIN_TRACING_V2"] == "true"
    assert os.environ["LANGCHAIN_API_KEY"] == "ls-test-key"
    assert os.environ["LANGCHAIN_PROJECT"] == "test-project"
    assert os.environ["LANGSMITH_TRACING"] == "true"
    assert os.environ["LANGSMITH_API_KEY"] == "ls-test-key"
    assert os.environ["LANGSMITH_PROJECT"] == "test-project"


def test_configure_langsmith_disables_when_inactive(monkeypatch):
    monkeypatch.setenv("LANGCHAIN_TRACING_V2", "true")
    monkeypatch.setenv("LANGSMITH_API_KEY", "stale-key")

    settings = Settings(
        _env_file=None,
        LANGSMITH_TRACING=False,
        LANGSMITH_API_KEY="",
    )
    configure_langsmith(settings)

    assert os.environ["LANGCHAIN_TRACING_V2"] == "false"
    assert os.environ["LANGSMITH_TRACING"] == "false"
    assert "LANGSMITH_API_KEY" not in os.environ


def test_configure_langsmith_disables_when_key_missing(monkeypatch):
    settings = Settings(
        _env_file=None,
        LANGSMITH_TRACING=True,
        LANGSMITH_API_KEY="",
    )
    configure_langsmith(settings)

    assert os.environ["LANGCHAIN_TRACING_V2"] == "false"
    assert os.environ["LANGSMITH_TRACING"] == "false"


def test_build_graph_invoke_config_includes_thread_metadata():
    request_id = "test-request-123"
    bind_request_context(request_id)
    conversation_id = uuid4()
    user_query = "Total revenue this month?"

    config = build_graph_invoke_config(
        conversation_id=conversation_id,
        app_env="production",
        app_name="hybrid-chatbot",
        user_query=user_query,
    )

    assert config["run_name"] == "chat: Total revenue this month?"
    assert config["tags"] == ["production"]
    assert config["configurable"]["thread_id"] == str(conversation_id)
    assert config["metadata"]["thread_id"] == str(conversation_id)
    assert config["metadata"]["conversation_id"] == str(conversation_id)
    assert config["metadata"]["session_id"] == str(conversation_id)
    assert config["metadata"]["user_query"] == user_query
    assert config["metadata"]["request_id"] == request_id


def test_build_child_run_config_preserves_thread_metadata():
    parent = build_graph_invoke_config(
        conversation_id=uuid4(),
        app_env="dev",
        app_name="app",
        user_query="hello",
    )
    child = build_child_run_config(parent, run_name="sql_generation")

    assert child["run_name"] == "sql_generation"
    assert child["metadata"]["thread_id"] == parent["metadata"]["thread_id"]
    assert child["metadata"]["conversation_id"] == parent["metadata"]["conversation_id"]


def test_make_graph_invoke_config_builder_adds_extra_tags():
    settings = Settings(_env_file=None, APP_ENV="staging", APP_NAME="my-app")
    builder = make_graph_invoke_config_builder(settings, extra_tags=["stub"])
    config = builder(conversation_id=uuid4(), user_query="policy?")

    assert config["tags"] == ["staging", "stub"]
    assert config["metadata"]["user_query"] == "policy?"


@pytest.mark.asyncio
async def test_orchestrator_passes_config_to_graph_ainvoke():
    mock_graph = MagicMock()
    mock_graph.ainvoke = AsyncMock(
        return_value={
            "route": RouteType.VECTOR.value,
            "confidence": 0.9,
            "answer": "ok",
            "sources": ["doc.txt"],
            "sql_query": None,
        }
    )

    def config_builder(*, conversation_id, user_query):
        return {
            "run_name": "chat_graph",
            "metadata": {
                "conversation_id": str(conversation_id),
                "thread_id": str(conversation_id),
                "user_query": user_query,
            },
        }

    orchestrator = ChatOrchestrator(mock_graph, invoke_config_builder=config_builder)
    conversation_id = uuid4()
    message = ChatMessage(content="hello", conversation_id=conversation_id)

    await orchestrator.process(message)

    mock_graph.ainvoke.assert_awaited_once()
    call_args = mock_graph.ainvoke.call_args
    assert call_args[0][0]["query"] == "hello"
    assert call_args[1]["config"]["metadata"]["thread_id"] == str(conversation_id)
    assert call_args[1]["config"]["metadata"]["user_query"] == "hello"


@pytest.mark.asyncio
async def test_orchestrator_empty_config_without_builder():
    mock_graph = MagicMock()
    mock_graph.ainvoke = AsyncMock(
        return_value={
            "route": RouteType.VECTOR.value,
            "confidence": 0.9,
            "answer": "ok",
            "sources": [],
            "sql_query": None,
        }
    )

    orchestrator = ChatOrchestrator(mock_graph)
    await orchestrator.process(ChatMessage(content="hi", conversation_id=uuid4()))

    call_kwargs = mock_graph.ainvoke.call_args[1]
    assert call_kwargs["config"] == {}


def test_create_orchestrator_forwards_invoke_config_builder():
    mock_classifier = MagicMock()
    mock_sql = MagicMock()
    mock_vector = MagicMock()
    builder = MagicMock()

    orchestrator = create_orchestrator(
        classifier=mock_classifier,
        sql_pipeline=mock_sql,
        vector_pipeline=mock_vector,
        invoke_config_builder=builder,
    )

    assert orchestrator._invoke_config_builder is builder
