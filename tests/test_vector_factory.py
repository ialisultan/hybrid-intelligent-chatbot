"""Vector store factory tests."""

from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.unit

from langchain_community.embeddings import FakeEmbeddings
from src.adapters.vector.factory import create_vector_store
from src.adapters.vector.faiss_adapter import FaissVectorAdapter
from src.adapters.vector.qdrant_adapter import QdrantVectorAdapter
from src.infrastructure.config import Settings


@pytest.fixture
def embeddings():
    return FakeEmbeddings(size=1536)


def test_factory_returns_faiss_adapter(embeddings, tmp_path):
    settings = Settings(
        VECTOR_STORE_BACKEND="faiss",
        FAISS_INDEX_PATH=str(tmp_path / "faiss"),
    )
    store = create_vector_store(settings, embeddings)
    assert isinstance(store, FaissVectorAdapter)


def test_factory_returns_qdrant_adapter(embeddings):
    settings = Settings(
        VECTOR_STORE_BACKEND="qdrant",
        QDRANT_HOST="localhost",
        QDRANT_PORT=6333,
    )
    mock_store = MagicMock()
    with (
        patch("src.adapters.vector.qdrant_adapter.QdrantClient") as mock_client_cls,
        patch("src.adapters.vector.qdrant_adapter.QdrantVectorStore", return_value=mock_store),
    ):
        mock_client_cls.return_value.collection_exists.return_value = True
        store = create_vector_store(settings, embeddings)
    assert isinstance(store, QdrantVectorAdapter)


def test_factory_unknown_backend_raises(embeddings):
    settings = Settings(VECTOR_STORE_BACKEND="pinecone")
    with pytest.raises(ValueError, match="Unknown vector store backend"):
        create_vector_store(settings, embeddings)
