"""Stub LLM adapters — replaced with real OpenAI/LangChain implementations."""

from src.application.ports.sql_pipeline import SQLPipelinePort
from src.application.ports.vector_pipeline import VectorPipelinePort
from src.domain.entities.chat import QueryRoute, RouteType


class StubClassifier:
    """Placeholder classifier for bootstrapping."""

    async def classify(self, query: str) -> QueryRoute:
        sql_keywords = {"total", "revenue", "orders", "customers", "top", "count", "sum", "list"}
        tokens = set(query.lower().split())
        if tokens & sql_keywords:
            return QueryRoute(route=RouteType.SQL, confidence=0.85, reasoning="keyword match")
        return QueryRoute(route=RouteType.VECTOR, confidence=0.85, reasoning="default vector")


class StubSQLPipeline(SQLPipelinePort):
    async def run(self, query: str) -> dict:
        return {
            "answer": f"[SQL stub] Processed: {query}",
            "sql_query": "SELECT 1",
        }


class StubVectorPipeline(VectorPipelinePort):
    async def run(self, query: str) -> dict:
        return {
            "answer": f"[Vector stub] Processed: {query}",
            "sources": ["stub-document-1"],
        }
