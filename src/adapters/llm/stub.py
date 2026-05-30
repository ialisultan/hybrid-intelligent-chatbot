"""Stub LLM adapters — used when no API keys are configured."""

from src.application.chains.classifier_chain import rule_based_classify
from src.application.ports.sql_pipeline import SQLPipelinePort
from src.application.ports.vector_pipeline import VectorPipelinePort
from src.domain.entities.chat import QueryRoute


class StubClassifier:
    """Classifier for stub mode — same rule-based logic as production fallback."""

    async def classify(self, query: str) -> QueryRoute:
        return rule_based_classify(query)


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
