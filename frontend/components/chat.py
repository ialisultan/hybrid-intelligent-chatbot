"""Chat transcript, input, and response rendering."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import httpx
import streamlit as st

from frontend.utils import post_chat


def init_session_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "conversation_id" not in st.session_state:
        st.session_state.conversation_id = None
    if "pending_query" not in st.session_state:
        st.session_state.pending_query = None


def _render_metadata(meta: dict[str, Any]) -> None:
    route = meta.get("route", "")
    confidence = meta.get("confidence")
    route_label = str(route).upper() if route else "UNKNOWN"
    conf_text = f" · {confidence:.0%} confidence" if confidence is not None else ""
    if route == "sql":
        st.info(f"Route: **{route_label}**{conf_text}")
    elif route == "vector":
        st.success(f"Route: **{route_label}**{conf_text}")
    else:
        st.caption(f"Route: {route_label}{conf_text}")

    sql_query = meta.get("sql_query")
    if sql_query:
        with st.expander("Generated SQL"):
            st.code(sql_query, language="sql")

    sources = meta.get("sources") or []
    if sources:
        with st.expander("Sources"):
            for src in sources:
                st.markdown(f"- `{src}`")


def render_message_history() -> None:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and msg.get("meta"):
                _render_metadata(msg["meta"])


def _send_query(query: str) -> None:
    query = query.strip()
    if not query:
        return

    st.session_state.messages.append({"role": "user", "content": query})

    conv_id: UUID | None = st.session_state.conversation_id
    try:
        with st.spinner("Routing query…"):
            result = post_chat(query, conversation_id=conv_id)

        answer = result.get("answer", "")
        meta = {
            "route": result.get("route"),
            "confidence": result.get("confidence"),
            "sql_query": result.get("sql_query"),
            "sources": result.get("sources", []),
        }
        st.session_state.messages.append(
            {"role": "assistant", "content": answer, "meta": meta}
        )
        if result.get("conversation_id"):
            st.session_state.conversation_id = UUID(str(result["conversation_id"]))
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


def render_chat_input() -> None:
    pending = st.session_state.pop("pending_query", None)
    if pending:
        _send_query(pending)
        st.rerun()

    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_area(
            "Your question",
            placeholder="Ask about revenue, policies, products…",
            height=100,
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button("Send", type="primary", use_container_width=True)

    if submitted and user_input:
        _send_query(user_input)
        st.rerun()
