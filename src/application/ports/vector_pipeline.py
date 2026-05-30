"""Vector pipeline port — retrieval-augmented grounded response."""

from abc import ABC, abstractmethod


class VectorPipelinePort(ABC):
    """Port for the Vector LangGraph node — retrieves docs and generates grounded answers."""

    @abstractmethod
    async def run(self, query: str) -> dict:
        """Process a natural language query via the vector RAG pipeline.

        Returns:
            dict with keys ``answer`` (str) and ``sources`` (list[str]).
        """
