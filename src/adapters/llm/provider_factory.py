"""Factory for multi-provider chat models and embeddings."""

from src.adapters.llm.providers.anthropic_provider import AnthropicChatModelAdapter
from src.adapters.llm.providers.google_provider import GoogleChatModelAdapter, GoogleEmbeddingAdapter
from src.adapters.llm.openai_adapter import OpenAIChatModelAdapter, OpenAIEmbeddingAdapter
from src.adapters.llm.providers.stub_provider import StubChatModelAdapter, StubEmbeddingAdapter
from src.application.ports.chat_model import ChatModelPort
from src.application.ports.embedding import EmbeddingPort
from src.domain.entities.llm import LLMProvider
from src.infrastructure.config.llm import resolve_active_providers, resolve_chat_provider, resolve_embedding_provider
from src.infrastructure.config.settings import Settings


def create_chat_model(settings: Settings) -> ChatModelPort:
    provider = resolve_chat_provider(settings)
    if provider == LLMProvider.OPENAI:
        return OpenAIChatModelAdapter(settings)
    if provider == LLMProvider.ANTHROPIC:
        return AnthropicChatModelAdapter(settings)
    if provider == LLMProvider.GOOGLE:
        return GoogleChatModelAdapter(settings)
    return StubChatModelAdapter()


def create_embeddings(settings: Settings) -> EmbeddingPort:
    provider = resolve_embedding_provider(settings)
    if provider == LLMProvider.OPENAI:
        return OpenAIEmbeddingAdapter(settings)
    if provider == LLMProvider.GOOGLE:
        return GoogleEmbeddingAdapter(settings)
    return StubEmbeddingAdapter()


def create_providers(settings: Settings) -> tuple[ChatModelPort, EmbeddingPort]:
    """Create chat model and embedding adapters based on key availability."""
    return create_chat_model(settings), create_embeddings(settings)
