"""Hybrid classifier — LLM misclassification corrected by policy rules."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.adapters.llm.query_classifier import LLMQueryClassifier
from src.domain.entities.chat import RouteType
from src.domain.entities.llm import LLMProvider
from src.infrastructure.config.settings import Settings
from src.interfaces.schemas.classification import ClassificationResultSchema

pytestmark = pytest.mark.unit


class MockChatModel:
    provider = LLMProvider.OPENAI

    def __init__(self) -> None:
        self.langchain_model = MagicMock()


@pytest.fixture
def classifier():
    settings = Settings(classifier_confidence_threshold=0.7)
    model = MockChatModel()
    clf = LLMQueryClassifier(model, settings)
    clf._chain = AsyncMock()
    return clf


@pytest.mark.asyncio
async def test_policy_intent_skips_llm(classifier):
    result = await classifier.classify("Tell me about orders policy")
    assert result.route == RouteType.VECTOR
    classifier._chain.ainvoke.assert_not_called()


@pytest.mark.asyncio
async def test_llm_sql_misroute_corrected_when_high_confidence(classifier):
    classifier._chain.ainvoke.return_value = ClassificationResultSchema(
        route=RouteType.SQL,
        confidence=0.95,
        reasoning="misclassified as aggregation",
    )
    result = await classifier.classify("Customers refund issues")
    assert result.route == RouteType.VECTOR


@pytest.mark.asyncio
async def test_llm_sql_high_confidence_not_overridden_for_aggregation(classifier):
    classifier._chain.ainvoke.return_value = ClassificationResultSchema(
        route=RouteType.SQL,
        confidence=0.95,
        reasoning="revenue aggregation",
    )
    result = await classifier.classify("Total revenue this month?")
    assert result.route == RouteType.SQL
    classifier._chain.ainvoke.assert_called_once()


@pytest.mark.asyncio
async def test_llm_sql_low_confidence_edge_case_uses_rules(classifier):
    classifier._chain.ainvoke.return_value = ClassificationResultSchema(
        route=RouteType.SQL,
        confidence=0.5,
        reasoning="uncertain",
    )
    result = await classifier.classify("Tell me about orders policy")
    assert result.route == RouteType.VECTOR
