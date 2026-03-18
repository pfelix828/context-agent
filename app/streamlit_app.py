"""
Streamlit UI for the Context-Aware Data Analysis Agent.
"""

import os
import sys
import json
import time
from pathlib import Path

# Fix macOS fork crash with multi-threaded processes (DuckDB + Streamlit)
os.environ["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

import streamlit as st
import plotly.io as pio

from src.agent import create_agent, TextDelta, ToolStart, ToolResult, StreamComplete
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


def stream_response(agent, prompt: str) -> dict:
    """Stream an agent response with live text and tool status indicators."""
    start_time = time.time()
    text_placeholder = st.empty()
    accumulated_text = ""
    all_figures = []
    final_response = None
    active_status = None

    for event in agent.ask_stream(prompt):
        if isinstance(event, TextDelta):
            accumulated_text += event.text
            text_placeholder.markdown(accumulated_text + "▌")

        elif isinstance(event, ToolStart):
            tool_label = {
                "run_sql": "Running SQL query...",
                "run_python": "Executing Python...",
            }.get(event.tool_name, f"Running {event.tool_name}...")

            active_status = st.status(tool_label, expanded=False)
            if event.tool_name == "run_sql":
                active_status.code(event.tool_input.get("query", ""), language="sql")
            elif event.tool_name == "run_python":
                active_status.code(event.tool_input.get("code", ""), language="python")

        elif isinstance(event, ToolResult):
            if event.figures:
                all_figures.extend(event.figures)
            if active_status:
                active_status.update(label=f"{event.tool_name} complete", state="complete")
                active_status = None

        elif isinstance(event, StreamComplete):
            final_response = event.response
            all_figures = final_response.figures

    # Render final text (remove cursor)
    if accumulated_text:
        text_placeholder.markdown(accumulated_text)

    # Render any figures
    render_figures(all_figures)

    elapsed = time.time() - start_time

    # Response metadata footer
    st.caption(f"Response time: {elapsed:.1f}s")

    return {
        "text": accumulated_text,
        "figures": all_figures,
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

        # Get agent response with streaming
        with st.chat_message("assistant"):
            try:
                result = stream_response(agent, prompt)
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
