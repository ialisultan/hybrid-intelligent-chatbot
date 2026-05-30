"""Chat transcript, input, and response rendering."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import httpx
import streamlit as st

from frontend.components.response_card import render_response_meta
from frontend.utils import parse_chat_response, post_chat

USER_AVATAR = "👤"
ASSISTANT_AVATAR = "🤖"


def init_session_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "conversation_id" not in st.session_state:
        st.session_state.conversation_id = None
    if "pending_query" not in st.session_state:
        st.session_state.pending_query = None
    if "dark_mode" not in st.session_state:
        st.session_state.dark_mode = False


def _meta_from_parsed(parsed: Any) -> dict[str, Any]:
    return {
        "route": parsed.route,
        "confidence": parsed.confidence,
        "sql_query": parsed.sql_query,
        "sources": parsed.sources,
    }


def render_message_history() -> None:
    for i, msg in enumerate(st.session_state.messages):
        is_user = msg["role"] == "user"
        role = msg["role"]
        avatar = USER_AVATAR if is_user else ASSISTANT_AVATAR
        with st.chat_message(name=role, avatar=avatar):
            st.markdown(msg["content"])
            if not is_user and msg.get("meta"):
                render_response_meta(msg["meta"], index=i)


def _send_query(query: str) -> None:
    query = query.strip()
    if not query:
        return

    st.session_state.messages.append({"role": "user", "content": query})

    conv_id: UUID | None = st.session_state.conversation_id
    try:
        with st.spinner("Routing query…"):
            raw = post_chat(query, conversation_id=conv_id)
            parsed = parse_chat_response(raw)

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": parsed.answer,
                "meta": _meta_from_parsed(parsed),
            }
        )
        if parsed.conversation_id:
            st.session_state.conversation_id = parsed.conversation_id
    except httpx.ConnectError:
        st.session_state.messages.pop()
        st.error(
            "Cannot reach the backend. Start it with `make run` or `make up`, "
            "then try again."
        )
    except httpx.HTTPStatusError as exc:
        st.session_state.messages.pop()
        detail = exc.response.text[:500] if exc.response else str(exc)
        st.error(f"Backend error ({exc.response.status_code}): {detail}")
    except Exception as exc:
        st.session_state.messages.pop()
        st.error(f"Request failed: {exc}")


def get_last_user_query() -> str | None:
    for msg in reversed(st.session_state.messages):
        if msg["role"] == "user":
            return msg["content"]
    return None


def render_chat_input() -> None:
    pending = st.session_state.pop("pending_query", None)
    if pending:
        _send_query(pending)
        st.rerun()

    user_input = st.chat_input("Ask about revenue, policies, products…")
    if user_input:
        _send_query(user_input)
        st.rerun()
