"""Sidebar — demo queries, backend status, session controls."""

from __future__ import annotations

import streamlit as st

from frontend.utils import get_backend_url, get_health

SQL_EXAMPLES = [
    "Total revenue this month?",
    "Top 5 customers by spending",
    "Orders placed in the last 7 days",
]

VECTOR_EXAMPLES = [
    "What is your return policy?",
    "Explain product features",
]

EDGE_CASE_EXAMPLES = [
    "Tell me about orders policy",
    "Customers refund issues",
]


def _example_button(label: str, query: str) -> None:
    key = "example_" + "".join(c if c.isalnum() else "_" for c in query)[:48]
    if st.button(label, key=key, use_container_width=True):
        st.session_state.pending_query = query
        st.rerun()


def render_sidebar() -> None:
    with st.sidebar:
        st.title("Hybrid Chatbot")
        st.caption("GenAI Assessment II — SQL vs Vector routing")

        st.divider()
        st.subheader("Backend")
        backend_url = get_backend_url()
        st.code(backend_url, language=None)

        try:
            health = get_health()
            st.success(f"Online — chat: `{health.get('chat_provider', '?')}`")
            st.caption(
                f"Embeddings: `{health.get('embedding_provider', '?')}` "
                "(configured server-side via `.env`)"
            )
            providers = sorted(
                {
                    str(health.get("chat_provider", "unknown")),
                    str(health.get("embedding_provider", "unknown")),
                }
            )
            st.selectbox(
                "Active providers",
                options=providers,
                index=0,
                disabled=True,
                help="Provider is configured server-side via `.env`.",
            )
        except Exception as exc:
            st.error("Backend unreachable")
            st.caption(str(exc))
            st.info("Run `make run` or `make up`, then refresh.")

        st.divider()
        st.subheader("SQL examples")
        for query in SQL_EXAMPLES:
            _example_button(query, query)

        st.subheader("Vector examples")
        for query in VECTOR_EXAMPLES:
            _example_button(query, query)

        st.subheader("Edge cases")
        for query in EDGE_CASE_EXAMPLES:
            _example_button(query, query)

        st.divider()
        if st.button("Clear chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.conversation_id = None
            st.session_state.pending_query = None
            st.rerun()
