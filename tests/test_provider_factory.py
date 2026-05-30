"""Provider factory auto-selection tests."""

import pytest

pytestmark = pytest.mark.unit

from src.adapters.llm.provider_factory import create_chat_model, create_embeddings
from src.domain.entities.llm import LLMProvider
from src.infrastructure.config.settings import Settings


def _settings(**overrides: str) -> Settings:
    base = {
        "OPENAI_API_KEY": "",
        "ANTHROPIC_API_KEY": "",
        "GOOGLE_API_KEY": "",
        "LLM_PROVIDER": "auto",
        "EMBEDDING_PROVIDER": "auto",
    }
    base.update(overrides)
    return Settings(**base)


def test_auto_selects_openai_when_key_present():
    settings = _settings(OPENAI_API_KEY="sk-test")
    assert create_chat_model(settings).provider == LLMProvider.OPENAI
    assert create_embeddings(settings).provider == LLMProvider.OPENAI


def test_auto_selects_anthropic_for_chat_when_only_anthropic_key():
    settings = _settings(ANTHROPIC_API_KEY="anthropic-test")
    assert create_chat_model(settings).provider == LLMProvider.ANTHROPIC
    assert create_embeddings(settings).provider == LLMProvider.STUB


def test_auto_selects_google_embeddings_when_only_google_key():
    settings = _settings(GOOGLE_API_KEY="google-test")
    assert create_chat_model(settings).provider == LLMProvider.GOOGLE
    assert create_embeddings(settings).provider == LLMProvider.GOOGLE


def test_stub_when_no_keys():
    settings = _settings()
    assert create_chat_model(settings).provider == LLMProvider.STUB
    assert create_embeddings(settings).provider == LLMProvider.STUB


def test_explicit_embedding_openai_with_anthropic_chat():
    settings = _settings(
        LLM_PROVIDER="anthropic",
        EMBEDDING_PROVIDER="openai",
        ANTHROPIC_API_KEY="anthropic-test",
        OPENAI_API_KEY="sk-test",
    )
    assert create_chat_model(settings).provider == LLMProvider.ANTHROPIC
    assert create_embeddings(settings).provider == LLMProvider.OPENAI


def test_anthropic_embedding_raises():
    settings = _settings(EMBEDDING_PROVIDER="anthropic", ANTHROPIC_API_KEY="key")
    with pytest.raises(ValueError, match="Anthropic does not provide"):
        create_embeddings(settings)
