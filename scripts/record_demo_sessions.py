"""Record real agent sessions for the demo-mode replay.

Runs the actual agent (real Claude API calls, real SQL/Python execution against
data/gtm.duckdb) on a fixed question list and persists complete transcripts —
question, every tool call with its input and output, figures, response text,
and timing — to demo_sessions/*.json.

These recordings are what the deployed app replays in demo mode. Nothing in
them is edited or fabricated; re-running this script regenerates them from
scratch (results may differ slightly since the model is not deterministic).

Usage: .venv/bin/python scripts/record_demo_sessions.py
Requires ANTHROPIC_API_KEY in .env (this costs real API usage: 8 questions).
"""

import json
import sys
import time
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

from src.agent import MODEL, StreamComplete, ToolResult, ToolStart, create_agent

SESSIONS_DIR = PROJECT_ROOT / "demo_sessions"

QUESTIONS = [
    ("Executive", "What's our current ARR and how is it trending?"),
    ("Executive", "How does our revenue break down by segment?"),
    ("Marketing", "How is the funnel performing this quarter?"),
    ("Marketing", "Which campaigns should I cut and which should I double down on?"),
    ("Sales", "How do win rates compare across segments?"),
    ("Sales", "Show me the largest open opportunities and their stages."),
    ("Product", "What are our DAU trends over the last 6 months?"),
    ("Product", "How does product usage compare across SMB, Mid-Market, and Enterprise?"),
]


def record_one(team: str, question: str) -> dict:
    agent = create_agent(team=team)
    steps = []
    final_text = ""
    final_figures = []

    t0 = time.time()
    for event in agent.ask_stream(question):
        if isinstance(event, ToolStart):
            steps.append({"tool": event.tool_name, "input": event.tool_input,
                          "output": None, "figures": []})
        elif isinstance(event, ToolResult):
            if steps and steps[-1]["output"] is None:
                steps[-1]["output"] = event.output
                steps[-1]["figures"] = event.figures
        elif isinstance(event, StreamComplete):
            final_text = event.response.text
            final_figures = event.response.figures
    elapsed = time.time() - t0

    return {
        "team": team,
        "question": question,
        "steps": steps,
        "text": final_text,
        "figures": final_figures,
        "elapsed_s": round(elapsed, 1),
        "model": MODEL,
        "recorded_at": date.today().isoformat(),
    }


def main() -> None:
    SESSIONS_DIR.mkdir(exist_ok=True)
    counters: dict[str, int] = {}

    for team, question in QUESTIONS:
        counters[team] = counters.get(team, 0) + 1
        name = f"{team.lower()}_{counters[team]}.json"
        print(f"Recording [{team}] {question!r} ...", flush=True)
        session = record_one(team, question)
        path = SESSIONS_DIR / name
        path.write_text(json.dumps(session, indent=1))
        print(f"  -> {path.name}: {len(session['steps'])} tool calls, "
              f"{len(session['figures'])} figures, {session['elapsed_s']}s, "
              f"{len(session['text'])} chars", flush=True)

    print("\nDone. Review the transcripts, then commit demo_sessions/.")


if __name__ == "__main__":
    main()
