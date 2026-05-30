"""Context helper unit tests."""

import pytest

from src.application.context import build_contextual_query, filter_current_turn

pytestmark = pytest.mark.unit


def test_build_contextual_query_empty_history():
    assert build_contextual_query("Hello", []) == "Hello"


def test_build_contextual_query_includes_prior_turns():
    messages = [
        {"role": "user", "content": "Hi"},
        {"role": "assistant", "content": "Hello!"},
    ]
    result = build_contextual_query("Follow up", messages)
    assert "Previous conversation:" in result
    assert "User: Hi" in result
    assert "Current question: Follow up" in result


def test_filter_current_turn_removes_matching_last_user_message():
    messages = [
        {"role": "user", "content": "old"},
        {"role": "assistant", "content": "answer"},
        {"role": "user", "content": "current"},
    ]
    assert len(filter_current_turn(messages, "current")) == 2


def test_filter_current_turn_keeps_all_when_no_match():
    messages = [{"role": "user", "content": "other"}]
    assert filter_current_turn(messages, "current") == messages
