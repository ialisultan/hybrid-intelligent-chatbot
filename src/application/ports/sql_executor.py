"""SQL executor port — read-only structured query execution."""

from abc import ABC, abstractmethod
from typing import Any


class SQLExecutorPort(ABC):
    """Execute validated read-only SQL against PostgreSQL."""

    @abstractmethod
    async def execute(self, sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Run a SELECT query and return rows as dicts."""
        ...

    @abstractmethod
    async def get_schema_description(self) -> str:
        """Return a human-readable schema for LLM SQL generation."""
        ...
