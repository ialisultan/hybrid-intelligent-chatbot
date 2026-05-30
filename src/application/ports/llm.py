"""LLM port — text generation abstraction."""

from abc import ABC, abstractmethod


class LLMPort(ABC):
    """Generate text completions via an underlying LLM provider."""

    @abstractmethod
    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Return the LLM completion text."""
        ...

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Return embedding vector for the given text."""
        ...
