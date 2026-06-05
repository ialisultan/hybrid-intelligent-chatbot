"""Vector RAG LCEL chain tests."""

from unittest.mock import AsyncMock, MagicMock

import pytest

pytestmark = pytest.mark.unit

from langchain_core.documents import Document
from langchain_core.runnables import RunnableLambda

from src.adapters.llm.chains.vector_rag_chain import (
    _grounded_summary_from_context,
    _is_refusal_answer,
    build_vector_rag_chain,
)


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


def test_is_refusal_answer_detects_common_phrases():
    assert _is_refusal_answer("I don't know.")
    assert _is_refusal_answer("I do not have enough information.")
    assert not _is_refusal_answer("We offer a 30-day return policy on physical products.")


def test_grounded_summary_from_context_extracts_policy_lines():
    context = "# Return Policy\n\n30-day returns for unused items.\n\nRefunds in 5-7 days."
    answer = _grounded_summary_from_context(context)
    assert "30-day" in answer
    assert "Refunds" in answer
    assert "don't know" not in answer.lower()


@pytest.mark.asyncio
async def test_vector_rag_chain_fallback_when_llm_refuses_with_context():
    docs = [
        Document(
            page_content=(
                "We accept returns within 30 days. Refunds are processed in 5-7 business days."
            ),
            metadata={"source": "return_policy.md"},
        ),
    ]
    retriever = MagicMock()
    retriever.ainvoke = AsyncMock(return_value=docs)

    llm = RunnableLambda(lambda _: "I don't know.")

    chain = build_vector_rag_chain(retriever, llm)
    result = await chain.ainvoke({"query": "Tell me about orders policy"})

    assert "don't know" not in result["answer"].lower()
    assert "30" in result["answer"] or "return" in result["answer"].lower()
    assert "return_policy.md" in result["sources"]
