"""OpenAI chat model and embedding adapters."""

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from src.application.ports.chat_model import ChatModelPort
from src.application.ports.embedding import EmbeddingPort
from src.domain.entities.llm import LLMProvider
from src.infrastructure.config.settings import Settings


class OpenAIChatModelAdapter(ChatModelPort):
    """OpenAI chat completions behind ChatModelPort."""

    def __init__(self, settings: Settings) -> None:
        self._model = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0,
        )

    @property
    def provider(self) -> LLMProvider:
        return LLMProvider.OPENAI

    @property
    def langchain_model(self) -> ChatOpenAI:
        return self._model

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        response = await self._model.ainvoke(
            [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
        )
        content = response.content
        return content if isinstance(content, str) else str(content)


class OpenAIEmbeddingAdapter(EmbeddingPort):
    """OpenAI embeddings behind EmbeddingPort."""

    def __init__(self, settings: Settings) -> None:
        self._embeddings = OpenAIEmbeddings(
            model=settings.openai_embedding_model,
            api_key=settings.openai_api_key,
        )

    @property
    def provider(self) -> LLMProvider:
        return LLMProvider.OPENAI

    @property
    def langchain_embeddings(self) -> OpenAIEmbeddings:
        return self._embeddings

    async def embed(self, text: str) -> list[float]:
        return await self._embeddings.aembed_query(text)
