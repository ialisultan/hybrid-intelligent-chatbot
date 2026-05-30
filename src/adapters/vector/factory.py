"""Vector store factory — selects FAISS, Qdrant, or Pinecone backend."""

from langchain_core.embeddings import Embeddings

from src.adapters.vector.faiss_adapter import FaissVectorAdapter
from src.adapters.vector.pinecone_adapter import PineconeVectorAdapter
from src.adapters.vector.qdrant_adapter import QdrantVectorAdapter
from src.application.ports.vector_store import VectorStorePort
from src.infrastructure.config import Settings


def create_vector_store(
    settings: Settings,
    embeddings: Embeddings,
) -> VectorStorePort:
    """Return the configured vector store adapter."""
    backend = settings.vector_store_backend
    if backend == "faiss":
        return FaissVectorAdapter(settings, embeddings)
    if backend == "qdrant":
        return QdrantVectorAdapter(settings, embeddings)
    if backend == "pinecone":
        return PineconeVectorAdapter(settings, embeddings)
    raise ValueError(f"Unknown vector store backend: {backend}")
