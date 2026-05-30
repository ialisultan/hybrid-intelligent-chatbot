"""Sidebar — connection, Quick Test, settings, session controls."""

from __future__ import annotations

import streamlit as st

from frontend.components.settings import render_connection_status, render_settings

SQL_EXAMPLES = [
    ("Total revenue this month?", "sql"),
    ("Top 5 customers by spending", "sql"),
    ("Orders placed in the last 7 days", "sql"),
]

VECTOR_EXAMPLES = [
    ("What is your return policy?", "vector"),
    ("Explain product features", "vector"),
]

EDGE_CASE_EXAMPLES = [
    ("Tell me about orders policy", "vector"),
    ("Customers refund issues", "vector"),
]


def _quick_test_button(query: str, expected_route: str) -> None:
    key = "qt_" + "".join(c if c.isalnum() else "_" for c in query)[:40]
    label = query if len(query) <= 42 else query[:39] + "…"
    if st.button(label, key=key, use_container_width=True, help=f"Expected: {expected_route}"):
        st.session_state.pending_query = query
        st.rerun()


def _render_quick_test_group(title: str, examples: list[tuple[str, str]]) -> None:
    st.markdown(f'<p class="quick-test-label">{title}</p>', unsafe_allow_html=True)
    for query, expected in examples:
        _quick_test_button(query, expected)


def render_sidebar() -> None:
    with st.sidebar:
        st.title("Hybrid Chatbot")
        st.caption("GenAI Assessment II")

        st.subheader("Connection")
        render_connection_status()

        render_settings()

        st.divider()

        with st.expander("Quick Test", expanded=True):
            st.caption("Assessment demo queries — click to send.")
            _render_quick_test_group("SQL", SQL_EXAMPLES)
            _render_quick_test_group("Vector", VECTOR_EXAMPLES)
            _render_quick_test_group("Edge cases", EDGE_CASE_EXAMPLES)

        st.divider()

        if st.button("Clear chat", use_container_width=True, key="sidebar_clear_chat"):
            st.session_state.messages = []
            st.session_state.conversation_id = None
            st.session_state.pending_query = None
            st.rerun()
