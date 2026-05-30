"""Rate limiting integration tests."""

import pytest

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_chat_rate_limit_returns_429(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    monkeypatch.setenv("GOOGLE_API_KEY", "")
    monkeypatch.setenv("CONVERSATION_REPOSITORY", "memory")
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
    monkeypatch.setenv("RATE_LIMIT_REQUESTS", "1")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SECONDS", "60")

    import src.infrastructure.di as di_module
    from httpx import ASGITransport, AsyncClient

    from src.main import create_app

    di_module.get_settings.cache_clear()
    di_module._container = None
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        first = await client.post(
            "/api/v1/chat",
            json={"query": "What is your return policy?"},
        )
        assert first.status_code == 200

        second = await client.post(
            "/api/v1/chat",
            json={"query": "What is your return policy?"},
        )
        assert second.status_code == 429

    di_module.get_settings.cache_clear()
