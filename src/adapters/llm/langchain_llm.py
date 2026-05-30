"""LangChain-backed LLM adapter."""

from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from src.application.ports.llm import LLMPort
from src.infrastructure.config import Settings


class LangChainLLMAdapter(LLMPort):
    """Wraps LangChain ChatOpenAI and OpenAIEmbeddings behind LLMPort."""

    def __init__(self, settings: Settings) -> None:
        self._chat = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key or None,
            temperature=0,
        )
        self._embeddings = OpenAIEmbeddings(
            model=settings.openai_embedding_model,
            api_key=settings.openai_api_key or None,
        )

    @property
    def chat_model(self) -> ChatOpenAI:
        """Expose LangChain chat model for LCEL chain construction."""
        return self._chat

    @property
    def embeddings(self) -> OpenAIEmbeddings:
        """Expose LangChain embeddings for vector store adapters."""
        return self._embeddings

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        from langchain_core.messages import HumanMessage, SystemMessage

        response = await self._chat.ainvoke(
            [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
        )
        content = response.content
        return content if isinstance(content, str) else str(content)

    async def embed(self, text: str) -> list[float]:
        return await self._embeddings.aembed_query(text)
