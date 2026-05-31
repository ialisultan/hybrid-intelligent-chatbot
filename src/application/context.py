"""Conversation context helpers for multi-turn LangGraph orchestration."""

from typing import Any


def enrich_invoke_config_with_conversation(
    config: dict[str, Any] | None,
    conversation_id: str,
) -> dict[str, Any]:
    """Attach a stable session thread id to RunnableConfig for LangGraph nodes.

    Uses the API ``conversation_id`` as ``thread_id`` so every turn in one chat
    session groups under the same LangSmith thread.
    """
    thread_id = str(conversation_id)
    enriched: dict[str, Any] = dict(config) if config else {}
    metadata = dict(enriched.get("metadata") or {})
    metadata["thread_id"] = thread_id
    metadata["conversation_id"] = thread_id
    metadata["session_id"] = thread_id
    enriched["metadata"] = metadata
    configurable = dict(enriched.get("configurable") or {})
    configurable["thread_id"] = thread_id
    enriched["configurable"] = configurable
    return enriched


def serialize_messages(messages: list) -> list[dict]:
    """Convert ChatMessage entities to serializable dicts."""
    return [{"role": msg.role, "content": msg.content} for msg in messages]


def filter_current_turn(messages: list[dict], current_query: str) -> list[dict]:
    """Exclude the current user message if it was saved before graph invocation."""
    if not messages:
        return messages
    last = messages[-1]
    if last.get("role") == "user" and last.get("content") == current_query:
        return messages[:-1]
    return messages


def build_contextual_query(
    query: str,
    messages: list[dict],
    max_turns: int = 6,
) -> str:
    """Format recent history + current query for classifier and pipeline ports."""
    if not messages:
        return query

    recent = messages[-max_turns:]
    lines = ["Previous conversation:"]
    for msg in recent:
        role = msg.get("role", "user").capitalize()
        lines.append(f"{role}: {msg.get('content', '')}")
    lines.append(f"Current question: {query}")
    return "\n".join(lines)
