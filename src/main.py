"""FastAPI application entry point.

Bootstraps the DI container on startup, registers API routes,
exception handlers, and middleware. Used by uvicorn and pytest.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded

from src.adapters.api.exception_handlers import (
    chatbot_error_handler,
    rate_limit_error_handler,
    unhandled_error_handler,
    validation_error_handler,
)
from src.adapters.api.middleware import RequestLoggingMiddleware
from src.adapters.api.rate_limit import register_rate_limiting
from src.adapters.api.router import api_router
from src.adapters.api.security_headers import SecurityHeadersMiddleware
from src.domain.exceptions.base import ChatbotError
from src.infrastructure.config import get_settings
from src.infrastructure.di import get_container
from src.infrastructure.logging import configure_logging
from src.infrastructure.tracing import configure_langsmith

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup / shutdown lifecycle — initialise DI container and DB engine."""
    settings = get_settings()
    configure_langsmith(settings)
    configure_logging(log_level=settings.log_level, json_output=settings.log_json)

    container = get_container()
    await container.init()
    logger.info(
        "app.startup",
        app_name=settings.app_name,
        env=settings.app_env,
    )

    yield

    await container.shutdown()
    logger.info("app.shutdown")


def _cors_origins(settings) -> list[str]:
    if settings.app_debug:
        origins = settings.cors_origins_list
        if origins:
            return origins
        return ["*"]
    return settings.cors_origins_list


def create_app() -> FastAPI:
    """Application factory — used by uvicorn and tests."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description=(
            "Hybrid Intelligent Chatbot with strict SQL vs Vector routing. "
            "Powered by FastAPI, LangGraph, LangChain, PostgreSQL, "
            "and configurable vector stores (FAISS, Qdrant, Pinecone)."
        ),
        version="0.1.0",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins(settings),
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestLoggingMiddleware)

    register_rate_limiting(app, settings)

    app.add_exception_handler(ChatbotError, chatbot_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(RateLimitExceeded, rate_limit_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)

    app.include_router(api_router)

    return app


app = create_app()
