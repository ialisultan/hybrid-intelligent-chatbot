"""LangSmith tracing configuration and RunnableConfig helpers."""

import os
from typing import Any
from uuid import UUID

import structlog

from src.application.context import enrich_invoke_config_with_conversation
from src.infrastructure.config.settings import Settings
from src.infrastructure.logging import get_request_id

logger = structlog.get_logger(__name__)

# LangSmith groups runs into threads when any of these metadata keys match.
_THREAD_METADATA_KEYS = frozenset(
    {"thread_id", "conversation_id", "session_id", "request_id", "app_name", "app_env"}
)


def _set_env(key: str, value: str) -> None:
    os.environ[key] = value


def _disable_tracing_env() -> None:
    _set_env("LANGCHAIN_TRACING_V2", "false")
    _set_env("LANGSMITH_TRACING", "false")
    for key in ("LANGCHAIN_API_KEY", "LANGCHAIN_PROJECT", "LANGSMITH_API_KEY", "LANGSMITH_PROJECT"):
        os.environ.pop(key, None)


def configure_langsmith(settings: Settings) -> None:
    """Configure LangSmith/LangChain tracing via process environment (fail-open)."""
    try:
        if not settings.langsmith_tracing_active:
            _disable_tracing_env()
            logger.info("tracing.langsmith.disabled")
            return

        api_key = settings.langsmith_api_key.strip()
        project = settings.langsmith_project_name

        _set_env("LANGCHAIN_TRACING_V2", "true")
        _set_env("LANGCHAIN_API_KEY", api_key)
        _set_env("LANGCHAIN_PROJECT", project)
        _set_env("LANGSMITH_TRACING", "true")
        _set_env("LANGSMITH_API_KEY", api_key)
        _set_env("LANGSMITH_PROJECT", project)

        if settings.langsmith_endpoint:
            _set_env("LANGSMITH_ENDPOINT", settings.langsmith_endpoint.strip())

        if settings.langsmith_hide_inputs:
            _set_env("LANGCHAIN_HIDE_INPUTS", "true")
        else:
            os.environ.pop("LANGCHAIN_HIDE_INPUTS", None)

        if settings.langsmith_hide_outputs:
            _set_env("LANGCHAIN_HIDE_OUTPUTS", "true")
        else:
            os.environ.pop("LANGCHAIN_HIDE_OUTPUTS", None)

        if settings.langsmith_sampling_rate < 1.0:
            _set_env("LANGSMITH_SAMPLING_RATE", str(settings.langsmith_sampling_rate))

        logger.info(
            "tracing.langsmith.enabled",
            project=project,
            env=settings.app_env,
            hide_inputs=settings.langsmith_hide_inputs,
            hide_outputs=settings.langsmith_hide_outputs,
            sampling_rate=settings.langsmith_sampling_rate,
        )
    except Exception as exc:
        logger.warning("tracing.langsmith.configure_failed", error=str(exc))


def _thread_metadata(
    *,
    conversation_id: str,
    request_id: str,
    app_name: str,
    app_env: str,
    user_query: str | None = None,
) -> dict[str, str]:
    """Metadata required for LangSmith thread grouping on parent and child runs."""
    meta: dict[str, str] = {
        "thread_id": conversation_id,
        "conversation_id": conversation_id,
        "session_id": conversation_id,
        "request_id": request_id,
        "app_name": app_name,
        "app_env": app_env,
    }
    if user_query:
        meta["user_query"] = user_query
    return meta


def _normalize_thread_fields(meta: dict[str, Any], thread_id: str) -> dict[str, Any]:
    """Ensure LangSmith thread keys all point at the same session id."""
    meta["thread_id"] = thread_id
    meta["conversation_id"] = thread_id
    meta["session_id"] = thread_id
    return meta


