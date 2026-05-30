"""Database seed script — populates sample structured data."""

import asyncio

import structlog
from sqlalchemy import text

from src.infrastructure.config import get_settings
from src.infrastructure.database import create_engine, get_session_factory

logger = structlog.get_logger(__name__)

SEED_STATEMENTS = [
    """
    INSERT INTO customers (id, name, email, country) VALUES
        (1, 'Alice Johnson', 'alice@example.com', 'Germany'),
        (2, 'Bob Smith', 'bob@example.com', 'USA'),
        (3, 'Carol Williams', 'carol@example.com', 'UK'),
        (4, 'David Brown', 'david@example.com', 'Germany'),
        (5, 'Eve Davis', 'eve@example.com', 'France')
    ON CONFLICT (id) DO NOTHING
    """,
    """
    INSERT INTO products (id, name, category, price) VALUES
        (1, 'SmartWidget Pro', 'Electronics', 299.99),
        (2, 'EcoBottle', 'Home', 24.99),
        (3, 'CloudSync License', 'Software', 49.99),
        (4, 'FitTrack Band', 'Wearables', 149.99),
        (5, 'DeskLamp XL', 'Home', 59.99)
    ON CONFLICT (id) DO NOTHING
    """,
    """
    INSERT INTO orders (id, customer_id, product_name, amount, order_date) VALUES
        (1, 1, 'SmartWidget Pro', 299.99, NOW() - INTERVAL '2 days'),
        (2, 2, 'EcoBottle', 24.99, NOW() - INTERVAL '5 days'),
        (3, 1, 'CloudSync License', 49.99, NOW() - INTERVAL '10 days'),
        (4, 3, 'FitTrack Band', 149.99, NOW() - INTERVAL '3 days'),
        (5, 4, 'DeskLamp XL', 59.99, NOW() - INTERVAL '1 day'),
        (6, 2, 'SmartWidget Pro', 299.99, NOW() - INTERVAL '15 days'),
        (7, 5, 'EcoBottle', 24.99, NOW() - INTERVAL '6 days')
    ON CONFLICT (id) DO NOTHING
    """,
]


async def seed() -> None:
    settings = get_settings()
    create_engine(settings)
    factory = get_session_factory()

    async with factory() as session:
        for statement in SEED_STATEMENTS:
            await session.execute(text(statement))
        await session.commit()

    logger.info("seed.complete")


if __name__ == "__main__":
    asyncio.run(seed())
