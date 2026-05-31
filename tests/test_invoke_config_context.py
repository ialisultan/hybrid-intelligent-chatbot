"""Session thread id helpers for LangGraph invoke config."""

from uuid import uuid4

import pytest

from src.application.context import enrich_invoke_config_with_conversation

pytestmark = pytest.mark.unit


def test_enrich_preserves_callbacks_and_sets_thread():
    conversation_id = str(uuid4())
    parent = {"callbacks": ["tracer"], "metadata": {"request_id": "r1"}}
    enriched = enrich_invoke_config_with_conversation(parent, conversation_id)

    assert enriched["callbacks"] == ["tracer"]
    assert enriched["metadata"]["thread_id"] == conversation_id
    assert enriched["metadata"]["request_id"] == "r1"
    assert enriched["configurable"]["thread_id"] == conversation_id
