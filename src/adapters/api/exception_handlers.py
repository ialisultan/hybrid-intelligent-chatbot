"""Global exception handlers for domain errors."""

import structlog
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from src.domain.exceptions.base import ChatbotError
from src.infrastructure.logging import CORRELATION_ID_HEADER, REQUEST_ID_HEADER, get_request_id
from src.interfaces.schemas.error import ErrorResponse

logger = structlog.get_logger(__name__)

_STATUS_MAP = {
    "CLASSIFICATION_ERROR": 422,
    "ROUTING_VIOLATION": 500,
    "SQL_PIPELINE_ERROR": 502,
    "VECTOR_PIPELINE_ERROR": 502,
    "DATABASE_ERROR": 503,
    "VECTOR_STORE_ERROR": 503,
}


def _error_response(
    *,
    status_code: int,
    error: str,
    message: str,
    request: Request | None = None,
) -> JSONResponse:
    request_id = get_request_id()
    body = ErrorResponse(error=error, message=message, request_id=request_id)
    response = JSONResponse(status_code=status_code, content=body.model_dump())
    response.headers[CORRELATION_ID_HEADER] = request_id
    response.headers[REQUEST_ID_HEADER] = request_id
    return response


async def chatbot_error_handler(request: Request, exc: ChatbotError) -> JSONResponse:
    logger.warning(
        "api.error",
        code=exc.code,
        message=exc.message,
        request_id=get_request_id(),
    )
    status_code = _STATUS_MAP.get(exc.code, 500)
    return _error_response(
        status_code=status_code,
        error=exc.code,
        message=exc.message,
        request=request,
    )


async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    logger.warning(
        "api.validation_error",
        errors=exc.errors(),
        request_id=get_request_id(),
    )
    return _error_response(
        status_code=422,
        error="VALIDATION_ERROR",
        message="Request validation failed",
        request=request,
    )


async def rate_limit_error_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    logger.warning("api.rate_limit", request_id=get_request_id())
    return _error_response(
        status_code=429,
        error="RATE_LIMIT_EXCEEDED",
        message="Too many requests. Please try again later.",
        request=request,
    )


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(
        "api.unhandled_error",
        error_type=type(exc).__name__,
        request_id=get_request_id(),
    )
    return _error_response(
        status_code=500,
        error="INTERNAL_ERROR",
        message="An unexpected error occurred",
        request=request,
    )
