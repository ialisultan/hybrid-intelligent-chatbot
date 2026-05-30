"""Health endpoint tests."""

import pytest

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "chat_provider" in body
    assert "embedding_provider" in body


@pytest.mark.asyncio
async def test_readiness_check(client):
    response = await client.get("/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"ready", "degraded"}
    assert body["postgres"] in {"ok", "down"}
    assert "chat_provider" in body
    assert "embedding_provider" in body
