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
    with pytest.raises(DatabaseError, match="Only SELECT"):
        await adapter.execute("INSERT INTO customers VALUES (1, 'x', 'x@x.com', 'US')")


@pytest.mark.asyncio
async def test_rejects_non_select(adapter):
    with pytest.raises(DatabaseError, match="Only SELECT"):
        await adapter.execute("DELETE FROM customers")


@pytest.mark.asyncio
async def test_rejects_forbidden_keyword_in_select(adapter):
    with pytest.raises(DatabaseError, match="forbidden"):
        await adapter.execute("SELECT 1; DROP TABLE customers")
