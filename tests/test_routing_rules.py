"""Pure routing rules — policy intent and assessment matrix."""

import pytest

from src.application.routing.rules import detect_policy_intent, rule_based_classify
from src.domain.entities.chat import RouteType

pytestmark = pytest.mark.unit

POLICY_QUERIES = [
    "Tell me about orders policy",
    "Customers refund issues",
    "What is the order policy for returns?",
]


@pytest.mark.parametrize("query", POLICY_QUERIES)
def test_detect_policy_intent(query):
    assert detect_policy_intent(query)


@pytest.mark.parametrize(
    "query,expected",
    [
        ("Total revenue this month?", RouteType.SQL),
        ("Top 5 customers by spending", RouteType.SQL),
        ("Orders placed in the last 7 days", RouteType.SQL),
        ("What is your return policy?", RouteType.VECTOR),
        ("Explain product features", RouteType.VECTOR),
        ("Tell me about orders policy", RouteType.VECTOR),
        ("Customers refund issues", RouteType.VECTOR),
    ],
)
def test_rule_based_assessment_routing(query, expected):
    assert rule_based_classify(query).route == expected


SQL_AGGREGATION_QUERIES = [
    "Total revenue this month?",
    "Top 5 customers by spending",
    "Orders placed in the last 7 days",
]


@pytest.mark.parametrize("query", SQL_AGGREGATION_QUERIES)
def test_detect_policy_intent_false_for_sql_aggregations(query):
    assert not detect_policy_intent(query)


def test_detect_policy_intent_false_when_aggregation_cues_present():
    assert not detect_policy_intent("total orders last month")


def test_rule_based_classify_sql_for_aggregation_with_table_words():
    result = rule_based_classify("Total orders count last month")
    assert result.route == RouteType.SQL
