"""Conversation context helpers for multi-turn LangGraph orchestration."""


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
