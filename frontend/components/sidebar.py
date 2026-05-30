"""Sidebar — connection status, tabs, session controls."""

from __future__ import annotations

import streamlit as st

from frontend.components.demo_script import render_demo_script_tab
from frontend.components.quick_tests import render_quick_tests_tab
from frontend.components.settings import render_connection_status, render_settings


def render_sidebar() -> bool:
    """Render sidebar; returns True if backend is online."""
    with st.sidebar:
        st.title("Hybrid Chatbot")
        st.caption("GenAI Assessment II")

        online = render_connection_status()

        tab_quick, tab_settings, tab_demo = st.tabs(
            ["Quick Tests", "Settings", "Demo Script"]
        )

        with tab_quick:
            render_quick_tests_tab()

        with tab_settings:
            render_settings()

        with tab_demo:
            render_demo_script_tab()

        st.divider()
        if st.button("Clear chat", use_container_width=True, key="sidebar_clear_chat"):
            st.session_state.messages = []
            st.session_state.conversation_id = None
            st.session_state.pending_query = None
            st.rerun()

    return online
