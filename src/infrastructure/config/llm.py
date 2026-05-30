"""LLM provider resolution helpers."""

from src.domain.entities.llm import LLMProvider
from src.infrastructure.config.settings import Settings


def _has_key(settings: Settings, provider: LLMProvider) -> bool:
    if provider == LLMProvider.OPENAI:
        return bool(settings.openai_api_key)
    if provider == LLMProvider.ANTHROPIC:
        return bool(settings.anthropic_api_key)
    if provider == LLMProvider.GOOGLE:
        return bool(settings.google_api_key)
    return False


def resolve_chat_provider(settings: Settings) -> LLMProvider:
    """Resolve chat model provider from settings and available API keys."""
    configured = settings.llm_provider.lower()
    if configured != "auto":
        provider = LLMProvider(configured)
        if provider == LLMProvider.STUB or _has_key(settings, provider):
            return provider
        raise ValueError(f"LLM_PROVIDER={configured} but API key is missing")

    for name in settings.llm_priority_list:
        try:
            provider = LLMProvider(name)
        except ValueError:
            continue
        if _has_key(settings, provider):
            return provider

    return LLMProvider.STUB


def resolve_embedding_provider(settings: Settings) -> LLMProvider:
    """Resolve embedding provider — OpenAI or Google only (Anthropic has no embeddings)."""
    configured = settings.embedding_provider.lower()
    if configured != "auto":
        provider = LLMProvider(configured)
        if provider == LLMProvider.ANTHROPIC:
            raise ValueError("Anthropic does not provide embedding models")
        if provider == LLMProvider.STUB:
            return provider
        if not _has_key(settings, provider):
            raise ValueError(f"EMBEDDING_PROVIDER={configured} but API key is missing")
        return provider

    if settings.openai_api_key:
        return LLMProvider.OPENAI
    if settings.google_api_key:
        return LLMProvider.GOOGLE
    return LLMProvider.STUB


def resolve_active_providers(settings: Settings) -> tuple[LLMProvider, LLMProvider]:
    """Return (chat_provider, embedding_provider)."""
    return resolve_chat_provider(settings), resolve_embedding_provider(settings)
