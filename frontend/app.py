"""Streamlit frontend application for Agentic PRD Generation."""

import json
import os
from typing import Any

import httpx
from httpx_sse import connect_sse
import streamlit as st

DEFAULT_PRD_CONTENT = "*Your generated PRD will appear here.*"
TERMINAL_STEPS = {"Complete", "Error"}
IMPLEMENTED_ADAPTERS = ["vanilla_openai", "vanilla_google"]


def main() -> None:
    """Main Streamlit application."""
    st.set_page_config(
        page_title="Agentic PRD Generation",
        page_icon="🛠️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    initialize_session_state()

    st.title("🛠️ Agentic PRD Generation")
    st.markdown("*AI-powered platform for iterative PRD generation*")

    with st.sidebar:
        st.header("Configuration")
        st.selectbox("Adapter", IMPLEMENTED_ADAPTERS, key="adapter")
        st.text_input(
            "Backend API URL",
            value=os.getenv("BACKEND_URL", "http://localhost:8000"),
            key="api_url",
        )

    col1, col2 = st.columns([2, 1])

    with col1:
        st.header("Project Idea")
        st.text_area(
            "Describe your project idea:",
            placeholder="e.g., A mobile app that uses AI to identify plants from photos.",
            height=100,
            key="project_idea",
        )
        if st.button(
            "Generate PRD",
            type="primary",
            disabled=st.session_state.stream_active,
        ):
            if not st.session_state.project_idea.strip():
                st.error("Please enter a project idea.")
            else:
                start_generation()
        prd_placeholder = st.empty()

    with col2:
        status_placeholder = st.empty()
        error_placeholder = st.empty()
        diff_placeholder = st.empty()

    render_state(
        prd_placeholder=prd_placeholder,
        status_placeholder=status_placeholder,
        diff_placeholder=diff_placeholder,
        error_placeholder=error_placeholder,
    )

    if should_resume_stream():
        listen_for_updates(
            prd_placeholder=prd_placeholder,
            status_placeholder=status_placeholder,
            diff_placeholder=diff_placeholder,
            error_placeholder=error_placeholder,
        )


def initialize_session_state() -> None:
    """Seed Streamlit session state defaults."""
    defaults: dict[str, Any] = {
        "run_id": None,
        "prd_content": DEFAULT_PRD_CONTENT,
        "status": "Idle",
        "diff": "",
        "error": None,
        "stream_active": False,
        "project_idea": "",
        "adapter": IMPLEMENTED_ADAPTERS[0],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def start_generation() -> None:
    """Initiate the PRD generation process."""
    payload = build_generation_payload(
        idea=st.session_state.project_idea,
        adapter=st.session_state.adapter,
    )

    try:
        with httpx.Client() as client:
            response = client.post(
                f"{st.session_state.api_url}/api/v1/generate_prd",
                json=payload,
            )
            response.raise_for_status()
        data = response.json()
        st.session_state.run_id = data["run_id"]
        st.session_state.status = "Outline"
        st.session_state.prd_content = (
            f"# PRD for {payload['idea']}\n\n_Starting outline generation..._"
        )
        st.session_state.diff = ""
        st.session_state.error = None
        st.session_state.stream_active = True
    except httpx.RequestError as exc:
        st.session_state.stream_active = False
        st.error(f"Could not connect to backend: {exc}")
    except httpx.HTTPStatusError as exc:
        st.session_state.stream_active = False
        st.error(
            f"Error from backend: {exc.response.status_code} - {exc.response.text}"
        )


def listen_for_updates(
    *,
    prd_placeholder: Any,
    status_placeholder: Any,
    diff_placeholder: Any,
    error_placeholder: Any,
) -> None:
    """Connect to the SSE stream and update the UI in-place."""
    if not st.session_state.run_id:
        return

    st.session_state.stream_active = True
    url = build_stream_url(st.session_state.api_url, st.session_state.run_id)
    timeout = httpx.Timeout(timeout=None, connect=5.0)

    try:
        with connect_sse(httpx.Client(timeout=timeout), "GET", url) as event_source:
            for sse in event_source.iter_sse():
                if sse.event != "message":
                    continue
                update_state(json.loads(sse.data))
                render_state(
                    prd_placeholder=prd_placeholder,
                    status_placeholder=status_placeholder,
                    diff_placeholder=diff_placeholder,
                    error_placeholder=error_placeholder,
                )
                if is_terminal_step(st.session_state.status):
                    st.session_state.stream_active = False
                    return
    except httpx.HTTPStatusError as exc:
        st.session_state.status = "Error"
        st.session_state.error = (
            f"Stream connection failed with status {exc.response.status_code}."
        )
    except httpx.RequestError as exc:
        st.session_state.error = f"Stream request failed: {exc}"
    except Exception as exc:  # pragma: no cover - defensive UI fallback
        st.session_state.status = "Error"
        st.session_state.error = f"Stream disconnected unexpectedly: {exc}"
    finally:
        st.session_state.stream_active = False
        render_state(
            prd_placeholder=prd_placeholder,
            status_placeholder=status_placeholder,
            diff_placeholder=diff_placeholder,
            error_placeholder=error_placeholder,
        )


def update_state(data: dict[str, Any]) -> None:
    """Update session state with data from the stream."""
    ui_state = coerce_stream_state(data)
    st.session_state.status = ui_state["status"]
    st.session_state.prd_content = ui_state["prd_content"]
    st.session_state.diff = ui_state["diff"]
    st.session_state.error = ui_state["error"]


def build_generation_payload(idea: str, adapter: str) -> dict[str, str]:
    """Create the backend payload for a new PRD run."""
    return {"idea": idea.strip(), "adapter": adapter}


def build_stream_url(api_url: str, run_id: str) -> str:
    """Build the SSE URL for a run."""
    return f"{api_url}/api/v1/stream/{run_id}"


def is_terminal_step(step: str) -> bool:
    """Return whether a workflow step is terminal."""
    return step in TERMINAL_STEPS


def should_resume_stream() -> bool:
    """Return whether the current session should keep listening for updates."""
    return bool(st.session_state.run_id) and not is_terminal_step(
        st.session_state.status
    )


def coerce_stream_state(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize a raw stream event into UI state."""
    return {
        "status": data.get("step", "Unknown"),
        "prd_content": data.get("content", DEFAULT_PRD_CONTENT),
        "diff": data.get("diff", "") or "",
        "error": data.get("error"),
    }


def render_state(
    *,
    prd_placeholder: Any,
    status_placeholder: Any,
    diff_placeholder: Any,
    error_placeholder: Any,
) -> None:
    """Render the current session state into placeholder containers."""
    with prd_placeholder.container():
        st.header("Live PRD")
        st.markdown(st.session_state.prd_content)

    with status_placeholder.container():
        st.header("Status")
        st.info(f"**Workflow Step:** {st.session_state.status}")

    if st.session_state.error:
        with error_placeholder.container():
            st.error(st.session_state.error)
    elif st.session_state.status == "Complete":
        with error_placeholder.container():
            st.success("PRD generation completed.")
    else:
        error_placeholder.empty()

    with diff_placeholder.container():
        st.header("Revision Diff")
        if st.session_state.diff:
            st.code(st.session_state.diff, language="diff")
        else:
            st.info("*No diff available yet.*")


if __name__ == "__main__":
    main()
