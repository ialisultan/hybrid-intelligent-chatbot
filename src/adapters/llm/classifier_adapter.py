"""Deprecated — use LLMQueryClassifier from query_classifier.py."""

from src.adapters.llm.query_classifier import LLMQueryClassifier

LangChainClassifierAdapter = LLMQueryClassifier

__all__ = ["LangChainClassifierAdapter", "LLMQueryClassifier"]
