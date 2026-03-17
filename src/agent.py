"""
Context-aware data analysis agent.

Uses Claude's tool use to execute SQL and Python against a DuckDB database,
then interprets results for the stakeholder.
"""

import anthropic

from .context_loader import load_context, load_skills, build_system_prompt
from .executor import get_schema_summary, execute_sql, execute_python


MODEL = "claude-sonnet-4-20250514"
MAX_ITERATIONS = 10

TOOLS = [
    {
        "name": "run_sql",
        "description": (
            "Execute a SQL query against the DuckDB database. "
            "Use standard SQL syntax (DuckDB is PostgreSQL-compatible). "
            "Returns results as a formatted markdown table."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The SQL query to execute",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "run_python",
        "description": (
            "Execute Python code for calculations or data transformations. "
            "pandas (as pd), numpy (as np), and a query() function are available. "
            "Use query('SELECT ...') to run SQL and get a pandas DataFrame. "
            "Print output or assign to a variable named `result`."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "The Python code to execute",
                },
            },
            "required": ["code"],
        },
    },
]


def create_agent(team: str | None = None):
    """Initialize the agent with context for a specific team."""
    client = anthropic.Anthropic()
    context = load_context(team=team)
    skills = load_skills()
    schema_summary = get_schema_summary()
    system_prompt = build_system_prompt(context, skills, schema_summary)

    return Agent(client, system_prompt, team=team)


class Agent:
    def __init__(self, client: anthropic.Anthropic, system_prompt: str, team: str | None = None):
        self.client = client
        self.system_prompt = system_prompt
        self.team = team
        self.conversation: list[dict] = []

    def ask(self, question: str) -> str:
        """
        Send a question to the agent and get a response.
        Handles the tool use loop automatically.
        """
        self.conversation.append({"role": "user", "content": question})

        for _ in range(MAX_ITERATIONS):
            response = self.client.messages.create(
                model=MODEL,
                max_tokens=4096,
                system=self.system_prompt,
                messages=self.conversation,
                tools=TOOLS,
            )

            # If the model is done (no more tool calls), return the text
            if response.stop_reason == "end_turn":
                text_parts = [b.text for b in response.content if b.type == "text"]
                full_text = "\n".join(text_parts)
                self.conversation.append({"role": "assistant", "content": response.content})
                return full_text

            # Process tool calls
            self.conversation.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    if block.name == "run_sql":
                        output = execute_sql(block.input["query"])
                    elif block.name == "run_python":
                        output = execute_python(block.input["code"])
                    else:
                        output = f"Unknown tool: {block.name}"

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": output,
                    })

            self.conversation.append({"role": "user", "content": tool_results})

        # Safety: return whatever we have
        return "Analysis reached maximum iterations. Please try a simpler question."

    def reset(self):
        """Clear conversation history."""
        self.conversation = []
