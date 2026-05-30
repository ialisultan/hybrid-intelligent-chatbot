"""HTTP client for the FastAPI backend."""

from __future__ import annotations

import os
from typing import Any
from uuid import UUID

import httpx

DEFAULT_BACKEND_URL = "http://localhost:8000"
CHAT_PATH = "/api/v1/chat"
HEALTH_PATH = "/health"
REQUEST_TIMEOUT = 120.0


def get_backend_url() -> str:
    return os.getenv("BACKEND_URL", DEFAULT_BACKEND_URL).rstrip("/")


def post_chat(
    query: str,
    conversation_id: UUID | None = None,
    *,
    backend_url: str | None = None,
    timeout: float = REQUEST_TIMEOUT,
) -> dict[str, Any]:
    """Send a chat message to the backend."""
    base = (backend_url or get_backend_url()).rstrip("/")
    payload: dict[str, Any] = {"query": query}
    if conversation_id is not None:
        payload["conversation_id"] = str(conversation_id)

    with httpx.Client(timeout=timeout) as client:
        response = client.post(f"{base}{CHAT_PATH}", json=payload)
        response.raise_for_status()
        return response.json()


def get_health(*, backend_url: str | None = None, timeout: float = 10.0) -> dict[str, Any]:
    """Fetch backend liveness and provider info."""
    base = (backend_url or get_backend_url()).rstrip("/")
    with httpx.Client(timeout=timeout) as client:
        response = client.get(f"{base}{HEALTH_PATH}")
        response.raise_for_status()
        return response.json()
