"""Vector pipeline — invokes LangChain RAG Runnable."""

import structlog
from langchain_core.runnables import Runnable

logger = structlog.get_logger(__name__)


class VectorPipeline:
    """LangGraph vector node target — runs LCEL RAG chain."""

    def __init__(self, rag_chain: Runnable) -> None:
        self._chain = rag_chain

    async def run(self, query: str) -> dict:
        logger.info("vector_pipeline.run", query=query[:80])
        result = await self._chain.ainvoke({"query": query})
        if isinstance(result, dict):
            return {
                "answer": result.get("answer", ""),
                "sources": result.get("sources", []),
            }
        return {"answer": str(result), "sources": []}
