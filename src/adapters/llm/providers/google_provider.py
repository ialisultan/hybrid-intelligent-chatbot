"""Google Gemini chat model and embedding provider."""

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from src.application.ports.chat_model import ChatModelPort
from src.application.ports.embedding import EmbeddingPort
from src.domain.entities.llm import LLMProvider
from src.infrastructure.config.settings import Settings


class GoogleChatModelAdapter(ChatModelPort):
    def __init__(self, settings: Settings) -> None:
        self._model = ChatGoogleGenerativeAI(
            model=settings.google_model,
            google_api_key=settings.google_api_key,
            temperature=0,
        )

    @property
    def provider(self) -> LLMProvider:
        return LLMProvider.GOOGLE

    @property
    def langchain_model(self) -> ChatGoogleGenerativeAI:
        return self._model

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        response = await self._model.ainvoke(
            [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
        )
        content = response.content
        return content if isinstance(content, str) else str(content)


class GoogleEmbeddingAdapter(EmbeddingPort):
    def __init__(self, settings: Settings) -> None:
        self._embeddings = GoogleGenerativeAIEmbeddings(
            model=settings.google_embedding_model,
            google_api_key=settings.google_api_key,
        )

    @property
    def provider(self) -> LLMProvider:
        return LLMProvider.GOOGLE

    @property
    def langchain_embeddings(self) -> GoogleGenerativeAIEmbeddings:
        return self._embeddings

    async def embed(self, text: str) -> list[float]:
        return await self._embeddings.aembed_query(text)
