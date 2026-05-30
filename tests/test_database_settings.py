"""Database URL resolution for local SQLite vs Docker PostgreSQL."""

import pytest

from src.infrastructure.config.settings import Settings

pytestmark = pytest.mark.unit


def test_local_default_uses_sqlite_when_no_database_url():
    settings = Settings(_env_file=None)
    assert settings.async_database_url == "sqlite+aiosqlite:///data/local.db"
    assert settings.is_sqlite is True
    assert settings.sql_dialect == "SQLite"


def test_explicit_postgres_database_url():
    url = "postgresql+asyncpg://chatbot:chatbot_secret@postgres:5432/chatbot"
    settings = Settings(_env_file=None, DATABASE_URL=url)
    assert settings.async_database_url == url
    assert settings.is_sqlite is False
    assert settings.sql_dialect == "PostgreSQL"


def test_docker_compose_postgres_host_fallback():
    """When DATABASE_URL is unset but POSTGRES_HOST=postgres (Compose service name)."""
    settings = Settings(
        _env_file=None,
        POSTGRES_HOST="postgres",
        POSTGRES_USER="chatbot",
        POSTGRES_PASSWORD="chatbot_secret",
        POSTGRES_DB="chatbot",
    )
    assert settings.async_database_url == (
        "postgresql+asyncpg://chatbot:chatbot_secret@postgres:5432/chatbot"
    )
    assert settings.is_sqlite is False
    assert settings.sql_dialect == "PostgreSQL"


def test_custom_sqlite_path():
    settings = Settings(_env_file=None, SQLITE_PATH="tmp/test.db")
    assert settings.async_database_url == "sqlite+aiosqlite:///tmp/test.db"
    assert settings.is_sqlite is True
