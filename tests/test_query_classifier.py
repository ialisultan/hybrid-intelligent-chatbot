"""LLM query classifier tests — assessment SQL/vector/edge cases."""

from unittest.mock import AsyncMock, MagicMock

import pytest

pytestmark = pytest.mark.unit

from src.adapters.llm.query_classifier import LLMQueryClassifier
from src.application.chains.classifier_chain import rule_based_classify
from src.domain.entities.chat import RouteType
from src.domain.entities.llm import LLMProvider
from src.infrastructure.config.settings import Settings
from src.interfaces.schemas.classification import ClassificationResultSchema


class MockChatModel:
    provider = LLMProvider.OPENAI

    def __init__(self) -> None:
        self.langchain_model = MagicMock()


@pytest.fixture
def settings():
    return Settings(classifier_confidence_threshold=0.7)


@pytest.fixture
def classifier(settings):
    model = MockChatModel()
    clf = LLMQueryClassifier(model, settings)
    clf._chain = AsyncMock()
    return clf


# --- Rule-based fallback (edge cases) ---

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
def test_rule_based_classify_assessment_queries(query, expected):
    result = rule_based_classify(query)
    assert result.route == expected


# --- LLM primary path ---

@pytest.mark.asyncio
async def test_llm_routes_sql(classifier):
    classifier._chain.ainvoke.return_value = ClassificationResultSchema(
        route=RouteType.SQL,
        confidence=0.95,
        reasoning="aggregation query",
    )
    result = await classifier.classify("Total revenue this month?")
    assert result.route == RouteType.SQL
    assert result.confidence >= 0.7


@pytest.mark.asyncio
async def test_llm_routes_vector(classifier):
    classifier._chain.ainvoke.return_value = ClassificationResultSchema(
        route=RouteType.VECTOR,
        confidence=0.92,
        reasoning="policy question",
    )
    result = await classifier.classify("What is your return policy?")
    assert result.route == RouteType.VECTOR


@pytest.mark.asyncio
async def test_low_confidence_falls_back_to_rules(classifier):
    classifier._chain.ainvoke.return_value = ClassificationResultSchema(
        route=RouteType.SQL,
        confidence=0.5,
        reasoning="uncertain",
    )
    result = await classifier.classify("Tell me about orders policy")
    assert result.route == RouteType.VECTOR


@pytest.mark.asyncio
async def test_llm_error_falls_back_to_rules(classifier):
    classifier._chain.ainvoke.side_effect = RuntimeError("LLM unavailable")
    result = await classifier.classify("Customers refund issues")
    assert result.route == RouteType.VECTOR
