"""Qdrant vector store adapter — Docker-backed semantic search."""

import structlog
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.http.models import Distance, VectorParams

from src.application.ports.vector_store import VectorStorePort
from src.domain.entities.document import RetrievedDocument
from src.domain.exceptions.base import VectorStoreError
from src.infrastructure.config import Settings

logger = structlog.get_logger(__name__)

_DEFAULT_VECTOR_SIZE = 1536


class QdrantVectorAdapter(VectorStorePort):
    """LangChain QdrantVectorStore with auto-collection creation."""

    def __init__(self, settings: Settings, embeddings: Embeddings) -> None:
        self._settings = settings
        self._embeddings = embeddings
        self._client = self._create_client(settings)
        self._vector_size = self._probe_vector_size()
        self._store = self._init_store()

    @staticmethod
    def _create_client(settings: Settings) -> QdrantClient:
        try:
            if settings.qdrant_url:
                return QdrantClient(url=settings.qdrant_url)
            return QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
        except Exception as exc:
            raise VectorStoreError(
                f"Failed to connect to Qdrant at "
                f"{settings.qdrant_url or f'{settings.qdrant_host}:{settings.qdrant_port}'}: {exc}"
            ) from exc

    def _probe_vector_size(self) -> int:
        try:
            vector = self._embeddings.embed_query("probe")
            size = len(vector)
            logger.info("qdrant.vector_size_probed", size=size)
            return size
        except Exception as exc:
            logger.warning(
                "qdrant.vector_size_probe_failed",
                error=str(exc),
                fallback=_DEFAULT_VECTOR_SIZE,
            )
            return _DEFAULT_VECTOR_SIZE

    def _ensure_collection(self) -> None:
        collection = self._settings.qdrant_collection
        if self._client.collection_exists(collection):
            info = self._client.get_collection(collection)
            existing_size = info.config.params.vectors.size  # type: ignore[union-attr]
            if existing_size != self._vector_size:
                logger.warning(
                    "qdrant.dimension_mismatch",
                    collection=collection,
                    existing_size=existing_size,
                    expected_size=self._vector_size,
                )
            return

        self._client.create_collection(
            collection_name=collection,
            vectors_config=VectorParams(size=self._vector_size, distance=Distance.COSINE),
        )
        logger.info("qdrant.collection_created", collection=collection, size=self._vector_size)

    def _init_store(self) -> QdrantVectorStore:
        try:
            self._ensure_collection()
            return QdrantVectorStore(
                client=self._client,
                collection_name=self._settings.qdrant_collection,
                embedding=self._embeddings,
            )
        except VectorStoreError:
            raise
        except UnexpectedResponse as exc:
            raise VectorStoreError(
                f"Qdrant API error (status {exc.status_code}): {exc.content}"
            ) from exc
        except Exception as exc:
            raise VectorStoreError(f"Failed to initialise Qdrant vector store: {exc}") from exc

    @property
    def vectorstore(self) -> QdrantVectorStore:
        return self._store

    async def search(self, query: str, top_k: int = 5) -> list[RetrievedDocument]:
        try:
            results = await self._store.asimilarity_search_with_score(query, k=top_k)
        except UnexpectedResponse as exc:
            raise VectorStoreError(
                f"Qdrant search failed (status {exc.status_code}): {exc.content}"
            ) from exc
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
        except UnexpectedResponse as exc:
            raise VectorStoreError(
                f"Qdrant upsert failed (status {exc.status_code}): {exc.content}"
            ) from exc
        except Exception as exc:
            raise VectorStoreError(f"Qdrant upsert failed: {exc}") from exc
