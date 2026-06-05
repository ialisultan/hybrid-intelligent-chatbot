"""Grounded RAG chain as LangChain LCEL Runnable."""

import re

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import (
    Runnable,
    RunnableConfig,
    RunnableLambda,
    RunnablePassthrough,
)
from langchain_core.vectorstores import VectorStoreRetriever

RAG_SYSTEM_PROMPT = (
    "You are a helpful customer support assistant. Answer the user's question using ONLY "
    "the provided context.\n\n"
    "Rules:\n"
    "- Use related information even when wording differs (e.g. questions about "
    "'orders policy' may be answered from return, shipping, or FAQ sections).\n"
    "- For broad or vague questions, summarize the relevant policies, steps, and "
    "timelines from the context.\n"
    "- Be concise and practical; bullet points are fine.\n"
    "- Only say you do not have enough information when the context is empty or "
    "completely unrelated to the question.\n"
    "- Never invent facts not supported by the context."
)

EDGE_RETRY_SYSTEM_PROMPT = (
    "The user asked an indirect or vague support question. The context was retrieved "
    "as relevant documentation. Summarize the applicable policies and guidance "
    "(returns, refunds, orders, shipping, warranty, or support). "
    "Do not refuse or say you don't know — explain what the documents state."
)

_REFUSAL_PHRASES = (
    "i don't know",
    "i do not know",
    "don't know",
    "do not know",
    "not enough information",
    "do not have enough information",
    "no information in the context",
    "cannot answer",
    "can't answer",
    "unable to answer",
    "does not contain",
    "doesn't contain",
)


def _format_docs(docs: list[Document]) -> str:
    return "\n\n".join(doc.page_content for doc in docs)


def _extract_sources(docs: list[Document]) -> list[str]:
    seen: set[str] = set()
    sources: list[str] = []
    for doc in docs:
        source = doc.metadata.get("source", "unknown")
        if source not in seen:
            seen.add(source)
            sources.append(source)
    return sources


def _is_refusal_answer(answer: str) -> bool:
    normalized = answer.strip().lower()
    if not normalized:
        return True
    return any(phrase in normalized for phrase in _REFUSAL_PHRASES)


def _grounded_summary_from_context(context: str) -> str:
    """Extractive fallback when the LLM refuses despite non-empty retrieved context."""
    lines: list[str] = []
    for raw in context.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        line = re.sub(r"^#+\s*", "", line)
        line = re.sub(r"^\*\*|\*\*$", "", line).strip()
        if line:
            lines.append(line)
    if not lines:
        return (
            "I could not find a clear answer in the documentation for that question. "
            "Please contact support@example.com for help."
        )
    body = "\n".join(f"- {line}" if not line.startswith("-") else line for line in lines[:14])
    return (
        "Here's what our documentation says that's relevant to your question:\n\n"
        f"{body}"
    )


def build_vector_rag_chain(retriever: VectorStoreRetriever, llm: Runnable) -> Runnable:
    """Build LCEL RAG chain returning {answer, sources}."""
    rag_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", RAG_SYSTEM_PROMPT),
            ("human", "Context:\n{context}\n\nQuestion: {query}"),
        ]
    )
    edge_retry_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", EDGE_RETRY_SYSTEM_PROMPT),
            ("human", "Context:\n{context}\n\nQuestion: {query}"),
        ]
    )
    answer_chain = rag_prompt | llm | StrOutputParser()
    edge_chain = edge_retry_prompt | llm | StrOutputParser()

    async def retrieve_and_answer(
        inputs: dict,
        config: RunnableConfig | None = None,
    ) -> dict:
        query = inputs["query"]
        docs = await retriever.ainvoke(query, config=config)
        context = _format_docs(docs)
        sources = _extract_sources(docs)

        if not context.strip():
            return {
                "answer": (
                    "I don't have enough information in the documentation to answer that. "
                    "Please contact support@example.com."
                ),
                "sources": sources,
            }

        answer = await answer_chain.ainvoke(
            {"query": query, "context": context},
            config=config,
        )
        if _is_refusal_answer(answer):
            answer = await edge_chain.ainvoke(
                {"query": query, "context": context},
                config=config,
            )
        if _is_refusal_answer(answer):
            answer = _grounded_summary_from_context(context)

        return {"answer": answer, "sources": sources}

    return RunnablePassthrough() | RunnableLambda(retrieve_and_answer)
