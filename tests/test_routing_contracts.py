"""Pipeline output contract validation — mutual exclusion invariants."""

import pytest

from src.application.routing.contracts import validate_pipeline_output
from src.domain.entities.chat import RouteType
from src.domain.exceptions.base import RoutingViolationError

pytestmark = pytest.mark.unit


def test_sql_route_rejects_non_empty_sources():
    with pytest.raises(RoutingViolationError, match="must not return document sources"):
        validate_pipeline_output(
            RouteType.SQL.value,
            sources=["faq.md"],
            sql_query="SELECT 1",
        )


def test_vector_route_rejects_sql_query():
    with pytest.raises(RoutingViolationError, match="must not return a sql_query"):
        validate_pipeline_output(
            RouteType.VECTOR.value,
            sources=["faq.md"],
            sql_query="SELECT 1",
        )


def test_valid_sql_output_passes():
    validate_pipeline_output(
        RouteType.SQL.value,
        sources=[],
        sql_query="SELECT SUM(amount) FROM orders",
    )
    validate_pipeline_output(
        RouteType.SQL.value,
        sources=None,
        sql_query=None,
    )


def test_valid_vector_output_passes():
    validate_pipeline_output(
        RouteType.VECTOR.value,
        sources=["return_policy.md"],
        sql_query=None,
    )
    validate_pipeline_output(
        RouteType.VECTOR.value,
        sources=[],
        sql_query=None,
    )


def test_unknown_route_raises():
    with pytest.raises(RoutingViolationError, match="Unknown route"):
        validate_pipeline_output(
            "hybrid",
            sources=[],
            sql_query=None,
        )