def extract_thread_metadata(
    config: dict[str, Any] | None,
    *,
    fallback_conversation_id: str | None = None,
) -> dict[str, Any]:
    """Pull thread-related metadata from RunnableConfig (metadata + configurable)."""
    meta: dict[str, Any] = dict(config.get("metadata") or {}) if config else {}

    configurable = (config or {}).get("configurable") or {}
    config_thread = configurable.get("thread_id")
    if config_thread:
        _normalize_thread_fields(meta, str(config_thread))

    thread_id = (
        meta.get("thread_id")
        or meta.get("conversation_id")
        or meta.get("session_id")
        or fallback_conversation_id
    )
    if thread_id:
        _normalize_thread_fields(meta, str(thread_id))

    return {k: meta[k] for k in _THREAD_METADATA_KEYS if k in meta}


def resolve_thread_id_from_config(config: dict[str, Any] | None) -> str | None:
    """Read the session thread id from a RunnableConfig."""
    meta = extract_thread_metadata(config)
    return meta.get("thread_id") or meta.get("conversation_id")


# Alias for callers that import from infrastructure.tracing
enrich_config_with_thread = enrich_invoke_config_with_conversation


def build_child_run_config(
    parent: dict[str, Any] | None,
    *,
    run_name: str,
    extra_metadata: dict[str, Any] | None = None,
    thread_id: str | None = None,
) -> dict[str, Any]:
    """Build a child RunnableConfig that preserves callbacks and thread metadata.

    Callback handlers (LangSmith tracers) must be passed by reference — they are not
    picklable and will raise if deep-copied.
    """
    fallback = thread_id
    if not fallback and extra_metadata:
        fallback = (
            extra_metadata.get("thread_id")
            or extra_metadata.get("conversation_id")
            or extra_metadata.get("session_id")
        )
        if fallback is not None:
            fallback = str(fallback)

    meta = extract_thread_metadata(parent, fallback_conversation_id=fallback)
    if extra_metadata:
        meta.update(extra_metadata)
    if fallback:
        _normalize_thread_fields(meta, str(fallback))

    if not parent:
        child: dict[str, Any] = {"run_name": run_name, "metadata": meta}
        if fallback:
            child["configurable"] = {"thread_id": str(fallback)}
        return child

    child = {"run_name": run_name, "metadata": meta}

    # Shallow-copy only serializable fields; never deepcopy callbacks or run_id.
    if parent.get("callbacks") is not None:
        child["callbacks"] = parent["callbacks"]
    if parent.get("tags") is not None:
        child["tags"] = list(parent["tags"])
    configurable = dict(parent.get("configurable") or {})
    if fallback:
        configurable["thread_id"] = str(fallback)
    if configurable:
        child["configurable"] = configurable

    return child


def build_graph_invoke_config(
    *,
    conversation_id: UUID | str,
    app_env: str,
    app_name: str,
    user_query: str,
    extra_tags: list[str] | None = None,
) -> dict[str, Any]:
    """Build RunnableConfig for LangGraph chat invocation with thread + request metadata."""
    thread_id = str(conversation_id)
    tags = [app_env]
    if extra_tags:
        tags.extend(extra_tags)

    query_preview = user_query.strip()[:80] or "empty"
    metadata = _thread_metadata(
        conversation_id=thread_id,
        request_id=get_request_id(),
        app_name=app_name,
        app_env=app_env,
        user_query=user_query,
    )

    return {
        "run_name": f"chat: {query_preview}",
        "tags": tags,
        "metadata": metadata,
        "configurable": {"thread_id": thread_id},
    }


def make_graph_invoke_config_builder(
    settings: Settings,
    *,
    extra_tags: list[str] | None = None,
):
    """Return a callable bound to settings for DI injection into ChatOrchestrator."""

    def builder(*, conversation_id: UUID | str, user_query: str) -> dict[str, Any]:
        return build_graph_invoke_config(
            conversation_id=conversation_id,
            app_env=settings.app_env,
            app_name=settings.app_name,
            user_query=user_query,
            extra_tags=extra_tags,
        )

    return builder
