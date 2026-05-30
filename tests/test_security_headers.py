"""Security headers middleware tests."""

import pytest
from httpx import ASGITransport, AsyncClient

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_security_headers_on_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-Correlation-ID")
    assert response.headers.get("X-Request-ID")
