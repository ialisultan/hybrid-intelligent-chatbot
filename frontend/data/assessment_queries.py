"""Assessment demo query catalog — aligned with README assessment matrix."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

RouteLiteral = Literal["sql", "vector"]
CategoryLiteral = Literal["sql", "vector", "edge"]


@dataclass(frozen=True)
class AssessmentQuery:
    label: str
    query: str
    expected_route: RouteLiteral
    category: CategoryLiteral
    demo_note: str = ""


SQL_QUERIES: tuple[AssessmentQuery, ...] = (
    AssessmentQuery(
        label="Revenue",
        query="Total revenue this month?",
        expected_route="sql",
        category="sql",
        demo_note="Structured aggregation over orders.",
    ),
    AssessmentQuery(
        label="Top customers",
        query="Top 5 customers by spending",
        expected_route="sql",
        category="sql",
        demo_note="Ranking query on customer spend.",
    ),
    AssessmentQuery(
        label="Recent orders",
        query="Orders placed in the last 7 days",
        expected_route="sql",
        category="sql",
        demo_note="Date-filtered order count.",
    ),
)

VECTOR_QUERIES: tuple[AssessmentQuery, ...] = (
    AssessmentQuery(
        label="Return policy",
        query="What is your return policy?",
        expected_route="vector",
        category="vector",
        demo_note="Policy document RAG.",
    ),
    AssessmentQuery(
        label="Product features",
        query="Explain product features",
        expected_route="vector",
        category="vector",
        demo_note="Product documentation search.",
    ),
)

EDGE_QUERIES: tuple[AssessmentQuery, ...] = (
    AssessmentQuery(
        label="Orders policy",
        query="Tell me about orders policy",
        expected_route="vector",
        category="edge",
        demo_note="Table word + policy intent → vector (not SQL).",
    ),
    AssessmentQuery(
        label="Refund issues",
        query="Customers refund issues",
        expected_route="vector",
        category="edge",
        demo_note="Support/refund intent despite customer vocabulary.",
    ),
)

ALL_QUERIES: tuple[AssessmentQuery, ...] = SQL_QUERIES + VECTOR_QUERIES + EDGE_QUERIES

DEMO_SCRIPT_STEPS: tuple[AssessmentQuery, ...] = (
    SQL_QUERIES[0],
    SQL_QUERIES[1],
    VECTOR_QUERIES[0],
    EDGE_QUERIES[0],
    EDGE_QUERIES[1],
)
