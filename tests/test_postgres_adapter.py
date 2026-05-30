"""Postgres adapter safety and schema tests."""

import pytest

pytestmark = pytest.mark.unit

from src.adapters.persistence.postgres_adapter import PostgresAdapter
from src.adapters.persistence.postgres_repository import PostgresRepository
from src.domain.exceptions.base import DatabaseError
from src.infrastructure.config.settings import Settings


@pytest.fixture
def adapter():
    return PostgresAdapter(Settings())


def test_schema_from_repository():
    repo = PostgresRepository()
    schema = repo.get_schema_metadata()
    assert "customers" in schema
    assert "products" in schema
    assert "orders" in schema
    assert "customer_id" in schema


@pytest.mark.asyncio
async def test_schema_description(adapter):
    description = await adapter.get_schema_description()
    assert "customers" in description
    assert "orders" in description


@pytest.mark.asyncio
async def test_rejects_insert(adapter):
    with pytest.raises(DatabaseError, match="Only SELECT or WITH"):
        await adapter.execute("INSERT INTO customers VALUES (1, 'x', 'x@x.com', 'US')")


@pytest.mark.asyncio
async def test_rejects_non_select(adapter):
    with pytest.raises(DatabaseError, match="Only SELECT or WITH"):
        await adapter.execute("DELETE FROM customers")


@pytest.mark.asyncio
async def test_rejects_forbidden_keyword_in_select(adapter):
    with pytest.raises(DatabaseError, match="Multiple SQL"):
        await adapter.execute("SELECT 1; DROP TABLE customers")


@pytest.mark.asyncio
async def test_accepts_with_cte(adapter):
    """WITH queries pass guard; execution may fail without DB — guard only here."""
    from unittest.mock import AsyncMock, MagicMock, patch

    with patch("src.adapters.persistence.postgres_adapter.get_session_factory") as mock_factory:
        session = AsyncMock()
        result = MagicMock()
        result.mappings.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=result)
        session.__aenter__ = AsyncMock(return_value=session)
        session.__aexit__ = AsyncMock(return_value=None)
        mock_factory.return_value.return_value = session

        rows = await adapter.execute(
            "WITH c AS (SELECT 1 AS n) SELECT n FROM c"
        )
        assert rows == []
