"""Structured display of chat API routing metadata."""

from __future__ import annotations

from typing import Any

import streamlit as st


def render_response_meta(meta: dict[str, Any]) -> None:
    """Render route, confidence, pipeline details, SQL, and sources."""
    route = meta.get("route", "")
    confidence = meta.get("confidence")
    sql_query = meta.get("sql_query")
    sources = meta.get("sources") or []

    route_label = str(route).upper() if route else "—"
    pipeline = "PostgreSQL NL→SQL" if route == "sql" else "Document RAG"
    conf_value = f"{confidence:.0%}" if confidence is not None else "—"

    with st.expander(f"Routing details · {route_label}", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Route", route_label)
        with c2:
            st.metric("Confidence", conf_value)
        with c3:
            st.metric("Pipeline", pipeline)

        if route == "sql":
            st.info("Routed to **SQL** — structured data from PostgreSQL.")
        elif route == "vector":
            st.success("Routed to **Vector** — semantic search over documents.")
        else:
            st.caption(f"Route: {route_label}")

        if sql_query:
            with st.expander("Generated SQL", expanded=False):
                st.code(sql_query, language="sql")

    if sources:
        with st.expander(f"Sources ({len(sources)})", expanded=True):
            chips = "".join(
                f'<span class="source-chip">{src}</span>' for src in sources
            )
            st.markdown(chips, unsafe_allow_html=True)
