"""
Streamlit frontend application for Agentic PRD Generation.

This is the main entry point for the web UI that allows users to
generate PRDs and Technical Specifications through an agentic workflow.
"""

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

    # Sidebar configuration
    with st.sidebar:
        st.header("Configuration")
        st.info("Backend API: Coming soon...")

    # Main content area
    col1, col2 = st.columns([2, 1])

    with col1:
        st.header("Project Idea Input")
        project_idea = st.text_area(  # noqa: F841
            "Describe your project idea:",
            placeholder="Enter a high-level description of your project...",
            height=100,
        )

        if st.button("Generate PRD", type="primary", disabled=True):
            st.info("🚧 Implementation in progress...")

    with col2:
        st.header("Status")
        st.info("🔧 Setting up the agentic workflow...")

        st.header("Configuration")
        st.selectbox("Autonomy Level", ["Full", "Supervised"], disabled=True)
        st.selectbox(
            "Framework", ["Vanilla OpenAI", "Vanilla Google", "CrewAI"], disabled=True
        )


if __name__ == "__main__":
    main()
