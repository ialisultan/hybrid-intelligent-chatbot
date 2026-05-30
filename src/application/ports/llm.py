"""Legacy LLM port — composes ChatModelPort + EmbeddingPort."""

from src.application.ports.chat_model import ChatModelPort
from src.application.ports.embedding import EmbeddingPort


class LLMPort(ChatModelPort, EmbeddingPort):
    """Combined chat + embedding port for backward compatibility."""
