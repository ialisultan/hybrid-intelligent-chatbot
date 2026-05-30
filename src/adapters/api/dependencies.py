"""FastAPI dependency injection helpers."""

from src.application.ports.classifier import ClassifierPort
from src.application.usecases.chat import ChatUseCase
from src.infrastructure.config import Settings, get_settings
from src.infrastructure.di import get_container


def get_app_settings() -> Settings:
    return get_settings()


async def get_chat_use_case() -> ChatUseCase:
    container = get_container()
    if not container._initialised or container.chat_use_case is None:
        await container.init()
    assert container.chat_use_case is not None
    return container.chat_use_case


async def get_classifier() -> ClassifierPort:
    container = get_container()
    if not container._initialised or container.classifier is None:
        await container.init()
    assert container.classifier is not None
    return container.classifier
