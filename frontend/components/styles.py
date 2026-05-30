"""Global Streamlit CSS overrides — light and dark themes."""

from __future__ import annotations

import streamlit as st

_LIGHT_VARS = """
    --hybrid-bg: #ffffff;
    --hybrid-text: #111827;
    --hybrid-muted: #6b7280;
    --hybrid-border: #e5e7eb;
    --hybrid-surface: #f8fafc;
    --hybrid-user-bg: #2563eb;
    --hybrid-user-text: #ffffff;
    --hybrid-user-border: #1d4ed8;
    --hybrid-assistant-bg: #f3f4f6;
    --hybrid-assistant-text: #111827;
    --hybrid-assistant-border: #e5e7eb;
    --hybrid-badge-sql-bg: #dbeafe;
    --hybrid-badge-sql-text: #1e40af;
    --hybrid-badge-vector-bg: #fef3c7;
    --hybrid-badge-vector-text: #92400e;
    --hybrid-chip-bg: #eff6ff;
    --hybrid-chip-border: #bfdbfe;
    --hybrid-metric-bg: #f8fafc;
    --hybrid-shadow: rgba(15, 23, 42, 0.06);
"""

_DARK_VARS = """
    --hybrid-bg: #0f172a;
    --hybrid-text: #f1f5f9;
    --hybrid-muted: #94a3b8;
    --hybrid-border: #334155;
    --hybrid-surface: #1e293b;
    --hybrid-user-bg: #3b82f6;
    --hybrid-user-text: #ffffff;
    --hybrid-user-border: #2563eb;
    --hybrid-assistant-bg: #1e293b;
    --hybrid-assistant-text: #f1f5f9;
    --hybrid-assistant-border: #334155;
    --hybrid-badge-sql-bg: #1e3a5f;
    --hybrid-badge-sql-text: #93c5fd;
    --hybrid-badge-vector-bg: #422006;
    --hybrid-badge-vector-text: #fcd34d;
    --hybrid-chip-bg: #1e3a5f;
    --hybrid-chip-border: #3b82f6;
    --hybrid-metric-bg: #1e293b;
    --hybrid-shadow: rgba(0, 0, 0, 0.25);
"""


