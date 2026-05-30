"""FAISS adapter tests with FakeEmbeddings."""

import pytest

pytestmark = pytest.mark.unit

from langchain_community.embeddings import FakeEmbeddings
from langchain_core.documents import Document
from src.adapters.vector.faiss_adapter import FaissVectorAdapter
from src.infrastructure.config import Settings


@pytest.fixture
def faiss_adapter(tmp_path):
    settings = Settings(
        VECTOR_STORE_BACKEND="faiss",
        FAISS_INDEX_PATH=str(tmp_path / "faiss"),
    )
    return FaissVectorAdapter(settings, FakeEmbeddings(size=1536))


@pytest.mark.asyncio
async def test_faiss_upsert_and_search(faiss_adapter):
    docs = [
        Document(
            page_content="Return policy allows 30 day returns.",
            metadata={"source": "policy.md"},
        ),
        Document(
            page_content="Total revenue from orders table.",
            metadata={"source": "sql.md"},
        ),
    ]
    await faiss_adapter.upsert_langchain_documents(docs)

    results = await faiss_adapter.search("return policy", top_k=2)
    assert len(results) == 2
    sources = {r.source for r in results}
    assert sources == {"policy.md", "sql.md"}
    assert all(r.content for r in results)


@pytest.mark.asyncio
async def test_faiss_search_empty_index(tmp_path):
    settings = Settings(
        VECTOR_STORE_BACKEND="faiss",
        FAISS_INDEX_PATH=str(tmp_path / "empty_faiss"),
    )
    adapter = FaissVectorAdapter(settings, FakeEmbeddings(size=1536))
    results = await adapter.search("anything", top_k=3)
    assert results == []
