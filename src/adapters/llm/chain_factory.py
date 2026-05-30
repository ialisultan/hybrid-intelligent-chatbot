"""LangChain LCEL chain factory — builds RAG and classifier chains."""

from langchain_core.runnables import Runnable

from src.adapters.vector.langchain_bridge import to_retriever
from src.adapters.llm.chains.classifier_chain import build_classifier_chain
from src.adapters.llm.chains.vector_rag_chain import build_vector_rag_chain
from src.application.ports.chat_model import ChatModelPort
from src.application.ports.vector_store import VectorStorePort
from src.infrastructure.config.settings import Settings


def build_rag_chain(
    vector_store: VectorStorePort,
    chat_model: ChatModelPort,
    settings: Settings,
) -> Runnable:
    """Build grounded RAG LCEL chain from vector store port and chat model port."""
    retriever = to_retriever(vector_store, settings.vector_top_k)
    return build_vector_rag_chain(retriever, chat_model.langchain_model)


def build_classifier_runnable(chat_model: ChatModelPort) -> Runnable:
    """Build query classifier LCEL chain."""
    return build_classifier_chain(chat_model.langchain_model)
