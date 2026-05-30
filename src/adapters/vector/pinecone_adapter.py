"""Pinecone vector store adapter — managed cloud semantic search (Pinecone SDK)."""

from uuid import uuid4

import structlog
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from pinecone import Pinecone

from src.application.ports.vector_store import VectorStorePort
from src.domain.entities.document import RetrievedDocument
from src.domain.exceptions.base import VectorStoreError
from src.infrastructure.config import Settings

logger = structlog.get_logger(__name__)


class PineconeVectorAdapter(VectorStorePort):
    """Pinecone index access via the official SDK and LangChain embeddings."""

    def __init__(self, settings: Settings, embeddings: Embeddings) -> None:
        self._settings = settings
        self._embeddings = embeddings
        self._namespace = settings.pinecone_namespace or None
        try:
            self._pinecone = Pinecone(api_key=settings.pinecone_api_key)
            self._index = self._pinecone.Index(settings.pinecone_index)
            logger.info(
                "pinecone.initialised",
                index=settings.pinecone_index,
                namespace=self._namespace or "(default)",
            )
        except Exception as exc:
            raise VectorStoreError(f"Failed to initialise Pinecone vector store: {exc}") from exc

    @property
    def pinecone_index(self):
        """Underlying Pinecone index handle (health checks, stats)."""
        return self._index

    def vector_count(self) -> int:
        """Return total vectors in the index (all namespaces)."""
        try:
            stats = self._index.describe_index_stats()
            return int(getattr(stats, "total_vector_count", 0) or 0)
        except Exception:
            return 0

    async def search(self, query: str, top_k: int = 5) -> list[RetrievedDocument]:
        try:
            vector = self._embeddings.embed_query(query)
            response = self._index.query(
                vector=vector,
                top_k=top_k,
                include_metadata=True,
                namespace=self._namespace,
            )
        except Exception as exc:
            raise VectorStoreError(f"Pinecone search failed: {exc}") from exc

        matches = getattr(response, "matches", None) or response.get("matches", [])
        documents: list[RetrievedDocument] = []
        for match in matches:
            metadata = getattr(match, "metadata", None) or match.get("metadata") or {}
            content = metadata.get("text") or metadata.get("content") or ""
            score = getattr(match, "score", None)
            if score is None and isinstance(match, dict):
                score = match.get("score", 0.0)
            documents.append(
                RetrievedDocument(
                    content=str(content),
                    source=str(metadata.get("source", "unknown")),
                    score=float(score or 0.0),
                )
            )
        return documents

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
            texts = [doc.page_content for doc in documents]
            vectors = self._embeddings.embed_documents(texts)
            records = []
            for doc, values in zip(documents, vectors, strict=True):
                metadata = dict(doc.metadata)
                metadata["text"] = doc.page_content
                records.append(
                    {
                        "id": str(uuid4()),
                        "values": values,
                        "metadata": metadata,
                    }
                )
            self._index.upsert(vectors=records, namespace=self._namespace)
            logger.info("pinecone.upserted", count=len(records))
        except Exception as exc:
            raise VectorStoreError(f"Pinecone upsert failed: {exc}") from exc
