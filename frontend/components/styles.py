"""Global Streamlit CSS overrides."""

from __future__ import annotations

import streamlit as st

_CUSTOM_CSS = """
<style>
    /* Main header */
    .hybrid-header {
        margin-bottom: 0.25rem;
    }
    .hybrid-subtitle {
        color: #6b7280;
        font-size: 0.95rem;
        margin-bottom: 1.5rem;
    }

    /* Connection status */
    .status-online {
        color: #059669;
        font-weight: 600;
    }
    .status-offline {
        color: #dc2626;
        font-weight: 600;
    }

    /* Response routing card */
    div[data-testid="stMetric"] {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 0.5rem 0.75rem;
    }

    /* Source chips */
    .source-chip {
        display: inline-block;
        background: #eff6ff;
        border: 1px solid #bfdbfe;
        border-radius: 999px;
        padding: 0.15rem 0.65rem;
        margin: 0.15rem 0.25rem 0.15rem 0;
        font-size: 0.8rem;
        font-family: ui-monospace, monospace;
    }

    /* Sidebar section labels */
    .quick-test-label {
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748b;
        margin: 0.5rem 0 0.25rem 0;
    }

    /* Message rows */
    div[data-testid="stChatMessage"] {
        align-items: flex-start;
        gap: 0.65rem;
        padding: 0.5rem 0 0.75rem;
        background: transparent !important;
    }

    div[data-testid="stChatMessage"] [data-testid="stChatMessageAvatar"] {
        width: 2rem;
        height: 2rem;
        min-width: 2rem;
        font-size: 1.1rem;
    }

    div[data-testid="stChatMessage"] [data-testid="stChatMessageContent"] {
        max-width: min(42rem, 92%);
        padding: 0.7rem 1rem;
        border-radius: 1.125rem;
        line-height: 1.55;
        font-size: 0.95rem;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.06);
        border: 1px solid transparent;
    }

    div[data-testid="stChatMessage"] [data-testid="stChatMessageContent"] p {
        margin: 0;
    }

    div[data-testid="stChatMessage"] [data-testid="stChatMessageContent"] p + p {
        margin-top: 0.65rem;
    }

    /* User bubble — right-aligned, accent fill */
    div[data-testid="stChatMessage"]:has([alt="👤"]) {
        flex-direction: row-reverse;
    }

    div[data-testid="stChatMessage"]:has([alt="👤"]) [data-testid="stChatMessageContent"] {
        margin-left: auto;
        margin-right: 0;
        background: #2563eb;
        color: #ffffff;
        border-color: #1d4ed8;
        border-bottom-right-radius: 0.3rem;
    }

    div[data-testid="stChatMessage"]:has([alt="👤"]) [data-testid="stChatMessageContent"] a {
        color: #dbeafe;
    }

    /* Assistant bubble — left-aligned, neutral fill */
    div[data-testid="stChatMessage"]:has([alt="🤖"]) [data-testid="stChatMessageContent"] {
        margin-right: auto;
        margin-left: 0;
        background: #f3f4f6;
        color: #111827;
        border-color: #e5e7eb;
        border-bottom-left-radius: 0.3rem;
    }

    /* Metadata expanders sit below the bubble, not inside it */
    div[data-testid="stChatMessage"]:has([alt="🤖"]) [data-testid="stExpander"],
    div[data-testid="stChatMessage"]:has([alt="🤖"]) [data-testid="stAlert"] {
        max-width: min(42rem, 92%);
        margin-top: 0.35rem;
    }

</style>
"""


def inject_custom_css() -> None:
    st.markdown(_CUSTOM_CSS, unsafe_allow_html=True)
