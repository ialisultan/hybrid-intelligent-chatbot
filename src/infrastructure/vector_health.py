"""Vector store readiness probes for health endpoints."""

from pathlib import Path
from typing import Literal

import structlog

from src.adapters.vector.faiss_adapter import FaissVectorAdapter
from src.adapters.vector.pinecone_adapter import PineconeVectorAdapter
from src.adapters.vector.qdrant_adapter import QdrantVectorAdapter
from src.domain.entities.llm import LLMProvider
from src.infrastructure.config import Settings
from src.infrastructure.di import Container

logger = structlog.get_logger(__name__)

VectorHealthStatus = Literal["ok", "down", "skipped"]


def check_vector_health(container: Container, settings: Settings) -> VectorHealthStatus:
    """Return vector store readiness for the configured backend."""
    if container.chat_model and container.chat_model.provider == LLMProvider.STUB:
        return "skipped"

    backend = settings.vector_store_backend

    if backend == "faiss":
        index_file = Path(settings.faiss_index_path) / "index.faiss"
        return "ok" if index_file.exists() else "down"

    if backend == "qdrant":
        store = container.vector_store
        if not isinstance(store, QdrantVectorAdapter):
            return "down"
        try:
            if store._client.collection_exists(settings.qdrant_collection):  # noqa: SLF001
                info = store._client.get_collection(settings.qdrant_collection)  # noqa: SLF001
                return "ok" if info.points_count > 0 else "down"
            return "down"
        except Exception as exc:
            logger.warning("vector_health.qdrant_failed", error=str(exc))
            return "down"

    if backend == "pinecone":
        store = container.vector_store
        if not isinstance(store, PineconeVectorAdapter):
            return "down"
        try:
            return "ok" if store.vector_count() > 0 else "down"
        except Exception as exc:
            logger.warning("vector_health.pinecone_failed", error=str(exc))
            return "down"

    return "down"
