"""LangChain SQL pipeline adapter — NL → safe SQL → execute → format.

Implements SQLPipelinePort. Fetches live schema from SQLExecutorPort,
generates read-only SELECT via LangChain structured output, executes
through PostgresAdapter, and formats results via ChatModelPort.
"""

import json
from typing import Any

import structlog
from langchain_core.runnables import Runnable

from src.adapters.llm.chains.sql_chain import SQLSchema, build_sql_chain
from src.application.ports.chat_model import ChatModelPort
from src.application.ports.sql_executor import SQLExecutorPort
from src.application.ports.sql_pipeline import SQLPipelinePort
from src.domain.entities.llm import LLMProvider
from src.domain.exceptions.base import DatabaseError
from src.infrastructure.config.settings import Settings
from src.infrastructure.tracing.langsmith import (
    build_child_run_config,
    resolve_thread_id_from_config,
)

logger = structlog.get_logger(__name__)


class LangChainSQLPipelineAdapter(SQLPipelinePort):
    """Generates read-only SQL, executes via SQLExecutorPort, formats via ChatModelPort."""

    def __init__(
        self,
        chat_model: ChatModelPort,
        sql_executor: SQLExecutorPort,
        _settings: Settings,
    ) -> None:
        self._executor = sql_executor
        self._chat_model = chat_model
        self._chain: Runnable = build_sql_chain(
            chat_model.langchain_model,
            dialect=_settings.sql_dialect,
        )

    async def run(
        self,
        query: str,
        *,
        config: dict[str, Any] | None = None,
    ) -> dict:
        logger.info("sql_pipeline.run", query=query[:80])
        try:
            schema = await self._executor.get_schema_description()
            logger.info("sql_pipeline.schema_loaded", schema_length=len(schema))

            sql_config = build_child_run_config(
                config,
                run_name="sql_generation",
                extra_metadata={"user_query": query},
                thread_id=resolve_thread_id_from_config(config),
            )
            result = await self._chain.ainvoke(
                {"query": query, "schema": schema},
                config=sql_config,
            )
            sql = self._extract_sql(result)
            logger.info("sql_pipeline.generated", sql=sql[:120])

            rows = await self._executor.execute(sql)
            answer = await self._format_answer(query, sql, rows, config=config)
            return {"answer": answer, "sql_query": sql}
        except DatabaseError as exc:
            logger.warning("sql_pipeline.database_error", error=str(exc))
            return {
                "answer": "Unable to process this SQL query. Please rephrase your question.",
                "sql_query": None,
            }
        except Exception as exc:
            logger.warning("sql_pipeline.error", error=str(exc))
            return {
                "answer": "Unable to process this SQL query. Please try again later.",
                "sql_query": None,
            }

    @staticmethod
    def _extract_sql(result: object) -> str:
        if isinstance(result, SQLSchema):
            return result.sql
        if isinstance(result, dict):
            return str(result.get("sql", "SELECT 1"))
        return str(getattr(result, "sql", "SELECT 1"))

    async def _format_answer(
        self,
        query: str,
        sql: str,
        rows: list[dict],
        *,
        config: dict[str, Any] | None = None,
    ) -> str:
        if self._chat_model.provider == LLMProvider.STUB:
            preview = json.dumps(rows[:5], default=str)
            return f"Executed SQL: {sql}\nResults: {preview}"

        system = (
            "Format SQL query results as a clear, concise natural language answer. "
            "Use the user question and result rows only."
        )
        user = f"Question: {query}\nSQL: {sql}\nRows: {json.dumps(rows, default=str)}"
        format_config = build_child_run_config(
            config,
            run_name="sql_answer_formatting",
            extra_metadata={"user_query": query},
            thread_id=resolve_thread_id_from_config(config),
        )
        return await self._chat_model.generate(system, user, config=format_config)
