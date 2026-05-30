"""Qdrant adapter tests — dynamic dimensions and error mapping."""

from unittest.mock import MagicMock, patch

import pytest

from src.adapters.vector.qdrant_adapter import QdrantVectorAdapter
from src.domain.exceptions.base import VectorStoreError
from src.infrastructure.config.settings import Settings


@pytest.fixture
def settings():
    return Settings(
        vector_store_backend="qdrant",
        qdrant_host="localhost",
        qdrant_port=6333,
        qdrant_collection="test_docs",
    )


@pytest.fixture
def mock_embeddings():
    emb = MagicMock()
    emb.embed_query.return_value = [0.1] * 768
    return emb


@patch("src.adapters.vector.qdrant_adapter.QdrantVectorStore")
@patch("src.adapters.vector.qdrant_adapter.QdrantClient")
def test_dynamic_vector_dimension(mock_client_cls, mock_store_cls, settings, mock_embeddings):
    mock_client = MagicMock()
    mock_client.collection_exists.return_value = False
    mock_client_cls.return_value = mock_client

    adapter = QdrantVectorAdapter(settings, mock_embeddings)

    assert adapter._vector_size == 768
    mock_embeddings.embed_query.assert_called_once_with("probe")
    create_call = mock_client.create_collection.call_args
    vectors_config = create_call.kwargs["vectors_config"]
    assert vectors_config.size == 768


@patch("src.adapters.vector.qdrant_adapter.QdrantVectorStore")
@patch("src.adapters.vector.qdrant_adapter.QdrantClient")
def test_dimension_mismatch_logs_warning(mock_client_cls, mock_store_cls, settings, mock_embeddings):
    mock_client = MagicMock()
    mock_client.collection_exists.return_value = True
    mock_info = MagicMock()
    mock_info.config.params.vectors.size = 1536
    mock_client.get_collection.return_value = mock_info
    mock_client_cls.return_value = mock_client

    adapter = QdrantVectorAdapter(settings, mock_embeddings)
    assert adapter._vector_size == 768
    mock_client.create_collection.assert_not_called()


@patch("src.adapters.vector.qdrant_adapter.QdrantClient")
def test_connection_error_mapped(mock_client_cls, settings, mock_embeddings):
    mock_client_cls.side_effect = ConnectionError("refused")
    with pytest.raises(VectorStoreError, match="Failed to connect to Qdrant"):
        QdrantVectorAdapter(settings, mock_embeddings)


@patch("src.adapters.vector.qdrant_adapter.QdrantVectorStore")
@patch("src.adapters.vector.qdrant_adapter.QdrantClient")
def test_qdrant_url_used_when_set(mock_client_cls, mock_store_cls, mock_embeddings, monkeypatch):
    monkeypatch.setenv("QDRANT_URL", "http://qdrant:6333")
    settings = Settings(_env_file=None)
    mock_client = MagicMock()
    mock_client.collection_exists.return_value = False
    mock_client_cls.return_value = mock_client

    QdrantVectorAdapter(settings, mock_embeddings)
    mock_client_cls.assert_called_once_with(url="http://qdrant:6333")
