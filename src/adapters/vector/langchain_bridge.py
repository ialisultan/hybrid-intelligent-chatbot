"""Bridge VectorStorePort adapters to LangChain retrievers (adapter-internal)."""

from langchain_core.vectorstores import VectorStoreRetriever

from src.adapters.vector.faiss_adapter import FaissVectorAdapter
from src.adapters.vector.qdrant_adapter import QdrantVectorAdapter
from src.application.ports.vector_store import VectorStorePort
from src.domain.exceptions.base import VectorStoreError


def to_retriever(vector_store: VectorStorePort, top_k: int) -> VectorStoreRetriever:
    """Convert a concrete vector adapter to a LangChain retriever."""
    if isinstance(vector_store, FaissVectorAdapter | QdrantVectorAdapter):
        return vector_store.vectorstore.as_retriever(search_kwargs={"k": top_k})
    raise VectorStoreError(
        f"Unsupported vector store type for retriever bridge: {type(vector_store).__name__}"
    )
