"""LLM provider domain enum."""

from enum import StrEnum


class LLMProvider(StrEnum):
    """Supported LLM / embedding providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    STUB = "stub"
