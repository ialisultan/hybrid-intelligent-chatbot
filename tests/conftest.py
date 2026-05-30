"""Shared pytest fixtures."""

import pytest
from httpx import ASGITransport, AsyncClient

import src.infrastructure.di as di_module
from main import create_app


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def stub_container(monkeypatch):
    """Fresh DI container in stub mode (no LLM API keys required)."""
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    monkeypatch.setenv("GOOGLE_API_KEY", "")
    monkeypatch.setenv("CONVERSATION_REPOSITORY", "memory")
    monkeypatch.delenv("DATABASE_URL", raising=False)

    di_module.get_settings.cache_clear()
    di_module._container = None

    container = di_module.get_container()
    await container.init()
    yield container

    await container.shutdown()
    di_module._container = None
    di_module.get_settings.cache_clear()


@pytest.fixture
async def client_stub(stub_container):
    """AsyncClient backed by stub-mode container."""
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
