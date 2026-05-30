"""HTTP client for the FastAPI backend."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any
from uuid import UUID

import httpx

DEFAULT_BACKEND_URL = "http://localhost:8000"
CHAT_PATH = "/api/v1/chat"
HEALTH_PATH = "/health"
REQUEST_TIMEOUT = 120.0


@dataclass(frozen=True)
class ChatResponseMeta:
    """Parsed fields from POST /api/v1/chat."""

    answer: str
    route: str
    confidence: float | None
    sql_query: str | None
    sources: list[str]
    conversation_id: UUID | None


def parse_chat_response(data: dict[str, Any]) -> ChatResponseMeta:
    """Normalize API JSON into a typed response object."""
    conv_raw = data.get("conversation_id")
    conversation_id = UUID(str(conv_raw)) if conv_raw else None
    route = data.get("route", "")
    route_str = route.value if hasattr(route, "value") else str(route)

    confidence = data.get("confidence")
    conf_float = float(confidence) if confidence is not None else None

    sources_raw = data.get("sources") or []
    sources = [str(s) for s in sources_raw]

    return ChatResponseMeta(
        answer=str(data.get("answer", "")),
        route=route_str,
        confidence=conf_float,
        sql_query=data.get("sql_query"),
        sources=sources,
        conversation_id=conversation_id,
    )


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


def build_curl_command(
    query: str,
    *,
    conversation_id: UUID | None = None,
    backend_url: str | None = None,
) -> str:
    """Build a copy-paste curl command for POST /api/v1/chat."""
    base = (backend_url or get_backend_url()).rstrip("/")
    payload: dict[str, Any] = {"query": query}
    if conversation_id is not None:
        payload["conversation_id"] = str(conversation_id)
    body = json.dumps(payload, ensure_ascii=False)
    return (
        f"curl -s -X POST {base}{CHAT_PATH} \\\n"
        f'  -H "Content-Type: application/json" \\\n'
        f"  -d '{body}' | jq ."
    )


def build_all_assessment_curl_commands(
    queries: tuple[Any, ...],
    *,
    backend_url: str | None = None,
) -> str:
    """Concatenate curl commands for a sequence of assessment queries."""
    blocks: list[str] = []
    for item in queries:
        q = item.query if hasattr(item, "query") else str(item)
        label = item.label if hasattr(item, "label") else q[:40]
        blocks.append(f"# {label}\n{build_curl_command(q, backend_url=backend_url)}")
    return "\n\n".join(blocks)
