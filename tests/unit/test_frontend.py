"""Unit tests for frontend helper functions."""

import streamlit as st

from frontend.app import (
    DEFAULT_PRD_CONTENT,
    build_generation_payload,
    build_stream_url,
    coerce_stream_state,
    is_terminal_step,
    mark_stream_error,
)


def test_build_generation_payload_trims_idea() -> None:
    """Payload building should trim leading and trailing whitespace."""
    payload = build_generation_payload("  test idea  ", "vanilla_openai")
    assert payload == {"idea": "test idea", "adapter": "vanilla_openai"}


def test_build_stream_url() -> None:
    """The stream URL should be derived from the backend base URL."""
    assert build_stream_url("http://localhost:8000", "run-1") == (
        "http://localhost:8000/api/v1/stream/run-1"
    )


def test_is_terminal_step() -> None:
    """Only terminal run states should return true."""
    assert is_terminal_step("Complete")
    assert is_terminal_step("Error")
    assert not is_terminal_step("Draft")


def test_coerce_stream_state_defaults() -> None:
    """Missing event fields should fall back to safe UI defaults."""
    assert coerce_stream_state({}) == {
        "status": "Unknown",
        "prd_content": DEFAULT_PRD_CONTENT,
        "diff": "",
        "error": None,
    }


def test_mark_stream_error_sets_terminal_state() -> None:
    """Transport failures should move the UI to a terminal error state."""
    st.session_state.status = "Draft"
    st.session_state.error = None

    mark_stream_error("backend unavailable")

    assert st.session_state.status == "Error"
    assert st.session_state.error == "backend unavailable"
