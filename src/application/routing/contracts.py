"""Pipeline routing contracts — pure validation (no framework imports)."""

from src.domain.entities.chat import RouteType
from src.domain.exceptions.base import RoutingViolationError


def validate_pipeline_output(
    route: str,
    *,
    sources: list[str] | None,
    sql_query: str | None,
) -> None:
    """Ensure SQL and Vector pipeline outputs never mix."""
    normalized_sources = sources or []
    if route == RouteType.SQL.value:
        if normalized_sources:
            raise RoutingViolationError(
                "SQL pipeline must not return document sources"
            )
        return

    if route == RouteType.VECTOR.value:
        if sql_query is not None:
            raise RoutingViolationError(
                "Vector pipeline must not return a sql_query"
            )
        return

    raise RoutingViolationError(f"Unknown route for validation: {route}")
