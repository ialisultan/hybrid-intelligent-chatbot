"""LangChain LCEL chain factory — builds RAG and classifier chains."""

from langchain_core.runnables import Runnable

from src.adapters.llm.langchain_llm import LangChainLLMAdapter
from src.adapters.vector.langchain_bridge import to_retriever
from src.application.chains.classifier_chain import build_classifier_chain
from src.application.chains.vector_rag_chain import build_vector_rag_chain
from src.application.ports.vector_store import VectorStorePort
from src.infrastructure.config import Settings


def build_rag_chain(
    vector_store: VectorStorePort,
    llm: LangChainLLMAdapter,
    settings: Settings,
) -> Runnable:
    """Build grounded RAG LCEL chain from vector store port and LLM adapter."""
    retriever = to_retriever(vector_store, settings.vector_top_k)
    return build_vector_rag_chain(retriever, llm.chat_model)


def build_classifier_runnable(
    llm: LangChainLLMAdapter,
) -> Runnable:
    """Build query classifier LCEL chain."""
    return build_classifier_chain(llm.chat_model)
