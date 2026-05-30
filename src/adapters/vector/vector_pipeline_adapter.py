"""LangChain vector pipeline adapter — retrieve → ground → respond.

Implements VectorPipelinePort. Builds a LangChain retriever from
VectorStorePort (FAISS or Qdrant), runs grounded RAG, and returns
answer + source citations.
"""

from typing import Any

import structlog
from langchain_core.runnables import Runnable

from src.adapters.vector.langchain_bridge import to_retriever
from src.adapters.llm.chains.vector_rag_chain import build_vector_rag_chain
from src.application.ports.chat_model import ChatModelPort
from src.application.ports.vector_pipeline import VectorPipelinePort
from src.application.ports.vector_store import VectorStorePort
from src.domain.exceptions.base import VectorStoreError
from src.infrastructure.config.settings import Settings
from src.infrastructure.tracing.langsmith import build_child_run_config

logger = structlog.get_logger(__name__)


class LangChainVectorPipelineAdapter(VectorPipelinePort):
    """Retrieves documents via VectorStorePort and generates grounded answers."""

    def __init__(
        self,
        vector_store: VectorStorePort,
        chat_model: ChatModelPort,
        settings: Settings,
    ) -> None:
        retriever = to_retriever(vector_store, settings.vector_top_k)
        self._chain: Runnable = build_vector_rag_chain(
            retriever, chat_model.langchain_model
        )

    async def run(
        self,
        query: str,
        *,
        config: dict[str, Any] | None = None,
    ) -> dict:
        logger.info("vector_pipeline.run", query=query[:80])
        try:
            rag_config = build_child_run_config(
                config,
                run_name="vector_rag",
                extra_metadata={"user_query": query},
            )
            result = await self._chain.ainvoke({"query": query}, config=rag_config)
            if isinstance(result, dict):
                return {
                    "answer": result.get("answer", ""),
                    "sources": result.get("sources", []),
                }
            return {"answer": str(result), "sources": []}
        except VectorStoreError as exc:
            logger.warning("vector_pipeline.vector_store_error", error=str(exc))
            return {
                "answer": "Unable to retrieve documents. Please try again later.",
                "sources": [],
            }
        except Exception as exc:
            logger.warning("vector_pipeline.error", error=str(exc))
            return {
                "answer": "Unable to process this question. Please try again later.",
                "sources": [],
            }
