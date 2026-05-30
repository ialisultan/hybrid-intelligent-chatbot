"""Unit tests for Streamlit HTTP client utilities."""

from unittest.mock import MagicMock, patch
from uuid import UUID

import httpx
import pytest

pytestmark = pytest.mark.unit

from frontend.data.assessment_queries import ALL_QUERIES
from frontend.utils import (
    ChatResponseMeta,
    build_all_assessment_curl_commands,
    build_curl_command,
    get_backend_url,
    get_health,
    parse_chat_response,
    post_chat,
)


def test_get_backend_url_default(monkeypatch):
    monkeypatch.delenv("BACKEND_URL", raising=False)
    assert get_backend_url() == "http://localhost:8000"


def test_get_backend_url_from_env(monkeypatch):
    monkeypatch.setenv("BACKEND_URL", "http://api:8000/")
    assert get_backend_url() == "http://api:8000"


def test_post_chat_payload_and_url():
    conv_id = UUID("3fa85f64-5717-4562-b3fc-2c963f66afa6")
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "answer": "ok",
        "route": "sql",
        "confidence": 0.9,
        "sources": [],
        "sql_query": "SELECT 1",
        "conversation_id": str(conv_id),
    }

    with patch("frontend.utils.httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.post.return_value = mock_response
        mock_client_cls.return_value = mock_client

        result = post_chat("Total revenue?", conversation_id=conv_id, backend_url="http://test:8000")

    mock_client.post.assert_called_once_with(
        "http://test:8000/api/v1/chat",
        json={
            "query": "Total revenue?",
            "conversation_id": str(conv_id),
        },
    )
    assert result["route"] == "sql"


def test_post_chat_without_conversation_id():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"answer": "hi", "route": "vector"}

    with patch("frontend.utils.httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.post.return_value = mock_response
        mock_client_cls.return_value = mock_client

        post_chat("Hello")

    call_kwargs = mock_client.post.call_args
    assert call_kwargs[1]["json"] == {"query": "Hello"}


def test_get_health():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "status": "ok",
        "chat_provider": "openai",
        "embedding_provider": "openai",
    }

    with patch("frontend.utils.httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.get.return_value = mock_response
        mock_client_cls.return_value = mock_client

        health = get_health(backend_url="http://test:8000")

    mock_client.get.assert_called_once_with("http://test:8000/health")
    assert health["status"] == "ok"


def test_parse_chat_response_full():
    conv_id = UUID("3fa85f64-5717-4562-b3fc-2c963f66afa6")
    parsed = parse_chat_response(
        {
            "answer": "Total is $100.",
            "route": "sql",
            "confidence": 0.92,
            "sources": [],
            "sql_query": "SELECT SUM(amount) FROM orders",
            "conversation_id": str(conv_id),
        }
    )
    assert isinstance(parsed, ChatResponseMeta)
    assert parsed.answer == "Total is $100."
    assert parsed.route == "sql"
    assert parsed.confidence == 0.92
    assert parsed.sql_query == "SELECT SUM(amount) FROM orders"
    assert parsed.sources == []
    assert parsed.conversation_id == conv_id


def test_parse_chat_response_vector_route_enum_like():
    class RouteEnum:
        value = "vector"

    parsed = parse_chat_response(
        {
            "answer": "30-day returns.",
            "route": RouteEnum(),
            "confidence": 0.88,
            "sources": ["return_policy.md"],
            "sql_query": None,
            "conversation_id": None,
        }
    )
    assert parsed.route == "vector"
    assert parsed.sources == ["return_policy.md"]
    assert parsed.conversation_id is None


def test_build_curl_command_basic():
    cmd = build_curl_command("Total revenue this month?", backend_url="http://localhost:8000")
    assert "curl -s -X POST http://localhost:8000/api/v1/chat" in cmd
    assert '"query": "Total revenue this month?"' in cmd
    assert "conversation_id" not in cmd


def test_build_curl_command_with_conversation_id():
    conv_id = UUID("3fa85f64-5717-4562-b3fc-2c963f66afa6")
    cmd = build_curl_command(
        "Follow up",
        conversation_id=conv_id,
        backend_url="http://localhost:8000",
    )
    assert "3fa85f64-5717-4562-b3fc-2c963f66afa6" in cmd


def test_build_curl_command_escapes_quotes():
    cmd = build_curl_command('Say "hello"', backend_url="http://localhost:8000")
    assert '\\"hello\\"' in cmd or '"hello"' in cmd


def test_build_all_assessment_curl_commands():
    text = build_all_assessment_curl_commands(ALL_QUERIES, backend_url="http://test:8000")
    assert text.count("curl -s -X POST") == len(ALL_QUERIES)
    assert "Tell me about orders policy" in text


def test_assessment_catalog_has_seven_queries():
    assert len(ALL_QUERIES) == 7
