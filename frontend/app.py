"""Streamlit chat UI for the Hybrid Intelligent Chatbot."""

from __future__ import annotations

import streamlit as st

from frontend.components.chat import init_session_state, render_chat_input, render_message_history
from frontend.components.sidebar import render_sidebar
from frontend.components.styles import inject_custom_css

st.set_page_config(
    page_title="Hybrid Intelligent Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_custom_css()
init_session_state()
render_sidebar()

st.markdown('<h1 class="hybrid-header">Hybrid Intelligent Chatbot</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="hybrid-subtitle">Each query routes to exactly one pipeline — '
    "<strong>SQL</strong> (PostgreSQL) or <strong>Vector</strong> (document RAG). "
    "Pipelines never mix.</p>",
    unsafe_allow_html=True,
)

_spacer_l, chat_col, _spacer_r = st.columns([1, 6, 1])
with chat_col:
    render_message_history()
    render_chat_input()
