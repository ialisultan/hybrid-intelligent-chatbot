"""Global exception handlers for domain errors."""

import structlog
from fastapi import Request
from fastapi.responses import JSONResponse

from src.domain.exceptions.base import ChatbotError

logger = structlog.get_logger(__name__)


async def chatbot_error_handler(_request: Request, exc: ChatbotError) -> JSONResponse:
    logger.warning("api.error", code=exc.code, message=exc.message)
    status_map = {
        "CLASSIFICATION_ERROR": 422,
        "ROUTING_VIOLATION": 500,
        "SQL_PIPELINE_ERROR": 502,
        "VECTOR_PIPELINE_ERROR": 502,
        "DATABASE_ERROR": 503,
        "VECTOR_STORE_ERROR": 503,
    }
    status_code = status_map.get(exc.code, 500)
    return JSONResponse(
        status_code=status_code,
        content={"error": exc.code, "message": exc.message},
    )


async def unhandled_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    logger.exception("api.unhandled_error", error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"error": "INTERNAL_ERROR", "message": "An unexpected error occurred"},
    )
