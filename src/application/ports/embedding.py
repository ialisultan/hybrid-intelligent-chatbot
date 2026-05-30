"""Embedding port — vector embedding abstraction."""

from abc import ABC, abstractmethod
from typing import Any

from src.domain.entities.llm import LLMProvider


class EmbeddingPort(ABC):
    """Embed text via an underlying provider."""

    @property
    @abstractmethod
    def provider(self) -> LLMProvider:
        """Active embedding provider identifier."""
        ...

    @property
    @abstractmethod
    def langchain_embeddings(self) -> Any:
        """LangChain embeddings for vector store adapters."""
        ...

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Return embedding vector for the given text."""
        ...
