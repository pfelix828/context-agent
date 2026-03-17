"""
Streamlit UI for the Context-Aware Data Analysis Agent.
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

import streamlit as st
from src.agent import create_agent
from src.context_loader import load_context, load_skills
from src.executor import get_schema_summary


st.set_page_config(
    page_title="Context Agent",
    page_icon="📊",
    layout="wide",
)


def init_agent():
    """Initialize or retrieve the agent from session state."""
    if "agent" not in st.session_state:
        st.session_state.agent = create_agent()
    if "messages" not in st.session_state:
        st.session_state.messages = []
    return st.session_state.agent


def render_sidebar():
    """Render the sidebar with context information."""
    context = load_context()
    skills = load_skills()

    st.sidebar.title("📊 Context Agent")
    st.sidebar.markdown("*AI-powered data analyst that adapts to the stakeholder*")
    st.sidebar.divider()

    # Stakeholder info
    st.sidebar.subheader("👤 Active Stakeholder")
    if "stakeholder" in context:
        lines = context["stakeholder"].split("\n")
        for line in lines:
            if line.startswith("- **Name**"):
                st.sidebar.markdown(line)
            elif line.startswith("- **Role**"):
                st.sidebar.markdown(line)
            elif line.startswith("- **Reports to**"):
                st.sidebar.markdown(line)
    st.sidebar.divider()

    # Available skills
    st.sidebar.subheader("🛠️ Analysis Skills")
    for name in skills:
        display_name = name.replace("_", " ").title()
        st.sidebar.markdown(f"- {display_name}")
    st.sidebar.divider()

    # Database info
    st.sidebar.subheader("🗄️ Database")
    schema = get_schema_summary()
    for line in schema.split("\n"):
        st.sidebar.markdown(line, unsafe_allow_html=True)
    st.sidebar.divider()

    # Context files
    st.sidebar.subheader("📁 Context Files")
    for name in context:
        st.sidebar.markdown(f"- `context/{name}.md`")

    # Reset button
    st.sidebar.divider()
    if st.sidebar.button("🔄 New Conversation", use_container_width=True):
        st.session_state.agent.reset()
        st.session_state.messages = []
        st.rerun()


def render_sample_questions():
    """Show sample questions when the chat is empty."""
    st.markdown("### Ask me anything about your GTM data")
    st.markdown("I'm configured for **Sarah Chen, VP of Marketing**. "
                "I'll analyze the data and deliver insights tailored to her priorities.")

    cols = st.columns(2)
    samples = [
        ("🔍 Funnel Analysis", "How is the funnel performing this quarter?"),
        ("💰 Campaign ROI", "Which campaigns should I cut and which should I double down on?"),
        ("📊 Segmentation", "How do our segments compare on pipeline and win rate?"),
        ("📈 Pipeline Forecast", "Are we going to hit our pipeline target this quarter?"),
        ("🎯 Channel Mix", "What's our most efficient channel for generating SQLs?"),
        ("⚡ Quick Stat", "What's our overall MQL to closed-won conversion rate?"),
    ]

    for i, (label, question) in enumerate(samples):
        col = cols[i % 2]
        if col.button(label, key=f"sample_{i}", use_container_width=True):
            return question
    return None


def main():
    agent = init_agent()
    render_sidebar()

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Show sample questions if no messages yet
    prompt = None
    if not st.session_state.messages:
        prompt = render_sample_questions()

    # Chat input
    user_input = st.chat_input("Ask a question about your data...")
    prompt = prompt or user_input

    if prompt:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get agent response
        with st.chat_message("assistant"):
            with st.spinner("Analyzing..."):
                response = agent.ask(prompt)
            st.markdown(response)

        st.session_state.messages.append({"role": "assistant", "content": response})


if __name__ == "__main__":
    main()
