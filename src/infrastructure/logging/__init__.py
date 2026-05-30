"""Structured logging with structlog and correlation ID support."""

import logging
import sys
from typing import Any
from uuid import uuid4

import structlog
from structlog.contextvars import bind_contextvars, clear_contextvars, get_contextvars, merge_contextvars
from structlog.types import Processor

CORRELATION_ID_HEADER = "X-Correlation-ID"
REQUEST_ID_HEADER = "X-Request-ID"


def _add_correlation_id(
    logger: logging.Logger,
    method_name: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    """Ensure every log record carries a correlation_id."""
    if "correlation_id" not in event_dict:
        event_dict["correlation_id"] = str(uuid4())
    return event_dict


def configure_logging(*, log_level: str = "INFO", json_output: bool = False) -> None:
    """Configure structlog + stdlib logging for the application."""
    shared_processors: list[Processor] = [
        merge_contextvars,
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        _add_correlation_id,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if json_output:
        renderer: Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=sys.stderr.isatty())

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(log_level.upper())

    for noisy in ("uvicorn.access", "httpx", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def bind_request_context(request_id: str | None = None) -> str:
    """Bind correlation_id and request_id to the current async context."""
    rid = request_id or str(uuid4())
    bind_contextvars(correlation_id=rid, request_id=rid)
    return rid


def bind_correlation_id(correlation_id: str | None = None) -> str:
    """Bind a correlation ID to the current async context (alias for request context)."""
    return bind_request_context(correlation_id)


def get_request_id() -> str:
    """Return the current request_id from context, or 'unknown'."""
    ctx = get_contextvars()
    return str(ctx.get("request_id") or ctx.get("correlation_id") or "unknown")


def clear_logging_context() -> None:
    """Reset context vars at the end of a request."""
    clear_contextvars()
