"""Exception handler unit tests."""

import pytest
from fastapi import Request

from src.adapters.api.exception_handlers import chatbot_error_handler, unhandled_error_handler
from src.domain.exceptions.base import ClassificationError, DatabaseError

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_classification_error_returns_422():
    request = Request({"type": "http", "method": "GET", "path": "/", "headers": []})
    response = await chatbot_error_handler(request, ClassificationError("failed"))
    assert response.status_code == 422
    body = response.body.decode()
    assert "CLASSIFICATION_ERROR" in body


@pytest.mark.asyncio
async def test_database_error_returns_503():
    request = Request({"type": "http", "method": "GET", "path": "/", "headers": []})
    response = await chatbot_error_handler(request, DatabaseError("down"))
    assert response.status_code == 503
    assert b"DATABASE_ERROR" in response.body


@pytest.mark.asyncio
async def test_unhandled_error_returns_500():
    request = Request({"type": "http", "method": "GET", "path": "/", "headers": []})
    response = await unhandled_error_handler(request, RuntimeError("boom"))
    assert response.status_code == 500
    assert b"INTERNAL_ERROR" in response.body
