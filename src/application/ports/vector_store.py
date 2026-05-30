"""Vector store port — semantic document retrieval."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RetrievedDocument:
    """A document chunk retrieved from the vector store."""

    content: str
    source: str
    score: float


class VectorStorePort(ABC):
    """Embed queries and retrieve top-k relevant documents."""

    @abstractmethod
    async def search(self, query: str, top_k: int = 5) -> list[RetrievedDocument]:
        """Return ranked document chunks for the query."""
        ...

    @abstractmethod
    async def upsert_documents(self, documents: list[dict]) -> None:
        """Index documents into the vector store."""
        ...
