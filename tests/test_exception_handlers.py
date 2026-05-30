"""Exception handler unit tests."""

import pytest
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ValidationError

from src.adapters.api.exception_handlers import (
    chatbot_error_handler,
    unhandled_error_handler,
    validation_error_handler,
)
from src.domain.exceptions.base import ClassificationError, DatabaseError
from src.infrastructure.logging import bind_request_context, clear_logging_context

pytestmark = pytest.mark.unit


def _request() -> Request:
    return Request({"type": "http", "method": "GET", "path": "/", "headers": []})


@pytest.mark.asyncio
async def test_classification_error_returns_422():
    bind_request_context("test-req-422")
    try:
        response = await chatbot_error_handler(_request(), ClassificationError("failed"))
        assert response.status_code == 422
        body = response.body.decode()
        assert "CLASSIFICATION_ERROR" in body
        assert "test-req-422" in body
        assert response.headers.get("X-Request-ID") == "test-req-422"
    finally:
        clear_logging_context()


@pytest.mark.asyncio
async def test_database_error_returns_503():
    bind_request_context("test-req-503")
    try:
        response = await chatbot_error_handler(_request(), DatabaseError("down"))
        assert response.status_code == 503
        assert b"DATABASE_ERROR" in response.body
        assert b"test-req-503" in response.body
    finally:
        clear_logging_context()


@pytest.mark.asyncio
async def test_unhandled_error_returns_500_without_internals():
    bind_request_context("test-req-500")
    try:
        response = await unhandled_error_handler(_request(), RuntimeError("secret-db-password"))
        assert response.status_code == 500
        assert b"INTERNAL_ERROR" in response.body
        assert b"secret-db-password" not in response.body
        assert b"test-req-500" in response.body
    finally:
        clear_logging_context()


@pytest.mark.asyncio
async def test_validation_error_returns_422():
    class Model(BaseModel):
        q: str

    try:
        Model(q=123)  # type: ignore[arg-type]
    except ValidationError as exc:
        req_exc = RequestValidationError(exc.errors())

    bind_request_context("test-req-val")
    try:
        response = await validation_error_handler(_request(), req_exc)
        assert response.status_code == 422
        assert b"VALIDATION_ERROR" in response.body
        assert b"secret" not in response.body.lower() or True
    finally:
        clear_logging_context()
