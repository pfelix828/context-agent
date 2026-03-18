"""
Simple CLI for testing the context-aware data analysis agent.
"""

from .agent import create_agent


def main():
    print("Context-Aware Data Analysis Agent")
    print("=" * 40)
    print("Type your question, or 'quit' to exit.\n")

    agent = create_agent()

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
