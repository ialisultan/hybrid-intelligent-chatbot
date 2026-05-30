"""Backward-compatible re-exports — prefer openai_adapter.py."""

from src.adapters.llm.openai_adapter import OpenAIChatModelAdapter, OpenAIEmbeddingAdapter

__all__ = ["OpenAIChatModelAdapter", "OpenAIEmbeddingAdapter"]
