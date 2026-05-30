"""Correlation ID middleware."""

from collections.abc import Callable

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.infrastructure.logging import (
    CORRELATION_ID_HEADER,
    bind_correlation_id,
    clear_logging_context,
)

logger = structlog.get_logger(__name__)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Propagate or generate X-Correlation-ID for every request."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        correlation_id = request.headers.get(CORRELATION_ID_HEADER)
        cid = bind_correlation_id(correlation_id)
        logger.info(
            "http.request.start",
            method=request.method,
            path=request.url.path,
        )
        try:
            response = await call_next(request)
            response.headers[CORRELATION_ID_HEADER] = cid
            logger.info(
                "http.request.complete",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
            )
            return response
        finally:
            clear_logging_context()
