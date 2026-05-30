"""Stub LLM provider for development without API keys."""

from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.embeddings import FakeEmbeddings

from src.application.ports.chat_model import ChatModelPort
from src.application.ports.embedding import EmbeddingPort
from src.domain.entities.llm import LLMProvider


class StubChatModelAdapter(ChatModelPort):
    def __init__(self) -> None:
        self._model = FakeListChatModel(responses=["Stub LLM response."])

    @property
    def provider(self) -> LLMProvider:
        return LLMProvider.STUB

    @property
    def langchain_model(self) -> FakeListChatModel:
        return self._model

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        return f"[Stub] {user_prompt[:120]}"


class StubEmbeddingAdapter(EmbeddingPort):
    def __init__(self, size: int = 1536) -> None:
        self._embeddings = FakeEmbeddings(size=size)

    @property
    def provider(self) -> LLMProvider:
        return LLMProvider.STUB

    @property
    def langchain_embeddings(self) -> FakeEmbeddings:
        return self._embeddings

    async def embed(self, text: str) -> list[float]:
        return await self._embeddings.aembed_query(text)
