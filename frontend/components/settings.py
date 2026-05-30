"""Sidebar settings — backend URL, providers, session, theme."""

from __future__ import annotations

import streamlit as st

from frontend.utils import get_backend_url, get_health

KNOWN_PROVIDERS = ["openai", "anthropic", "google", "stub", "uninitialised"]


def _fetch_health() -> dict | None:
    if "health_cache" in st.session_state:
        return st.session_state.health_cache
    try:
        health = get_health()
        st.session_state.health_cache = health
        return health
    except Exception:
        st.session_state.health_cache = None
        return None


def refresh_health() -> None:
    """Clear cached health (call after backend may have restarted)."""
    st.session_state.pop("health_cache", None)


def render_connection_status() -> bool:
    """Compact online/offline indicator. Returns True if backend is reachable."""
    health = _fetch_health()
    if health:
        st.markdown(
            '<p class="status-online">● Online</p>',
            unsafe_allow_html=True,
        )
        return True
    st.markdown(
        '<p class="status-offline">● Offline</p>',
        unsafe_allow_html=True,
    )
    st.caption("Run `make run` or `make up`, then refresh.")
    return False


def render_settings() -> None:
    st.toggle(
        "Dark mode",
        key="dark_mode",
        help="Switch between light and dark chat theme.",
    )

    st.text_input("Backend URL", value=get_backend_url(), disabled=True)

    health = _fetch_health()
    chat_provider = str(health.get("chat_provider", "unknown")) if health else "unknown"
    embedding_provider = (
        str(health.get("embedding_provider", "unknown")) if health else "unknown"
    )

    provider_options = sorted(set(KNOWN_PROVIDERS) | {chat_provider, embedding_provider})
    chat_idx = provider_options.index(chat_provider) if chat_provider in provider_options else 0
    emb_idx = (
        provider_options.index(embedding_provider)
        if embedding_provider in provider_options
        else 0
    )

    st.selectbox(
        "LLM provider",
        options=provider_options,
        index=chat_idx,
        disabled=True,
        help="Configured server-side via `.env` (LLM_PROVIDER).",
    )
    st.selectbox(
        "Embeddings",
        options=provider_options,
        index=emb_idx,
        disabled=True,
        help="Configured server-side via `.env` (EMBEDDING_PROVIDER).",
    )
    st.slider(
        "Temperature",
        min_value=0.0,
        max_value=1.0,
        value=0.0,
        step=0.1,
        disabled=True,
        help="Fixed at 0 on the server for deterministic routing and SQL.",
    )

    st.divider()
    st.subheader("Session")
    conv_id = st.session_state.get("conversation_id")
    conv_display = str(conv_id) if conv_id else "(new session)"
    st.text_input("Conversation ID", value=conv_display, disabled=True)
    if conv_id:
        st.code(str(conv_id), language=None)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("New session", use_container_width=True, key="settings_new_session"):
            st.session_state.messages = []
            st.session_state.conversation_id = None
            st.session_state.pending_query = None
            refresh_health()
            st.rerun()
    with col2:
        if st.button("Refresh", use_container_width=True, key="settings_refresh_health"):
            refresh_health()
            st.rerun()
