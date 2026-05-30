"""Vector pipeline adapter tests."""

from unittest.mock import ANY, AsyncMock, MagicMock, patch

import pytest

pytestmark = pytest.mark.unit

from src.adapters.vector.vector_pipeline_adapter import LangChainVectorPipelineAdapter
from src.domain.exceptions.base import VectorStoreError
from src.infrastructure.config.settings import Settings


class MockChatModel:
    def __init__(self) -> None:
        self.langchain_model = MagicMock()


@pytest.fixture
def mock_vector_store():
    return MagicMock()


@pytest.fixture
def mock_chat_model():
    return MockChatModel()


@patch("src.adapters.vector.vector_pipeline_adapter.build_vector_rag_chain")
@patch("src.adapters.vector.vector_pipeline_adapter.to_retriever")
@pytest.mark.asyncio
async def test_run_returns_answer_and_sources(
    mock_to_retriever, mock_build_chain, mock_vector_store, mock_chat_model
):
    mock_retriever = MagicMock()
    mock_to_retriever.return_value = mock_retriever

    mock_chain = MagicMock()
    mock_chain.ainvoke = AsyncMock(
        return_value={"answer": "30-day return policy.", "sources": ["return_policy.md"]}
    )
    mock_build_chain.return_value = mock_chain

    adapter = LangChainVectorPipelineAdapter(
        mock_vector_store, mock_chat_model, Settings()
    )
    result = await adapter.run("What is your return policy?")

    mock_to_retriever.assert_called_once()
    mock_build_chain.assert_called_once_with(mock_retriever, mock_chat_model.langchain_model)
    mock_chain.ainvoke.assert_awaited_once_with(
        {"query": "What is your return policy?"},
        config=ANY,
    )
    assert "return" in result["answer"].lower()
    assert "return_policy.md" in result["sources"]


@patch("src.adapters.vector.vector_pipeline_adapter.build_vector_rag_chain")
@patch("src.adapters.vector.vector_pipeline_adapter.to_retriever")
@pytest.mark.asyncio
async def test_vector_store_error_returns_graceful_fallback(
    mock_to_retriever, mock_build_chain, mock_vector_store, mock_chat_model
):
    mock_to_retriever.return_value = MagicMock()
    mock_chain = MagicMock()
    mock_chain.ainvoke = AsyncMock(side_effect=VectorStoreError("Qdrant unavailable"))
    mock_build_chain.return_value = mock_chain

    adapter = LangChainVectorPipelineAdapter(
        mock_vector_store, mock_chat_model, Settings()
    )
    result = await adapter.run("What is your return policy?")

    assert result["sources"] == []
    assert "Unable to retrieve documents" in result["answer"]
