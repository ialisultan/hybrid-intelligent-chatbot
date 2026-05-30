"""Assessment routing matrix — all GenAI Assessment II scenarios."""

import pytest

from src.adapters.llm.stub import StubClassifier
from src.application.chains.classifier_chain import rule_based_classify
from src.domain.entities.chat import RouteType

pytestmark = pytest.mark.unit

ASSESSMENT_CASES = [
    ("Total revenue this month?", RouteType.SQL),
    ("Top 5 customers by spending", RouteType.SQL),
    ("Orders placed in the last 7 days", RouteType.SQL),
    ("What is your return policy?", RouteType.VECTOR),
    ("Explain product features", RouteType.VECTOR),
    ("Tell me about orders policy", RouteType.VECTOR),
    ("Customers refund issues", RouteType.VECTOR),
]


@pytest.mark.parametrize("query,expected", ASSESSMENT_CASES)
def test_rule_based_assessment_routing(query, expected):
    result = rule_based_classify(query)
    assert result.route == expected


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "query,expected",
    [
        ("Total revenue this month?", RouteType.SQL),
        ("What is your return policy?", RouteType.VECTOR),
    ],
)
async def test_stub_classifier_keyword_routing(query, expected):
    classifier = StubClassifier()
    result = await classifier.classify(query)
    assert result.route == expected
