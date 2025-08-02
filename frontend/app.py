"""
Streamlit frontend application for Agentic PRD Generation.

This is the main entry point for the web UI that allows users to
generate PRDs and Technical Specifications through an agentic workflow.
"""

import json

import httpx
from httpx_sse import connect_sse
import streamlit as st


def main() -> None:
    """Main Streamlit application."""
    st.set_page_config(
        page_title="Agentic PRD Generation",
        page_icon="🛠️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("🛠️ Agentic PRD Generation")
    st.markdown(
        "*AI-powered platform for iterative PRD and Technical Specification generation*"
    )

    # Initialize session state
    if "run_id" not in st.session_state:
        st.session_state.run_id = None
    if "prd_content" not in st.session_state:
        st.session_state.prd_content = "*Your generated PRD will appear here.*"
    if "status" not in st.session_state:
        st.session_state.status = "Idle"
    if "diff" not in st.session_state:
        st.session_state.diff = ""

    # --- UI Layout ---

    # Sidebar configuration
    with st.sidebar:
        st.header("Configuration")
        st.selectbox("Autonomy Level", ["Full", "Supervised"], key="autonomy_level")
        st.selectbox(
            "Adapter",
            ["vanilla_openai", "vanilla_google", "crewai"],
            key="adapter",
        )
        st.text_input(
            "Backend API URL",
            value="http://localhost:8000",
            key="api_url",
        )

    # Main content area
    col1, col2 = st.columns([2, 1])

    with col1:
        st.header("Project Idea")
        st.text_area(
            "Describe your project idea:",
            placeholder="e.g., A mobile app that uses AI to identify plants from photos.",
            height=100,
            key="project_idea",
        )

        if st.button("Generate PRD", type="primary"):
            if not st.session_state.project_idea:
                st.error("Please enter a project idea.")
            else:
                start_generation()

        st.header("Live PRD")
        st.markdown(st.session_state.prd_content)

    with col2:
        st.header("Status")
        st.info(f"**Workflow Step:** {st.session_state.status}")

        st.header("Revision Diff")
        if st.session_state.diff:
            st.code(st.session_state.diff, language="diff")
        else:
            st.info("*No diff available yet.*")


def start_generation() -> None:
    """Initiates the PRD generation process."""
    api_url = st.session_state.api_url
    payload = {
        "idea": st.session_state.project_idea,
        "autonomy_level": st.session_state.autonomy_level,
        "adapter": st.session_state.adapter,
    }

    try:
        with httpx.Client() as client:
            response = client.post(f"{api_url}/api/v1/generate_prd", json=payload)
            response.raise_for_status()
            data = response.json()
            st.session_state.run_id = data["run_id"]
            st.session_state.status = "Starting..."
            listen_for_updates()
    except httpx.RequestError as e:
        st.error(f"Could not connect to backend: {e}")
    except httpx.HTTPStatusError as e:
        st.error(f"Error from backend: {e.response.status_code} - {e.response.text}")


def listen_for_updates() -> None:
    """Connects to the SSE stream and updates the UI."""
    if not st.session_state.run_id:
        return

    api_url = st.session_state.api_url
    run_id = st.session_state.run_id
    url = f"{api_url}/api/v1/stream/{run_id}"

    try:
        with connect_sse(httpx.Client(), "GET", url) as event_source:
            st.info(f"Connected to stream for run ID: {run_id}")
            for sse in event_source.iter_sse():
                if sse.event == "message":
                    update_state(json.loads(sse.data))
                    st.rerun()  # Rerun to update the UI
    except httpx.HTTPStatusError as e:
        st.error(f"Error connecting to stream: {e.response.status_code}")
        st.session_state.status = "Error"
    except Exception as e:
        st.warning(f"Stream disconnected: {e}")
        if st.session_state.status not in ("Complete", "Error"):
            st.session_state.status = "Finished"


def update_state(data: dict) -> None:
    """Updates the session state with data from the stream."""
    st.session_state.status = data.get("step", "Unknown")
    st.session_state.prd_content = data.get("content", "*No content received.*")
    st.session_state.diff = data.get("diff", "")


if __name__ == "__main__":
    main()
