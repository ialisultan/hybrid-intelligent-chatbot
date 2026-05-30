"""SQL pipeline port — NL to safe SQL execution and formatted answer."""

from abc import ABC, abstractmethod


class SQLPipelinePort(ABC):
    """Port for the SQL LangGraph node — generates, executes, and formats SQL results."""

    @abstractmethod
    async def run(self, query: str) -> dict:
        """Process a natural language query via the SQL pipeline.

        Returns:
            dict with keys ``answer`` (str) and ``sql_query`` (str | None).
        """
