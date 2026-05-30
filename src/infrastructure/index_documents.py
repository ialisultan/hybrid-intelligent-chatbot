"""Index document corpus into the active vector store backend."""

import asyncio

import structlog

from src.adapters.llm.langchain_llm import LangChainLLMAdapter
from src.adapters.vector.document_loader import load_and_chunk_documents
from src.adapters.vector.factory import create_vector_store
from src.adapters.vector.faiss_adapter import FaissVectorAdapter
from src.adapters.vector.qdrant_adapter import QdrantVectorAdapter
from src.infrastructure.config import get_settings
from src.infrastructure.logging import configure_logging

logger = structlog.get_logger(__name__)


async def index_documents(data_dir: str = "data") -> None:
    settings = get_settings()
    configure_logging(log_level=settings.log_level, json_output=settings.log_json)

    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is required to embed documents")

    llm = LangChainLLMAdapter(settings)
    vector_store = create_vector_store(settings, llm.embeddings)
    documents = load_and_chunk_documents(data_dir)

    if not documents:
        logger.warning("index.no_documents", data_dir=data_dir)
        return

    if isinstance(vector_store, FaissVectorAdapter | QdrantVectorAdapter):
        await vector_store.upsert_langchain_documents(documents)
    else:
        await vector_store.upsert_documents(
            [{"content": d.page_content, "metadata": d.metadata} for d in documents]
        )

    logger.info(
        "index.complete",
        backend=settings.vector_store_backend,
        chunks=len(documents),
    )


if __name__ == "__main__":
    asyncio.run(index_documents())
