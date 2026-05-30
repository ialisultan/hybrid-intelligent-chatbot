"""SQL pipeline — LangChain NL-to-SQL chain with stub execution."""

import structlog
from langchain_core.runnables import Runnable

from src.application.chains.sql_chain import SQLSchema

logger = structlog.get_logger(__name__)


class SQLPipeline:
    """LangGraph SQL node target — generates SQL via LCEL chain."""

    def __init__(self, sql_chain: Runnable) -> None:
        self._chain = sql_chain

    async def run(self, query: str) -> dict:
        logger.info("sql_pipeline.run", query=query[:80])
        try:
            result = await self._chain.ainvoke({"query": query})
            if isinstance(result, SQLSchema):
                sql = result.sql
                explanation = result.explanation
            elif isinstance(result, dict):
                sql = result.get("sql", "SELECT 1")
                explanation = result.get("explanation", "")
            else:
                sql = getattr(result, "sql", "SELECT 1")
                explanation = getattr(result, "explanation", "")

            # SQL execution against PostgreSQL will be wired in a follow-up.
            answer = (
                f"Generated SQL: {sql}"
                + (f"\n\n{explanation}" if explanation else "")
            )
            return {"answer": answer, "sql_query": sql}
        except Exception as exc:
            logger.warning("sql_pipeline.error", error=str(exc))
            return {
                "answer": f"Unable to process SQL query: {exc}",
                "sql_query": None,
            }