def _build_css(dark: bool) -> str:
    theme_vars = _DARK_VARS if dark else _LIGHT_VARS
    theme_class = "hybrid-dark" if dark else "hybrid-light"

    return f"""
<style>
    @media (prefers-color-scheme: dark) {{
        :root:not(.hybrid-light-forced) {{
            {_DARK_VARS}
        }}
    }}

    .{theme_class}, .{theme_class} ~ * {{
        /* scoped via wrapper */
    }}

    section.main .block-container {{
        --theme-applied: 1;
    }}

    :root, section.main {{
        {theme_vars}
    }}

    .hybrid-header {{
        color: var(--hybrid-text);
        margin-bottom: 0.25rem;
    }}
    .hybrid-subtitle {{
        color: var(--hybrid-muted);
        font-size: 0.95rem;
        margin-bottom: 1.5rem;
    }}

    .status-pill {{
        display: inline-block;
        font-size: 0.8rem;
        font-weight: 600;
        padding: 0.2rem 0.65rem;
        border-radius: 999px;
        margin-left: 0.5rem;
        vertical-align: middle;
    }}
    .status-pill-online {{
        background: #d1fae5;
        color: #065f46;
    }}
    .status-pill-offline {{
        background: #fee2e2;
        color: #991b1b;
    }}
    .hybrid-dark .status-pill-online {{
        background: #064e3b;
        color: #6ee7b7;
    }}
    .hybrid-dark .status-pill-offline {{
        background: #7f1d1d;
        color: #fca5a5;
    }}

    .status-online {{ color: #059669; font-weight: 600; }}
    .status-offline {{ color: #dc2626; font-weight: 600; }}
    .hybrid-dark .status-online {{ color: #34d399; }}
    .hybrid-dark .status-offline {{ color: #f87171; }}

    .badge-sql, .badge-vector, .badge-neutral, .badge-inline {{
        display: inline-block;
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        padding: 0.2rem 0.55rem;
        border-radius: 6px;
        margin-right: 0.35rem;
        vertical-align: middle;
    }}
    .badge-sql {{
        background: var(--hybrid-badge-sql-bg);
        color: var(--hybrid-badge-sql-text);
    }}
    .badge-vector {{
        background: var(--hybrid-badge-vector-bg);
        color: var(--hybrid-badge-vector-text);
    }}
    .badge-neutral {{
        background: var(--hybrid-surface);
        color: var(--hybrid-muted);
        border: 1px solid var(--hybrid-border);
    }}

    .confidence-pill {{
        display: inline-block;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 0.15rem 0.5rem;
        border-radius: 999px;
        background: var(--hybrid-surface);
        color: var(--hybrid-muted);
        border: 1px solid var(--hybrid-border);
        margin-right: 0.35rem;
        vertical-align: middle;
    }}

    .pipeline-hint {{
        font-size: 0.75rem;
        color: var(--hybrid-muted);
        vertical-align: middle;
    }}

    .meta-bar {{
        margin: 0.35rem 0 0.5rem 0;
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 0.25rem;
    }}

    .sources-row {{
        margin-top: 0.35rem;
        margin-bottom: 0.5rem;
    }}
    .sources-label {{
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--hybrid-muted);
        display: block;
        margin-bottom: 0.25rem;
    }}

    .source-chip {{
        display: inline-block;
        background: var(--hybrid-chip-bg);
        border: 1px solid var(--hybrid-chip-border);
        border-radius: 999px;
        padding: 0.15rem 0.65rem;
        margin: 0.15rem 0.25rem 0.15rem 0;
        font-size: 0.8rem;
        font-family: ui-monospace, monospace;
        color: var(--hybrid-text);
    }}

    .quick-test-label {{
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--hybrid-muted);
        margin: 0.5rem 0 0.25rem 0;
    }}

    div[data-testid="stMetric"] {{
        background: var(--hybrid-metric-bg);
        border: 1px solid var(--hybrid-border);
        border-radius: 8px;
        padding: 0.5rem 0.75rem;
    }}

    div[data-testid="stChatMessage"] {{
        align-items: flex-start;
        gap: 0.65rem;
        padding: 0.5rem 0 0.75rem;
        background: transparent !important;
    }}

    div[data-testid="stChatMessage"] [data-testid="stChatMessageAvatar"] {{
        width: 2rem;
        height: 2rem;
        min-width: 2rem;
        font-size: 1.1rem;
    }}

    div[data-testid="stChatMessage"] [data-testid="stChatMessageContent"] {{
        max-width: min(42rem, 92%);
        padding: 0.7rem 1rem;
        border-radius: 1.125rem;
        line-height: 1.55;
        font-size: 0.95rem;
        box-shadow: 0 1px 2px var(--hybrid-shadow);
        border: 1px solid transparent;
    }}

    div[data-testid="stChatMessage"] [data-testid="stChatMessageContent"] p {{
        margin: 0;
    }}

    div[data-testid="stChatMessage"]:has([alt="👤"]) {{
        flex-direction: row-reverse;
    }}

    div[data-testid="stChatMessage"]:has([alt="👤"]) [data-testid="stChatMessageContent"] {{
        margin-left: auto;
        margin-right: 0;
        background: var(--hybrid-user-bg);
        color: var(--hybrid-user-text);
        border-color: var(--hybrid-user-border);
        border-bottom-right-radius: 0.3rem;
    }}

    div[data-testid="stChatMessage"]:has([alt="🤖"]) [data-testid="stChatMessageContent"] {{
        margin-right: auto;
        margin-left: 0;
        background: var(--hybrid-assistant-bg);
        color: var(--hybrid-assistant-text);
        border-color: var(--hybrid-assistant-border);
        border-bottom-left-radius: 0.3rem;
    }}

    div[data-testid="stChatMessage"]:has([alt="🤖"]) .meta-bar,
    div[data-testid="stChatMessage"]:has([alt="🤖"]) .sources-row {{
        max-width: min(42rem, 92%);
    }}
</style>
"""


def inject_custom_css(*, dark: bool | None = None) -> None:
    if dark is None:
        dark = bool(st.session_state.get("dark_mode", False))
    wrapper_class = "hybrid-dark" if dark else "hybrid-light"
    st.markdown(
        f'<div class="{wrapper_class}"></div>' + _build_css(dark),
        unsafe_allow_html=True,
    )
