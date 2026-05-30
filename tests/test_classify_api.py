"""Classify debug API integration tests."""

import pytest
from httpx import ASGITransport, AsyncClient

import src.infrastructure.di as di_module
from main import create_app

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_classify_hidden_when_debug_off(client, monkeypatch):
    monkeypatch.setenv("APP_DEBUG", "false")
    di_module.get_settings.cache_clear()
    response = await client.post(
        "/api/v1/classify",
        json={"query": "Total revenue this month?"},
    )
    assert response.status_code == 404
    di_module.get_settings.cache_clear()


@pytest.mark.asyncio
async def test_classify_returns_route_when_debug_on(monkeypatch):
    monkeypatch.setenv("APP_DEBUG", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    monkeypatch.setenv("GOOGLE_API_KEY", "")
    di_module.get_settings.cache_clear()
    di_module._container = None

    container = di_module.get_container()
    await container.init()

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/classify",
            json={"query": "Tell me about orders policy"},
        )

    await container.shutdown()
    di_module._container = None
    di_module.get_settings.cache_clear()

    assert response.status_code == 200
    body = response.json()
    assert body["route"] in {"sql", "vector"}
    assert body["route_label"] in {"SQL", "VECTOR"}
    assert "confidence" in body
    assert "reasoning" in body
