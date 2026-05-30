"""Database seed script — populates sample structured data."""

import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import structlog
from sqlalchemy import func, select

from src.adapters.persistence.models import Customer, Order, Product
from src.infrastructure.config import get_settings
from src.infrastructure.database import create_engine, get_session_factory

logger = structlog.get_logger(__name__)

CUSTOMERS = [
    {"id": 1, "name": "Alice Johnson", "email": "alice@example.com", "country": "Germany"},
    {"id": 2, "name": "Bob Smith", "email": "bob@example.com", "country": "USA"},
    {"id": 3, "name": "Carol Williams", "email": "carol@example.com", "country": "UK"},
    {"id": 4, "name": "David Brown", "email": "david@example.com", "country": "Germany"},
    {"id": 5, "name": "Eve Davis", "email": "eve@example.com", "country": "France"},
]

PRODUCTS = [
    {"id": 1, "name": "SmartWidget Pro", "category": "Electronics", "price": Decimal("299.99")},
    {"id": 2, "name": "EcoBottle", "category": "Home", "price": Decimal("24.99")},
    {"id": 3, "name": "CloudSync License", "category": "Software", "price": Decimal("49.99")},
    {"id": 4, "name": "FitTrack Band", "category": "Wearables", "price": Decimal("149.99")},
    {"id": 5, "name": "DeskLamp XL", "category": "Home", "price": Decimal("59.99")},
]

ORDERS = [
    (1, 1, "SmartWidget Pro", Decimal("299.99"), 2),
    (2, 2, "EcoBottle", Decimal("24.99"), 5),
    (3, 1, "CloudSync License", Decimal("49.99"), 10),
    (4, 3, "FitTrack Band", Decimal("149.99"), 3),
    (5, 4, "DeskLamp XL", Decimal("59.99"), 1),
    (6, 2, "SmartWidget Pro", Decimal("299.99"), 15),
    (7, 5, "EcoBottle", Decimal("24.99"), 6),
]


async def seed() -> None:
    settings = get_settings()
    create_engine(settings)
    factory = get_session_factory()

    async with factory() as session:
        existing = await session.scalar(select(func.count()).select_from(Customer))
        if existing and existing > 0:
            logger.info("seed.skipped", reason="customers already present")
            return

        now = datetime.now(UTC)
        for row in CUSTOMERS:
            session.add(Customer(**row))
        for row in PRODUCTS:
            session.add(Product(**row))
        for order_id, customer_id, product_name, amount, days_ago in ORDERS:
            session.add(
                Order(
                    id=order_id,
                    customer_id=customer_id,
                    product_name=product_name,
                    amount=amount,
                    order_date=now - timedelta(days=days_ago),
                )
            )
        await session.commit()

    logger.info("seed.complete")


if __name__ == "__main__":
    asyncio.run(seed())
