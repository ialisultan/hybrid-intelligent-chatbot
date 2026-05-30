"""Bridge VectorStorePort adapters to LangChain retrievers (adapter-internal)."""

from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_core.vectorstores import VectorStoreRetriever
from pydantic import ConfigDict

from src.adapters.vector.faiss_adapter import FaissVectorAdapter
from src.adapters.vector.pinecone_adapter import PineconeVectorAdapter
from src.adapters.vector.qdrant_adapter import QdrantVectorAdapter
from src.application.ports.vector_store import VectorStorePort
from src.domain.exceptions.base import VectorStoreError


class PortVectorRetriever(BaseRetriever):
    """LangChain retriever backed by VectorStorePort.search (Pinecone SDK path)."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    vector_store: VectorStorePort
    top_k: int

    async def _aget_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun | None = None,
    ) -> list[Document]:
        results = await self.vector_store.search(query, top_k=self.top_k)
        return [
            Document(page_content=r.content, metadata={"source": r.source, "score": r.score})
            for r in results
        ]

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun | None = None,
    ) -> list[Document]:
        raise NotImplementedError("Use async retrieval via the vector RAG chain.")


def to_retriever(vector_store: VectorStorePort, top_k: int) -> VectorStoreRetriever | PortVectorRetriever:
    """Convert a concrete vector adapter to a LangChain retriever."""
    if isinstance(vector_store, FaissVectorAdapter | QdrantVectorAdapter):
        return vector_store.vectorstore.as_retriever(search_kwargs={"k": top_k})
    if isinstance(vector_store, PineconeVectorAdapter):
        return PortVectorRetriever(vector_store=vector_store, top_k=top_k)
    raise VectorStoreError(
        f"Unsupported vector store type for retriever bridge: {type(vector_store).__name__}"
    )
