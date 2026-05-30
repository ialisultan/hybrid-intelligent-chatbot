"""Health check routes."""

from fastapi import APIRouter

from src.infrastructure.database import check_postgres_connection
from src.infrastructure.di import get_container
from src.interfaces.schemas.health import HealthResponse, ReadyResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    container = get_container()
    chat_provider = (
        container.chat_model.provider.value if container.chat_model else "uninitialised"
    )
    embedding_provider = (
        container.embeddings.provider.value if container.embeddings else "uninitialised"
    )
    return HealthResponse(
        status="ok",
        chat_provider=chat_provider,
        embedding_provider=embedding_provider,
    )


@router.get("/ready", response_model=ReadyResponse)
async def readiness_check() -> ReadyResponse:
    container = get_container()
    if not container._initialised:
        await container.init()

    postgres_ok = await check_postgres_connection()
    return ReadyResponse(
        status="ready" if postgres_ok else "degraded",
        postgres="ok" if postgres_ok else "down",
        chat_provider=container.chat_model.provider.value if container.chat_model else "stub",
        embedding_provider=(
            container.embeddings.provider.value if container.embeddings else "stub"
        ),
    )
