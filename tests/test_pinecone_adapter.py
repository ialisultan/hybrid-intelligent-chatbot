"""Pinecone adapter tests — mocked Pinecone SDK."""

from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.unit

from src.adapters.vector.pinecone_adapter import PineconeVectorAdapter
from src.domain.exceptions.base import VectorStoreError
from src.infrastructure.config.settings import Settings


@pytest.fixture
def settings():
    return Settings(
        _env_file=None,
        VECTOR_STORE_BACKEND="pinecone",
        PINECONE_API_KEY="test-key",
        PINECONE_INDEX="test-index",
        PINECONE_NAMESPACE="ns1",
    )


@pytest.fixture
def mock_embeddings():
    emb = MagicMock()
    emb.embed_query.return_value = [0.1] * 1536
    emb.embed_documents.return_value = [[0.1] * 1536, [0.2] * 1536]
    return emb


@patch("src.adapters.vector.pinecone_adapter.Pinecone")
def test_pinecone_initialises_with_namespace(mock_pinecone_cls, settings, mock_embeddings):
    mock_pc = MagicMock()
    mock_index = MagicMock()
    mock_pc.Index.return_value = mock_index
    mock_pinecone_cls.return_value = mock_pc

    adapter = PineconeVectorAdapter(settings, mock_embeddings)

    mock_pinecone_cls.assert_called_once_with(api_key="test-key")
    mock_pc.Index.assert_called_once_with("test-index")
    assert adapter._namespace == "ns1"  # noqa: SLF001


@patch("src.adapters.vector.pinecone_adapter.Pinecone")
def test_vector_count_from_index_stats(mock_pinecone_cls, settings, mock_embeddings):
    mock_pc = MagicMock()
    mock_index = MagicMock()
    mock_stats = MagicMock()
    mock_stats.total_vector_count = 42
    mock_index.describe_index_stats.return_value = mock_stats
    mock_pc.Index.return_value = mock_index
    mock_pinecone_cls.return_value = mock_pc

    adapter = PineconeVectorAdapter(settings, mock_embeddings)
    assert adapter.vector_count() == 42


@patch("src.adapters.vector.pinecone_adapter.Pinecone")
@pytest.mark.asyncio
async def test_search_maps_matches(mock_pinecone_cls, settings, mock_embeddings):
    mock_pc = MagicMock()
    mock_index = MagicMock()
    match = MagicMock()
    match.metadata = {"text": "Return within 30 days.", "source": "return_policy.md"}
    match.score = 0.91
    mock_index.query.return_value = MagicMock(matches=[match])
    mock_pc.Index.return_value = mock_index
    mock_pinecone_cls.return_value = mock_pc

    adapter = PineconeVectorAdapter(settings, mock_embeddings)
    results = await adapter.search("return policy", top_k=3)

    assert len(results) == 1
    assert results[0].content == "Return within 30 days."
    assert results[0].source == "return_policy.md"
    mock_index.query.assert_called_once()


@patch("src.adapters.vector.pinecone_adapter.Pinecone")
def test_initialisation_error_mapped(mock_pinecone_cls, settings, mock_embeddings):
    mock_pinecone_cls.side_effect = RuntimeError("invalid api key")
    with pytest.raises(VectorStoreError, match="Failed to initialise Pinecone"):
        PineconeVectorAdapter(settings, mock_embeddings)
