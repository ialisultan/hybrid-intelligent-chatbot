"""Sidebar Quick Tests tab — one-click assessment queries."""

from __future__ import annotations

import streamlit as st

from frontend.data.assessment_queries import (
    EDGE_QUERIES,
    SQL_QUERIES,
    VECTOR_QUERIES,
    AssessmentQuery,
)


def _quick_test_button(item: AssessmentQuery) -> None:
    key = "qt_" + "".join(c if c.isalnum() else "_" for c in item.query)[:40]
    label = item.label if len(item.label) <= 36 else item.label[:33] + "…"
    help_text = f"{item.query} — expect route: {item.expected_route}"
    if st.button(label, key=key, use_container_width=True, help=help_text):
        st.session_state.pending_query = item.query
        st.rerun()


def _render_group(title: str, items: tuple[AssessmentQuery, ...]) -> None:
    st.markdown(f'<p class="quick-test-label">{title}</p>', unsafe_allow_html=True)
    for item in items:
        _quick_test_button(item)


def render_quick_tests_tab() -> None:
    st.caption("Click a button to send the query immediately.")
    _render_group("SQL", SQL_QUERIES)
    _render_group("Vector", VECTOR_QUERIES)
    _render_group("Edge cases", EDGE_QUERIES)
