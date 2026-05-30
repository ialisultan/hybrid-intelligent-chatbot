"""SQL pipeline adapter tests."""

from unittest.mock import AsyncMock, MagicMock

import pytest

pytestmark = pytest.mark.unit

from src.adapters.persistence.sql_pipeline_adapter import LangChainSQLPipelineAdapter
from src.adapters.llm.chains.sql_chain import SQLSchema
from src.domain.entities.llm import LLMProvider
from src.domain.exceptions.base import DatabaseError
from src.infrastructure.config.settings import Settings


class MockChatModel:
    provider = LLMProvider.OPENAI

    def __init__(self) -> None:
        self.langchain_model = MagicMock()

    async def generate(self, system: str, user: str) -> str:
        return "Total revenue is $100."


class MockExecutor:
    def __init__(self) -> None:
        self.execute = AsyncMock(return_value=[{"total": 100}])
        self.get_schema_description = AsyncMock(
            return_value="Tables:\n- orders(id, amount, order_date)"
        )


@pytest.fixture
def adapter():
    chat_model = MockChatModel()
    executor = MockExecutor()
    pipeline = LangChainSQLPipelineAdapter(chat_model, executor, Settings())
    mock_chain = MagicMock()
    mock_chain.ainvoke = AsyncMock(
        return_value=SQLSchema(sql="SELECT SUM(amount) FROM orders", explanation="sum")
    )
    pipeline._chain = mock_chain
    return pipeline, executor, mock_chain


@pytest.mark.asyncio
async def test_run_fetches_schema_and_executes_sql(adapter):
    pipeline, executor, mock_chain = adapter
    result = await pipeline.run("Total revenue this month?")

    executor.get_schema_description.assert_awaited_once()
    mock_chain.ainvoke.assert_awaited_once()
    call_args = mock_chain.ainvoke.call_args[0][0]
    assert "schema" in call_args
    assert "orders" in call_args["schema"]
    executor.execute.assert_awaited_once_with("SELECT SUM(amount) FROM orders")
    assert result["sql_query"] == "SELECT SUM(amount) FROM orders"
    assert "100" in result["answer"]


@pytest.mark.asyncio
async def test_database_error_returns_safe_message(adapter):
    pipeline, executor, _mock_chain = adapter
    executor.execute.side_effect = DatabaseError("Only SELECT queries are allowed")

    result = await pipeline.run("DROP everything")

    assert result["sql_query"] is None
    assert "Unable to process this SQL query" in result["answer"]
    assert "DROP" not in result["answer"]


@pytest.mark.asyncio
async def test_stub_format_path():
    class StubChatModel(MockChatModel):
        provider = LLMProvider.STUB

    chat_model = StubChatModel()
    executor = MockExecutor()
    pipeline = LangChainSQLPipelineAdapter(chat_model, executor, Settings())
    mock_chain = MagicMock()
    mock_chain.ainvoke = AsyncMock(
        return_value=SQLSchema(sql="SELECT 1", explanation="test")
    )
    pipeline._chain = mock_chain

    result = await pipeline.run("test query")

    assert "Executed SQL: SELECT 1" in result["answer"]
    assert "Results:" in result["answer"]
