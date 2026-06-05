"""Seed order date helpers — assessment SQL demos need current-month data."""

from datetime import UTC, datetime, timedelta

from src.infrastructure.seed import order_dates_for_demo


def test_order_dates_include_current_month_and_last_seven_days():
    now = datetime(2026, 6, 1, 10, 0, tzinfo=UTC)
    dates = order_dates_for_demo(now)
    month_start = now.replace(day=1, hour=12, minute=0, second=0, microsecond=0)
    month_end = now.replace(month=7, day=1, hour=0, minute=0, second=0, microsecond=0)
    window_start = now - timedelta(days=7)

    assert any(month_start <= d < month_end for d in dates)
    assert any(window_start <= d <= now for d in dates)
