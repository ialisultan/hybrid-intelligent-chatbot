"""Legacy facade — delegates to provider factory."""

from src.adapters.llm.provider_factory import create_providers
from src.application.ports.llm import LLMPort
from src.infrastructure.config.settings import Settings


class LangChainLLMAdapter(LLMPort):
    """Backward-compatible adapter composing chat model + embedding ports."""

    def __init__(self, settings: Settings) -> None:
        chat_model, embeddings = create_providers(settings)
        self._chat_model = chat_model
        self._embeddings = embeddings

    @property
    def provider(self):
        return self._chat_model.provider

    @property
    def langchain_model(self):
        return self._chat_model.langchain_model

    @property
    def chat_model(self):
        return self._chat_model.langchain_model

    @property
    def embeddings(self):
        return self._embeddings.langchain_embeddings

    @property
    def langchain_embeddings(self):
        return self._embeddings.langchain_embeddings

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        return await self._chat_model.generate(system_prompt, user_prompt)

    async def embed(self, text: str) -> list[float]:
        return await self._embeddings.embed(text)
