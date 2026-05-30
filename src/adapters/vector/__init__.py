"""Vector store adapters — FAISS (local), Qdrant (Docker), and Pinecone (cloud)."""

from src.adapters.vector.factory import create_vector_store

__all__ = ["create_vector_store"]
