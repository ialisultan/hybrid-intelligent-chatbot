"""FAISS vector store adapter — local file-backed index."""

from pathlib import Path

import structlog
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from src.application.ports.vector_store import RetrievedDocument, VectorStorePort
from src.domain.exceptions.base import VectorStoreError
from src.infrastructure.config import Settings

logger = structlog.get_logger(__name__)


class FaissVectorAdapter(VectorStorePort):
    """LangChain FAISS vectorstore with local persistence."""

    def __init__(self, settings: Settings, embeddings: OpenAIEmbeddings) -> None:
        self._settings = settings
        self._embeddings = embeddings
        self._index_path = Path(settings.faiss_index_path)
        self._store: FAISS | None = None
        self._load_or_init()

    @property
    def vectorstore(self) -> FAISS:
        if self._store is None:
            raise VectorStoreError("FAISS index is not initialised")
        return self._store

    def _load_or_init(self) -> None:
        index_file = self._index_path / "index.faiss"
        if index_file.exists():
            try:
                self._store = FAISS.load_local(
                    str(self._index_path),
                    self._embeddings,
                    allow_dangerous_deserialization=True,
                )
                logger.info("faiss.loaded", path=str(self._index_path))
            except Exception as exc:
                raise VectorStoreError(f"Failed to load FAISS index: {exc}") from exc
        else:
            self._store = None
            logger.info("faiss.empty", path=str(self._index_path))

    def _save(self) -> None:
        if self._store is None:
            return
        self._index_path.mkdir(parents=True, exist_ok=True)
        self._store.save_local(str(self._index_path))

    async def search(self, query: str, top_k: int = 5) -> list[RetrievedDocument]:
        if self._store is None:
            return []
        try:
            results = await self._store.asimilarity_search_with_score(query, k=top_k)
        except Exception as exc:
            raise VectorStoreError(f"FAISS search failed: {exc}") from exc

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
        try:
            if self._store is None:
                self._store = await FAISS.afrom_documents(docs, self._embeddings)
            else:
                await self._store.aadd_documents(docs)
            self._save()
            logger.info("faiss.upserted", count=len(docs))
        except Exception as exc:
            raise VectorStoreError(f"FAISS upsert failed: {exc}") from exc

    async def upsert_langchain_documents(self, documents: list[Document]) -> None:
        """Index LangChain Document objects directly (used by index_documents)."""
        if not documents:
            return
        try:
            if self._store is None:
                self._store = await FAISS.afrom_documents(documents, self._embeddings)
            else:
                await self._store.aadd_documents(documents)
            self._save()
            logger.info("faiss.upserted", count=len(documents))
        except Exception as exc:
            raise VectorStoreError(f"FAISS upsert failed: {exc}") from exc
