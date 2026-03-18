"""
Context-aware data analysis agent.

Uses Claude's tool use to execute SQL and Python against a DuckDB database,
then interprets results for the stakeholder.
"""

import anthropic
from dataclasses import dataclass, field
from typing import Generator

from .context_loader import load_context, load_skills, build_system_prompt
from .executor import get_schema_summary, execute_sql, execute_python


MODEL = "claude-sonnet-4-20250514"
MAX_ITERATIONS = 10


@dataclass
class AgentResponse:
    """Agent response with text and optional Plotly figures."""
    text: str
    figures: list[str] = field(default_factory=list)  # Plotly figure JSON strings


# Streaming event types
@dataclass
class TextDelta:
    """A chunk of streamed text."""
    text: str

@dataclass
class ToolStart:
    """A tool execution is beginning."""
    tool_name: str
    tool_input: dict

@dataclass
class ToolResult:
    """A tool execution completed."""
    tool_name: str
    output: str
    figures: list[str] = field(default_factory=list)

@dataclass
class StreamComplete:
    """Streaming is complete. Contains the full response."""
    response: AgentResponse


StreamEvent = TextDelta | ToolStart | ToolResult | StreamComplete

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
            "pandas (as pd), numpy (as np), plotly.express (as px), "
            "plotly.graph_objects (as go), and a query() function are available. "
            "Use query('SELECT ...') to run SQL and get a pandas DataFrame. "
            "Print output or assign to a variable named `result`. "
            "To create a chart, build a Plotly figure and assign it to any variable — "
            "it will be rendered automatically."
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

    def ask(self, question: str) -> AgentResponse:
        """
        Send a question to the agent and get a response.
        Handles the tool use loop automatically.
        """
        self.conversation.append({"role": "user", "content": question})
        self._manage_context_window()
        all_figures = []

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
                return AgentResponse(text=full_text, figures=all_figures)

            # Process tool calls
            self.conversation.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    if block.name == "run_sql":
                        output = execute_sql(block.input["query"])
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": output,
                        })
                    elif block.name == "run_python":
                        result = execute_python(block.input["code"])
                        all_figures.extend(result.figures)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result.text,
                        })
                    else:
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": f"Unknown tool: {block.name}",
                        })

            self.conversation.append({"role": "user", "content": tool_results})

        # Safety: return whatever we have
        return AgentResponse(
            text="Analysis reached maximum iterations. Please try a simpler question.",
            figures=all_figures,
        )

    def _manage_context_window(self):
        """Keep conversation history manageable by trimming older messages."""
        max_messages = 20
        if len(self.conversation) > max_messages:
            # Keep a note that history was truncated, then the last max_messages
            self.conversation = [
                {"role": "user", "content": "[Earlier conversation truncated]"},
                {"role": "assistant", "content": "Understood, I'll continue from here."},
            ] + self.conversation[-max_messages:]

    def ask_stream(self, question: str) -> Generator[StreamEvent, None, None]:
        """
        Stream a response to a question, yielding events as they arrive.
        Yields TextDelta, ToolStart, ToolResult, and StreamComplete events.
        """
        self.conversation.append({"role": "user", "content": question})
        self._manage_context_window()
        all_figures = []

        for _ in range(MAX_ITERATIONS):
            # Stream the response
            accumulated_text = ""
            tool_calls = {}  # id -> {name, input_json}
            current_tool_id = None

            with self.client.messages.stream(
                model=MODEL,
                max_tokens=4096,
                system=self.system_prompt,
                messages=self.conversation,
                tools=TOOLS,
            ) as stream:
                for event in stream:
                    if event.type == "content_block_start":
                        if event.content_block.type == "tool_use":
                            current_tool_id = event.content_block.id
                            tool_calls[current_tool_id] = {
                                "name": event.content_block.name,
                                "input_json": "",
                            }
                    elif event.type == "content_block_delta":
                        if event.delta.type == "text_delta":
                            accumulated_text += event.delta.text
                            yield TextDelta(text=event.delta.text)
                        elif event.delta.type == "input_json_delta":
                            if current_tool_id:
                                tool_calls[current_tool_id]["input_json"] += event.delta.partial_json
                    elif event.type == "content_block_stop":
                        current_tool_id = None

                response = stream.get_final_message()

            # If done, yield complete
            if response.stop_reason == "end_turn":
                self.conversation.append({"role": "assistant", "content": response.content})
                yield StreamComplete(
                    response=AgentResponse(text=accumulated_text, figures=all_figures)
                )
                return

            # Process tool calls
            self.conversation.append({"role": "assistant", "content": response.content})
            tool_results = []

            for block in response.content:
                if block.type == "tool_use":
                    if block.name == "run_sql":
                        yield ToolStart(tool_name="run_sql", tool_input=block.input)
                        output = execute_sql(block.input["query"])
                        yield ToolResult(tool_name="run_sql", output=output)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": output,
                        })
                    elif block.name == "run_python":
                        yield ToolStart(tool_name="run_python", tool_input=block.input)
                        result = execute_python(block.input["code"])
                        all_figures.extend(result.figures)
                        yield ToolResult(
                            tool_name="run_python",
                            output=result.text,
                            figures=result.figures,
                        )
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result.text,
                        })
                    else:
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": f"Unknown tool: {block.name}",
                        })

            self.conversation.append({"role": "user", "content": tool_results})

        # Safety fallback
        yield StreamComplete(
            response=AgentResponse(
                text="Analysis reached maximum iterations. Please try a simpler question.",
                figures=all_figures,
            )
        )

    def reset(self):
        """Clear conversation history."""
        self.conversation = []
