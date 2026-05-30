"""ORM read layer for PostgreSQL persistence."""

from typing import Any

import structlog
from sqlalchemy import select, text

from src.adapters.persistence.models import Customer, Order, Product
from src.infrastructure.database import get_session_factory

logger = structlog.get_logger(__name__)

_SCHEMA_MODELS = (Customer, Product, Order)


class PostgresRepository:
    """Read-only repository over SQLAlchemy ORM models."""

    def get_schema_metadata(self) -> str:
        """Build schema description from ORM column definitions for LLM SQL generation."""
        lines = ["Tables:"]
        for model in _SCHEMA_MODELS:
            table = model.__table__
            columns = ", ".join(col.name for col in table.columns)
            lines.append(f"- {table.name}({columns})")
        return "\n".join(lines)

    async def health_check(self) -> bool:
        """Return True if Postgres accepts SELECT 1."""
        try:
            factory = get_session_factory()
            async with factory() as session:
                await session.execute(text("SELECT 1"))
            return True
        except Exception as exc:
            logger.warning("postgres.health_check_failed", error=str(exc))
            return False

    async def list_customers(self, limit: int = 10) -> list[dict[str, Any]]:
        factory = get_session_factory()
        async with factory() as session:
            result = await session.execute(select(Customer).limit(limit))
            return [
                {"id": c.id, "name": c.name, "email": c.email, "country": c.country}
                for c in result.scalars().all()
            ]

    async def list_orders(self, limit: int = 10) -> list[dict[str, Any]]:
        factory = get_session_factory()
        async with factory() as session:
            result = await session.execute(select(Order).limit(limit))
            return [
                {
                    "id": o.id,
                    "customer_id": o.customer_id,
                    "product_name": o.product_name,
                    "amount": float(o.amount),
                    "order_date": o.order_date.isoformat() if o.order_date else None,
                }
                for o in result.scalars().all()
            ]
