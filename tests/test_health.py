"""Health endpoint tests."""

from unittest.mock import patch

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
    assert "vector_backend" in body
    assert body["sql_dialect"] in {"SQLite", "PostgreSQL"}


@pytest.mark.asyncio
async def test_readiness_check_ok(client):
    response = await client.get("/ready")
    assert response.status_code in {200, 503}
    body = response.json()
    assert body["status"] in {"ready", "degraded"}
    assert body["postgres"] in {"ok", "down"}
    assert body["vector"] in {"ok", "down", "skipped"}
    assert "vector_backend" in body


@pytest.mark.asyncio
async def test_readiness_returns_503_when_postgres_down(client):
    with patch(
        "src.adapters.api.routes.health.check_postgres_connection",
        return_value=False,
    ):
        response = await client.get("/ready")
    assert response.status_code == 503
    assert response.json()["status"] == "degraded"
    assert response.json()["postgres"] == "down"
