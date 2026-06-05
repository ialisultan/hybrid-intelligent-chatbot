"""Database seed script — populates sample structured data."""

import asyncio
import calendar
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

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
    (1, 1, "SmartWidget Pro", Decimal("299.99")),
    (2, 2, "EcoBottle", Decimal("24.99")),
    (3, 1, "CloudSync License", Decimal("49.99")),
    (4, 3, "FitTrack Band", Decimal("149.99")),
    (5, 4, "DeskLamp XL", Decimal("59.99")),
    (6, 2, "SmartWidget Pro", Decimal("299.99")),
    (7, 5, "EcoBottle", Decimal("24.99")),
]


def _day_of_current_month(now: datetime, day: int) -> datetime:
    """Nth day of the current month, capped to today (no future seed dates)."""
    t = now.astimezone(UTC).replace(hour=12, minute=0, second=0, microsecond=0)
    last_dom = calendar.monthrange(t.year, t.month)[1]
    dom = min(max(1, day), last_dom, t.day)
    return t.replace(day=dom)


def order_dates_for_demo(now: datetime | None = None) -> list[datetime]:
    """Spread dates for assessment SQL: current-month revenue and last-7-days orders."""
    t = (now or datetime.now(UTC)).astimezone(UTC).replace(
        hour=12, minute=0, second=0, microsecond=0
    )
    month_start = t.replace(day=1)
    return [
        month_start,
        t - timedelta(days=3),
        month_start,
        t - timedelta(days=5),
        t,
        t - timedelta(days=6),
        _day_of_current_month(t, 15),
    ]


def _month_bounds(now: datetime) -> tuple[datetime, datetime]:
    t = now.astimezone(UTC)
    start = t.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if t.month == 12:
        end = start.replace(year=t.year + 1, month=1)
    else:
        end = start.replace(month=t.month + 1)
    return start, end


async def _has_orders_in_current_month(session: AsyncSession) -> bool:
    now = datetime.now(UTC)
    month_start, month_end = _month_bounds(now)
    count = await session.scalar(
        select(func.count())
        .select_from(Order)
        .where(Order.order_date >= month_start, Order.order_date < month_end)
    )
    return bool(count and count > 0)


async def _refresh_order_dates(session: AsyncSession) -> None:
    now = datetime.now(UTC)
    dates = order_dates_for_demo(now)
    result = await session.execute(select(Order).order_by(Order.id))
    orders = result.scalars().all()
    for order, order_date in zip(orders, dates, strict=True):
        order.order_date = order_date
    await session.commit()
    logger.info("seed.refreshed_order_dates", count=len(orders))


async def seed() -> None:
    settings = get_settings()
    create_engine(settings)
    factory = get_session_factory()

    async with factory() as session:
        existing = await session.scalar(select(func.count()).select_from(Customer))
        if existing and existing > 0:
            if not await _has_orders_in_current_month(session):
                await _refresh_order_dates(session)
            else:
                logger.info("seed.skipped", reason="customers already present")
            return

        now = datetime.now(UTC)
        dates = order_dates_for_demo(now)
        for row in CUSTOMERS:
            session.add(Customer(**row))
        for row in PRODUCTS:
            session.add(Product(**row))
        for (order_id, customer_id, product_name, amount), order_date in zip(
            ORDERS, dates, strict=True
        ):
            session.add(
                Order(
                    id=order_id,
                    customer_id=customer_id,
                    product_name=product_name,
                    amount=amount,
                    order_date=order_date,
                )
            )
        await session.commit()

    logger.info("seed.complete")


if __name__ == "__main__":
    asyncio.run(seed())
