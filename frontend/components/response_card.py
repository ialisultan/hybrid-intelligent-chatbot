"""Structured display of chat API routing metadata — badges and toggles."""

from __future__ import annotations

from typing import Any

import streamlit as st


def _route_badge_html(route: str) -> str:
    route_lower = str(route).lower()
    if route_lower == "sql":
        return '<span class="badge-sql">SQL</span>'
    if route_lower == "vector":
        return '<span class="badge-vector">VECTOR</span>'
    return f'<span class="badge-neutral">{route.upper()}</span>'


def _confidence_pill(confidence: float | None) -> str:
    if confidence is None:
        return '<span class="confidence-pill">—</span>'
    return f'<span class="confidence-pill">{confidence:.0%}</span>'


def render_response_meta(meta: dict[str, Any], *, index: int) -> None:
    """Render inline route badges, confidence, SQL toggle, and sources."""
    route = meta.get("route", "")
    confidence = meta.get("confidence")
    sql_query = meta.get("sql_query")
    sources = meta.get("sources") or []

    route_lower = str(route).lower()
    pipeline = (
        "PostgreSQL NL→SQL"
        if route_lower == "sql"
        else "Document RAG"
        if route_lower == "vector"
        else "—"
    )

    st.markdown(
        f'<div class="meta-bar">'
        f"{_route_badge_html(route)}"
        f"{_confidence_pill(confidence)}"
        f'<span class="pipeline-hint">{pipeline}</span>'
        f"</div>",
        unsafe_allow_html=True,
    )

    if sql_query:
        toggle_key = f"show_sql_{index}"
        show_sql = st.toggle("Show SQL", key=toggle_key, value=False)
        if show_sql:
            st.code(sql_query, language="sql")

    if sources:
        chips = "".join(f'<span class="source-chip">{src}</span>' for src in sources)
        st.markdown(
            f'<div class="sources-row"><span class="sources-label">Sources</span>{chips}</div>',
            unsafe_allow_html=True,
        )
