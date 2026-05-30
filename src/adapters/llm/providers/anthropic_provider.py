"""Anthropic chat model provider (no embeddings)."""

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from src.application.ports.chat_model import ChatModelPort
from src.domain.entities.llm import LLMProvider
from src.infrastructure.config.settings import Settings


class AnthropicChatModelAdapter(ChatModelPort):
    def __init__(self, settings: Settings) -> None:
        self._model = ChatAnthropic(
            model=settings.anthropic_model,
            api_key=settings.anthropic_api_key,
            temperature=0,
        )

    @property
    def provider(self) -> LLMProvider:
        return LLMProvider.ANTHROPIC

    @property
    def langchain_model(self) -> ChatAnthropic:
        return self._model

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        response = await self._model.ainvoke(
            [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
        )
        content = response.content
        return content if isinstance(content, str) else str(content)
