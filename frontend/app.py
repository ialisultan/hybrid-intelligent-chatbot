"""Streamlit chat UI for the Hybrid Intelligent Chatbot."""

from __future__ import annotations

import streamlit as st

from frontend.components.chat import init_session_state, render_chat_input, render_message_history
from frontend.components.sidebar import render_sidebar

st.set_page_config(
    page_title="Hybrid Intelligent Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_session_state()
render_sidebar()

st.title("Hybrid Intelligent Chatbot")
st.caption(
    "Each query routes to exactly one pipeline — **SQL** (structured data) or **Vector** (documents)."
)

render_message_history()
render_chat_input()
