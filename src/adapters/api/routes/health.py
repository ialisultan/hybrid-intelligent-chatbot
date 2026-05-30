"""Health check routes."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from src.infrastructure.config import get_settings
from src.infrastructure.database import check_postgres_connection
from src.infrastructure.di import get_container
from src.infrastructure.vector_health import check_vector_health
from src.interfaces.schemas.health import HealthResponse, ReadyResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Liveness probe — process is running (no dependency checks)."""
    settings = get_settings()
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
        vector_backend=settings.vector_store_backend,
    )


@router.get("/ready", response_model=ReadyResponse)
async def readiness_check() -> JSONResponse:
    """Readiness probe — returns 503 when dependencies are unavailable."""
    settings = get_settings()
    container = get_container()

    postgres_ok = await check_postgres_connection()
    vector_status = check_vector_health(container, settings)
    ready = postgres_ok and vector_status in {"ok", "skipped"}

    body = ReadyResponse(
        status="ready" if ready else "degraded",
        postgres="ok" if postgres_ok else "down",
        vector=vector_status,
        chat_provider=container.chat_model.provider.value if container.chat_model else "stub",
        embedding_provider=(
            container.embeddings.provider.value if container.embeddings else "stub"
        ),
        vector_backend=settings.vector_store_backend,
    )
    status_code = 200 if ready else 503
    return JSONResponse(status_code=status_code, content=body.model_dump())
