"""Grounded RAG chain as LangChain LCEL Runnable."""

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableLambda, RunnablePassthrough
from langchain_core.vectorstores import VectorStoreRetriever


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


def build_vector_rag_chain(retriever: VectorStoreRetriever, llm: Runnable) -> Runnable:
    """Build LCEL RAG chain returning {answer, sources}."""
    rag_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a helpful assistant. Answer the user's question using ONLY "
                "the provided context. If the context does not contain enough "
                "information, say you don't know. Do not invent facts.",
            ),
            ("human", "Context:\n{context}\n\nQuestion: {query}"),
        ]
    )

    async def retrieve_and_answer(inputs: dict) -> dict:
        query = inputs["query"]
        docs = await retriever.ainvoke(query)
        context = _format_docs(docs)
        answer = await (rag_prompt | llm | StrOutputParser()).ainvoke(
            {"query": query, "context": context}
        )
        return {"answer": answer, "sources": _extract_sources(docs)}

    return RunnablePassthrough() | RunnableLambda(retrieve_and_answer)
