"""Vector RAG LCEL chain tests."""

from unittest.mock import AsyncMock, MagicMock

import pytest

pytestmark = pytest.mark.unit

from langchain_core.documents import Document
from langchain_core.runnables import RunnableLambda

from src.adapters.llm.chains.vector_rag_chain import build_vector_rag_chain


@pytest.mark.asyncio
async def test_vector_rag_chain_returns_answer_and_sources():
    docs = [
        Document(
            page_content="30-day return policy applies.",
            metadata={"source": "return_policy.md"},
        ),
    ]
    retriever = MagicMock()
    retriever.ainvoke = AsyncMock(return_value=docs)

    llm = RunnableLambda(lambda _: "We offer a 30-day return policy.")

    chain = build_vector_rag_chain(retriever, llm)
    result = await chain.ainvoke({"query": "What is your return policy?"})

    assert "30-day" in result["answer"] or "return" in result["answer"].lower()
    assert "return_policy.md" in result["sources"]
