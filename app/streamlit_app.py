"""
Streamlit UI for the Context-Aware Data Analysis Agent.
"""

import os
import sys
from pathlib import Path

# Fix macOS fork crash with multi-threaded processes (DuckDB + Streamlit)
os.environ["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

import streamlit as st
from src.agent import create_agent
from src.context_loader import load_context, load_skills, list_teams
from src.executor import get_schema_summary


st.set_page_config(
    page_title="Context Agent",
    page_icon="📊",
    layout="wide",
)

# Team display config
TEAM_CONFIG = {
    "Marketing": {"icon": "📣", "greeting": "I'm your marketing analytics partner. Ask me about campaigns, pipeline contribution, MQLs, and budget allocation."},
    "Sales": {"icon": "💰", "greeting": "I'm your sales analytics partner. Ask me about pipeline health, win rates, forecast, and deal velocity."},
    "Product": {"icon": "🔧", "greeting": "I'm your product analytics partner. Ask me about user engagement, feature adoption, and usage trends."},
}

SAMPLE_QUESTIONS = {
    "Marketing": [
        ("🔍 Funnel Analysis", "How is the funnel performing this quarter?"),
        ("💰 Campaign ROI", "Which campaigns should I cut and which should I double down on?"),
        ("📊 Channel Mix", "What's our most efficient channel for generating SQLs?"),
        ("🎯 Lead Quality", "How does MQL-to-SQL conversion vary by channel?"),
    ],
    "Sales": [
        ("📈 Pipeline Health", "Are we going to hit our pipeline target this quarter?"),
        ("🏆 Win Rates", "How do win rates compare across segments?"),
        ("⏱️ Deal Velocity", "What's our average sales cycle by segment?"),
        ("💼 Top Deals", "Show me the largest open opportunities and their stages."),
    ],
    "Product": [
        ("👥 Active Users", "What are our DAU trends over the last 6 months?"),
        ("📊 Segment Usage", "How does product usage compare across SMB, Mid-Market, and Enterprise?"),
        ("🔌 API Adoption", "Which accounts have the highest API usage?"),
        ("💾 Feature Depth", "What's the relationship between features used and account retention?"),
    ],
}


def get_or_create_agent(team: str):
    """Get the agent for the selected team, creating a new one if the team changed."""
    if "agent" not in st.session_state or st.session_state.get("active_team") != team:
        st.session_state.agent = create_agent(team=team)
        st.session_state.active_team = team
        st.session_state.messages = []
    return st.session_state.agent


def render_sidebar():
    """Render the sidebar with team selector and context info."""
    st.sidebar.title("📊 Context Agent")
    st.sidebar.markdown("*AI-powered data analyst that adapts to the team*")
    st.sidebar.divider()

    # Team selector
    teams = list_teams()
    st.sidebar.subheader("👥 Select Team")
    selected_team = st.sidebar.selectbox(
        "Team",
        teams,
        index=teams.index("Marketing") if "Marketing" in teams else 0,
        label_visibility="collapsed",
    )

    config = TEAM_CONFIG.get(selected_team, {"icon": "📊"})
    st.sidebar.divider()

    # Show active team profile summary
    st.sidebar.subheader(f"{config['icon']} {selected_team} Team")
    context = load_context(team=selected_team)
    if "stakeholder" in context:
        # Show "What They Care About" section
        lines = context["stakeholder"].split("\n")
        in_section = False
        for line in lines:
            if "What They Care About" in line:
                in_section = True
                st.sidebar.markdown("**Key Metrics:**")
                continue
            elif line.startswith("## ") and in_section:
                break
            elif in_section and line.startswith("- "):
                st.sidebar.markdown(line)
    st.sidebar.divider()

    # Available skills
    skills = load_skills()
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

    # Reset button
    if st.sidebar.button("🔄 New Conversation", use_container_width=True):
        st.session_state.agent = create_agent(team=selected_team)
        st.session_state.messages = []
        st.rerun()

    return selected_team


def render_sample_questions(team: str):
    """Show sample questions for the selected team."""
    config = TEAM_CONFIG.get(team, {"icon": "📊", "greeting": "Ask me anything about your data."})

    st.markdown(f"### {config['icon']} {team} Analytics")
    st.markdown(config["greeting"])

    samples = SAMPLE_QUESTIONS.get(team, [])
    cols = st.columns(2)

    for i, (label, question) in enumerate(samples):
        col = cols[i % 2]
        if col.button(label, key=f"sample_{i}", use_container_width=True):
            return question
    return None


def main():
    selected_team = render_sidebar()
    agent = get_or_create_agent(selected_team)

    # Display chat history
    for msg in st.session_state.get("messages", []):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Show sample questions if no messages yet
    prompt = None
    if not st.session_state.get("messages"):
        prompt = render_sample_questions(selected_team)

    # Chat input
    user_input = st.chat_input("Ask a question about your data...")
    prompt = prompt or user_input

    if prompt:
        # Initialize messages if needed
        if "messages" not in st.session_state:
            st.session_state.messages = []

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
