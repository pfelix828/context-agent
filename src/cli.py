"""
Simple CLI for testing the context-aware data analysis agent.
"""

import argparse

from .agent import create_agent
from .context_loader import list_teams


VALID_TEAMS = ["executive", "marketing", "product", "sales"]


def main():
    parser = argparse.ArgumentParser(description="Context-Aware Data Analysis Agent")
    parser.add_argument(
        "--team",
        type=str,
        choices=VALID_TEAMS,
        default=None,
        help="Stakeholder team profile to load (e.g., marketing, sales)",
    )
    args = parser.parse_args()

    print("Context-Aware Data Analysis Agent")
    print("=" * 40)

    if args.team is None:
        available = list_teams()
        print(f"Available teams: {', '.join(available)}")
        print("Note: Running without a team means no stakeholder profile is loaded.\n")
    else:
        print(f"Team: {args.team.title()}\n")

    print("Type your question, or 'quit' to exit.\n")

    agent = create_agent(team=args.team.title() if args.team else None)

    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not question:
            continue
        if question.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        print("\nAnalyzing...\n")
        response = agent.ask(question)
        print(f"\n{response.text}\n")
        print("-" * 40 + "\n")


if __name__ == "__main__":
    main()
