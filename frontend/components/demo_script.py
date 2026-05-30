"""Sidebar Demo Script tab — guided assessment walkthrough + cURL."""

from __future__ import annotations

import streamlit as st

from frontend.data.assessment_queries import ALL_QUERIES, DEMO_SCRIPT_STEPS, AssessmentQuery
from frontend.utils import build_all_assessment_curl_commands, build_curl_command


def _run_button(item: AssessmentQuery, step: int) -> None:
    if st.button(f"Run step {step}", key=f"demo_run_{step}", use_container_width=True):
        st.session_state.pending_query = item.query
        st.rerun()


def _expected_badge(route: str) -> str:
    if route == "sql":
        return '<span class="badge-sql badge-inline">SQL</span>'
    return '<span class="badge-vector badge-inline">VECTOR</span>'


def render_demo_script_tab() -> None:
    st.caption("Follow these steps for a live assessment demo.")

    for i, item in enumerate(DEMO_SCRIPT_STEPS, start=1):
        st.markdown(
            f"**Step {i}** — {_expected_badge(item.expected_route)}",
            unsafe_allow_html=True,
        )
        st.markdown(f"*{item.demo_note}*")
        st.markdown(f"`{item.query}`")
        _run_button(item, i)
        st.divider()

    st.markdown("**Multi-turn** — reuse `conversation_id` from the last response:")
    conv_id = st.session_state.get("conversation_id")
    if conv_id:
        st.code(
            build_curl_command(
                "What about warranty?",
                conversation_id=conv_id,
            ),
            language="bash",
        )
    else:
        st.caption("Send any message first to obtain a conversation ID.")

    show_curl = st.toggle("Show cURL commands", key="demo_show_curl")
    if show_curl:
        st.markdown("##### Highlighted demo steps")
        st.code(
            build_all_assessment_curl_commands(DEMO_SCRIPT_STEPS),
            language="bash",
        )
        st.markdown("##### All assessment queries")
        st.code(
            build_all_assessment_curl_commands(ALL_QUERIES),
            language="bash",
        )
