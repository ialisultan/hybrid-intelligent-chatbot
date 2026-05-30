"""Qdrant vector store adapter — Docker-backed semantic search."""

import structlog
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

from src.application.ports.vector_store import RetrievedDocument, VectorStorePort
from src.domain.exceptions.base import VectorStoreError
from src.infrastructure.config import Settings

logger = structlog.get_logger(__name__)


class QdrantVectorAdapter(VectorStorePort):
    """LangChain QdrantVectorStore with auto-collection creation."""

    def __init__(self, settings: Settings, embeddings: OpenAIEmbeddings) -> None:
        self._settings = settings
        self._embeddings = embeddings
        self._client = QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
        )
        self._store = self._init_store()

    def _ensure_collection(self) -> None:
        collection = self._settings.qdrant_collection
        if self._client.collection_exists(collection):
            return
        # text-embedding-3-small dimension
        vector_size = 1536
        self._client.create_collection(
            collection_name=collection,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )
        logger.info("qdrant.collection_created", collection=collection)

    def _init_store(self) -> QdrantVectorStore:
        try:
            self._ensure_collection()
            return QdrantVectorStore(
                client=self._client,
                collection_name=self._settings.qdrant_collection,
                embedding=self._embeddings,
            )
        except Exception as exc:
            raise VectorStoreError(f"Failed to connect to Qdrant: {exc}") from exc

    @property
    def vectorstore(self) -> QdrantVectorStore:
        return self._store

    async def search(self, query: str, top_k: int = 5) -> list[RetrievedDocument]:
        try:
            results = await self._store.asimilarity_search_with_score(query, k=top_k)
        except Exception as exc:
            raise VectorStoreError(f"Qdrant search failed: {exc}") from exc

        return [
            RetrievedDocument(
                content=doc.page_content,
                source=doc.metadata.get("source", "unknown"),
                score=float(score),
            )
            for doc, score in results
        ]

    async def upsert_documents(self, documents: list[dict]) -> None:
        if not documents:
            return
        docs = [
            Document(page_content=d["content"], metadata=d.get("metadata", {}))
            for d in documents
        ]
        await self.upsert_langchain_documents(docs)

    async def upsert_langchain_documents(self, documents: list[Document]) -> None:
        if not documents:
            return
        try:
            await self._store.aadd_documents(documents)
            logger.info("qdrant.upserted", count=len(documents))
        except Exception as exc:
            raise VectorStoreError(f"Qdrant upsert failed: {exc}") from exc
