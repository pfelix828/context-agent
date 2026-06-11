"""
Streamlit UI for the Context-Aware Data Analysis Agent.
"""

# === macOS fork crash prevention (must run before ALL other imports) ===
# On macOS 26+, fork() crashes when the Network framework is loaded in a
# multi-threaded process.  The Network framework gets pulled in by Python's
# _scproxy module (system proxy detection).  Mocking _scproxy before any
# networking imports prevents the framework from loading at all.
import os
import sys
import types

if sys.platform == "darwin":
    os.environ["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"
    os.environ["no_proxy"] = "*"

    _fake = types.ModuleType("_scproxy")
    _fake._get_proxy_settings = lambda: {}
    _fake._get_proxies = lambda: {}
    sys.modules["_scproxy"] = _fake

    import multiprocessing
    try:
        multiprocessing.set_start_method("spawn")
    except RuntimeError:
        pass  # already set

import json
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

import streamlit as st
import plotly.io as pio

from src.agent import create_agent
from src.context_loader import load_context, load_skills, list_teams


st.set_page_config(
    page_title="Context Agent",
    page_icon="📊",
    layout="wide",
)

# Team display config
TEAM_CONFIG = {
    "Executive": {"icon": "💼", "greeting": "I'm your executive analytics partner. Ask me about ARR, bookings, unit economics, and company-level performance."},
    "Marketing": {"icon": "📣", "greeting": "I'm your marketing analytics partner. Ask me about campaigns, pipeline contribution, MQLs, and budget allocation."},
    "Sales": {"icon": "💰", "greeting": "I'm your sales analytics partner. Ask me about pipeline health, win rates, forecast, and deal velocity."},
    "Product": {"icon": "🔧", "greeting": "I'm your product analytics partner. Ask me about user engagement, feature adoption, and usage trends."},
}

SAMPLE_QUESTIONS = {
    "Executive": [
        ("📈 ARR Overview", "What's our current ARR and how is it trending?"),
        ("🎯 Bookings vs Plan", "Are we on track to hit our bookings target this quarter?"),
        ("💰 Unit Economics", "What's our LTV/CAC ratio by segment?"),
        ("📊 Revenue Mix", "How does our revenue break down by segment?"),
    ],
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


def _get_api_key() -> str | None:
    """Get API key from environment, secrets, or sidebar input."""
    # Check environment variable first (local dev)
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return key

    # Check Streamlit secrets (Streamlit Cloud deployment)
    try:
        key = st.secrets.get("ANTHROPIC_API_KEY")
        if key:
            return key
    except Exception:
        pass

    # Fall back to sidebar input (visitor provides their own key)
    return st.session_state.get("user_api_key")


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

    # API key input if not set via environment
    if not os.environ.get("ANTHROPIC_API_KEY"):
        try:
            has_secret = bool(st.secrets.get("ANTHROPIC_API_KEY"))
        except Exception:
            has_secret = False

        if not has_secret:
            st.sidebar.subheader("🔑 API Key")
            api_key = st.sidebar.text_input(
                "Anthropic API Key",
                type="password",
                value=st.session_state.get("user_api_key", ""),
                placeholder="sk-ant-...",
                label_visibility="collapsed",
            )
            if api_key:
                st.session_state.user_api_key = api_key
                os.environ["ANTHROPIC_API_KEY"] = api_key
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

    # Data sources
    st.sidebar.subheader("📁 Available Data")
    st.sidebar.markdown("- Accounts & Segments")
    st.sidebar.markdown("- Leads & Funnel Stages")
    st.sidebar.markdown("- Campaigns & Attribution")
    st.sidebar.markdown("- Opportunities & Pipeline")
    st.sidebar.markdown("- Product Usage")
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


def render_figures(figures: list[str]):
    """Render Plotly figures from JSON strings."""
    for fig_json in figures:
        fig = pio.from_json(fig_json)
        st.plotly_chart(fig, use_container_width=True)


def get_response(agent, prompt: str) -> dict:
    """Get an agent response with a spinner and render results."""
    start_time = time.time()

    with st.spinner("Analyzing..."):
        response = agent.ask(prompt)

    st.markdown(response.text)
    render_figures(response.figures)

    elapsed = time.time() - start_time
    st.caption(f"Response time: {elapsed:.1f}s")

    return {
        "text": response.text,
        "figures": response.figures,
    }


def main():
    # Check for API key
    api_key = _get_api_key()
    if not api_key:
        st.warning(
            "Please enter your Anthropic API key in the sidebar to get started. "
            "Your key stays in your browser session only — it is never stored."
        )

    selected_team = render_sidebar()

    # Don't proceed without API key
    if not _get_api_key():
        st.stop()

    try:
        agent = get_or_create_agent(selected_team)
    except Exception as e:
        error_name = type(e).__name__
        if "AuthenticationError" in error_name:
            st.error("Invalid API key. Please check your Anthropic API key and try again.")
        else:
            st.error(f"Failed to initialize agent: {e}")
        st.stop()

    # Display chat history
    for msg in st.session_state.get("messages", []):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("figures"):
                render_figures(msg["figures"])

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
            try:
                result = get_response(agent, prompt)
            except Exception as e:
                error_name = type(e).__name__
                if "RateLimitError" in error_name:
                    st.error("Rate limit exceeded. Please wait a moment and try again.")
                elif "AuthenticationError" in error_name:
                    st.error("Invalid API key. Please check your Anthropic API key.")
                elif "APIConnectionError" in error_name:
                    st.error("Could not connect to the Anthropic API. Please check your internet connection.")
                else:
                    st.error(f"An error occurred: {e}")
                result = {"text": "", "figures": []}

        if result["text"]:
            st.session_state.messages.append({
                "role": "assistant",
                "content": result["text"],
                "figures": result.get("figures", []),
            })


if __name__ == "__main__":
    main()
