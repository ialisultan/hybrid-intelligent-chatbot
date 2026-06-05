"""Streamlit chat UI for the Hybrid Intelligent Chatbot."""

from __future__ import annotations

import streamlit as st

from frontend.components.chat import (
    get_last_user_query,
    init_session_state,
    render_chat_input,
    render_message_history,
)
from frontend.components.sidebar import render_sidebar
from frontend.components.styles import inject_custom_css
from frontend.data.assessment_queries import ALL_QUERIES
from frontend.utils import build_all_assessment_curl_commands, build_curl_command

st.set_page_config(
    page_title="Hybrid Intelligent Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_session_state()
inject_custom_css(dark=st.session_state.get("dark_mode", False))
backend_online = render_sidebar()

status_class = "status-pill-online" if backend_online else "status-pill-offline"
status_label = "Online" if backend_online else "Offline"
st.markdown(
    f'<h1 class="hybrid-header">Hybrid Intelligent Chatbot'
    f'<span class="status-pill {status_class}">{status_label}</span></h1>',
    unsafe_allow_html=True,
)
_sql_dialect = st.session_state.get("sql_dialect", "SQL database")
st.markdown(
    '<p class="hybrid-subtitle">Each query routes to exactly one pipeline — '
    f"<strong>SQL</strong> ({_sql_dialect}) or <strong>Vector</strong> (document RAG). "
    "Pipelines never mix.</p>",
    unsafe_allow_html=True,
)

with st.expander("Show cURL commands for reviewers", expanded=False):
    last_query = get_last_user_query()
    conv_id = st.session_state.get("conversation_id")
    if last_query:
        st.markdown("**Last user message**")
        st.code(
            build_curl_command(last_query, conversation_id=conv_id),
            language="bash",
        )
    else:
        st.caption("Send a message to generate a cURL command for the last query.")
    st.markdown("**All assessment queries**")
    st.code(build_all_assessment_curl_commands(ALL_QUERIES), language="bash")

_spacer_l, chat_col, _spacer_r = st.columns([1, 6, 1])
with chat_col:
    render_message_history()
    render_chat_input()
