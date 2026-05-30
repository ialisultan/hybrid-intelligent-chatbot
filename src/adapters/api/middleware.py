"""HTTP middleware — request logging and correlation IDs."""

import time
from collections.abc import Callable

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.infrastructure.logging import (
    CORRELATION_ID_HEADER,
    REQUEST_ID_HEADER,
    bind_request_context,
    clear_logging_context,
)

logger = structlog.get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Propagate request IDs and emit structured access logs."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        incoming = (
            request.headers.get(REQUEST_ID_HEADER)
            or request.headers.get(CORRELATION_ID_HEADER)
        )
        request_id = bind_request_context(incoming)
        client_ip = request.client.host if request.client else "unknown"
        started = time.perf_counter()

        logger.info(
            "http.request.start",
            method=request.method,
            path=request.url.path,
            client_ip=client_ip,
            request_id=request_id,
        )
        try:
            response = await call_next(request)
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            response.headers[CORRELATION_ID_HEADER] = request_id
            response.headers[REQUEST_ID_HEADER] = request_id
            logger.info(
                "http.request.complete",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=duration_ms,
                client_ip=client_ip,
                request_id=request_id,
            )
            return response
        finally:
            clear_logging_context()


# Backward-compatible alias
CorrelationIdMiddleware = RequestLoggingMiddleware
