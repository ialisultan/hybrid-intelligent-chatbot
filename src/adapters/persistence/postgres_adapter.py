"""Read-only PostgreSQL adapter implementing SQLExecutorPort."""

import re
from typing import Any

import structlog
from sqlalchemy import text

from src.adapters.persistence.postgres_repository import PostgresRepository
from src.application.ports.sql_executor import SQLExecutorPort
from src.domain.exceptions.base import DatabaseError
from src.infrastructure.config.settings import Settings
from src.infrastructure.database import get_session_factory

logger = structlog.get_logger(__name__)

_FORBIDDEN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|GRANT|REVOKE|COPY)\b",
    re.IGNORECASE,
)


class PostgresAdapter(SQLExecutorPort):
    """Execute validated read-only SELECT queries against PostgreSQL."""

    def __init__(
        self,
        settings: Settings,
        repository: PostgresRepository | None = None,
    ) -> None:
        self._max_rows = settings.sql_pipeline_max_rows
        self._repository = repository or PostgresRepository()

    async def execute(
        self,
        sql: str,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        normalized = sql.strip().rstrip(";")
        if not normalized.upper().startswith("SELECT"):
            raise DatabaseError("Only SELECT queries are allowed")
        if _FORBIDDEN.search(normalized):
            raise DatabaseError("Query contains forbidden SQL keywords")

        limited_sql = f"SELECT * FROM ({normalized}) AS subquery LIMIT {self._max_rows}"
        factory = get_session_factory()

        try:
            async with factory() as session:
                result = await session.execute(text(limited_sql), params or {})
                rows = result.mappings().all()
                return [dict(row) for row in rows]
        except DatabaseError:
            raise
        except Exception as exc:
            raise DatabaseError(f"SQL execution failed: {exc}") from exc

    async def get_schema_description(self) -> str:
        return self._repository.get_schema_metadata()

    async def health_check(self) -> bool:
        return await self._repository.health_check()
