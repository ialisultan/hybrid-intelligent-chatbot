"""Chat API integration tests."""

import pytest

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_chat_endpoint_returns_schema_fields(client_stub):
    response = await client_stub.post(
        "/api/v1/chat",
        json={"query": "Total revenue this month?"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "answer" in body
    assert body["route"] in {"sql", "vector"}
    assert "confidence" in body
    assert "sources" in body
    assert "conversation_id" in body
    assert body["conversation_id"] is not None


@pytest.mark.asyncio
async def test_chat_sql_query_routes_to_sql(client_stub):
    response = await client_stub.post(
        "/api/v1/chat",
        json={"query": "Top 5 customers by spending"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["route"] == "sql"
    assert body["sql_query"] is not None


@pytest.mark.asyncio
async def test_chat_vector_query_routes_to_vector(client_stub):
    response = await client_stub.post(
        "/api/v1/chat",
        json={"query": "What is your return policy?"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["route"] == "vector"
    assert body["sql_query"] is None
    assert isinstance(body["sources"], list)


@pytest.mark.asyncio
async def test_chat_multi_turn_preserves_conversation_id(client_stub):
    first = await client_stub.post(
        "/api/v1/chat",
        json={"query": "What is your return policy?"},
    )
    conversation_id = first.json()["conversation_id"]

    second = await client_stub.post(
        "/api/v1/chat",
        json={"query": "What about warranty?", "conversation_id": conversation_id},
    )
    assert second.status_code == 200
    assert second.json()["conversation_id"] == conversation_id
