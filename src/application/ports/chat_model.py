"""Chat model port — text generation abstraction."""

from abc import ABC, abstractmethod
from typing import Any

from src.domain.entities.llm import LLMProvider


class ChatModelPort(ABC):
    """Generate text completions via an underlying LLM provider."""

    @property
    @abstractmethod
    def provider(self) -> LLMProvider:
        """Active provider identifier."""
        ...

    @property
    @abstractmethod
    def langchain_model(self) -> Any:
        """LangChain chat model for LCEL chain construction (adapter-internal leak)."""
        ...

    @abstractmethod
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        config: dict[str, Any] | None = None,
    ) -> str:
        """Return the LLM completion text."""
        ...
