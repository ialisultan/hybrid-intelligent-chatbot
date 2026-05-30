"""Vector store adapters — FAISS (local) and Qdrant (Docker)."""

from src.adapters.vector.factory import create_vector_store

__all__ = ["create_vector_store"]
