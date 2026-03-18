"""
Tests for the context-aware agent (mocked API calls).
"""

import pytest
from unittest.mock import MagicMock, patch

from src.agent import Agent, AgentResponse, MAX_ITERATIONS


class TestAgent:
    def _make_agent(self, client):
        return Agent(client=client, system_prompt="You are a test agent.", team="Marketing")

    def test_simple_response(self, mock_anthropic_client):
        """Agent returns text for a simple question."""
        response = mock_anthropic_client._make_response("The answer is 42.")
        mock_anthropic_client.messages.create.return_value = response

        agent = self._make_agent(mock_anthropic_client)
        result = agent.ask("What is the answer?")

        assert isinstance(result, AgentResponse)
        assert "42" in result.text
        assert result.figures == []

    def test_sql_tool_use(self, mock_anthropic_client, test_db):
        """Agent uses run_sql tool and returns final text."""
        # First call: agent wants to run SQL
        tool_response = mock_anthropic_client._make_response(
            text="Let me query the data.",
            stop_reason="tool_use",
            tool_calls=[{"name": "run_sql", "input": {"query": "SELECT COUNT(*) as n FROM dim_accounts"}, "id": "sql_1"}],
        )
        # Second call: agent interprets results
        final_response = mock_anthropic_client._make_response("There are 3 accounts.")

        mock_anthropic_client.messages.create.side_effect = [tool_response, final_response]

        agent = self._make_agent(mock_anthropic_client)
        with patch("src.agent.execute_sql", return_value="| n |\n|---|\n| 3 |"):
            result = agent.ask("How many accounts?")

        assert "3 accounts" in result.text

    def test_python_tool_use(self, mock_anthropic_client):
        """Agent uses run_python tool."""
        from src.executor import ExecutionResult

        tool_response = mock_anthropic_client._make_response(
            text="Let me calculate.",
            stop_reason="tool_use",
            tool_calls=[{"name": "run_python", "input": {"code": "print(2+2)"}, "id": "py_1"}],
        )
        final_response = mock_anthropic_client._make_response("The result is 4.")

        mock_anthropic_client.messages.create.side_effect = [tool_response, final_response]

        agent = self._make_agent(mock_anthropic_client)
        with patch("src.agent.execute_python", return_value=ExecutionResult(text="4\n", figures=[])):
            result = agent.ask("What is 2+2?")

        assert "4" in result.text

    def test_python_with_figures(self, mock_anthropic_client):
        """Agent captures Plotly figures from Python execution."""
        from src.executor import ExecutionResult

        tool_response = mock_anthropic_client._make_response(
            text="Creating a chart.",
            stop_reason="tool_use",
            tool_calls=[{"name": "run_python", "input": {"code": "fig = px.line(...)"}, "id": "py_1"}],
        )
        final_response = mock_anthropic_client._make_response("Here's the chart.")

        mock_anthropic_client.messages.create.side_effect = [tool_response, final_response]

        agent = self._make_agent(mock_anthropic_client)
        fake_fig_json = '{"data": [], "layout": {"title": "Test"}}'
        with patch("src.agent.execute_python", return_value=ExecutionResult(text="", figures=[fake_fig_json])):
            result = agent.ask("Show me a chart")

        assert len(result.figures) == 1
        assert "Test" in result.figures[0]

    def test_multi_iteration(self, mock_anthropic_client):
        """Agent handles multiple tool call iterations."""
        from src.executor import ExecutionResult

        # Iteration 1: SQL
        sql_response = mock_anthropic_client._make_response(
            text="",
            stop_reason="tool_use",
            tool_calls=[{"name": "run_sql", "input": {"query": "SELECT 1"}, "id": "sql_1"}],
        )
        # Iteration 2: Python
        py_response = mock_anthropic_client._make_response(
            text="",
            stop_reason="tool_use",
            tool_calls=[{"name": "run_python", "input": {"code": "print(1)"}, "id": "py_1"}],
        )
        # Iteration 3: Final answer
        final_response = mock_anthropic_client._make_response("Done with analysis.")

        mock_anthropic_client.messages.create.side_effect = [sql_response, py_response, final_response]

        agent = self._make_agent(mock_anthropic_client)
        with patch("src.agent.execute_sql", return_value="| 1 |\n|---|\n| 1 |"), \
             patch("src.agent.execute_python", return_value=ExecutionResult(text="1\n")):
            result = agent.ask("Complex question")

        assert "Done with analysis" in result.text

    def test_max_iterations(self, mock_anthropic_client):
        """Agent stops after MAX_ITERATIONS."""
        # Always return tool use, never end_turn
        tool_response = mock_anthropic_client._make_response(
            text="",
            stop_reason="tool_use",
            tool_calls=[{"name": "run_sql", "input": {"query": "SELECT 1"}, "id": "sql_1"}],
        )
        mock_anthropic_client.messages.create.return_value = tool_response

        agent = self._make_agent(mock_anthropic_client)
        with patch("src.agent.execute_sql", return_value="1"):
            result = agent.ask("Infinite loop question")

        assert "maximum iterations" in result.text.lower()
        assert mock_anthropic_client.messages.create.call_count == MAX_ITERATIONS

    def test_conversation_history(self, mock_anthropic_client):
        """Agent maintains conversation history across calls."""
        response1 = mock_anthropic_client._make_response("First answer.")
        response2 = mock_anthropic_client._make_response("Second answer.")
        mock_anthropic_client.messages.create.side_effect = [response1, response2]

        agent = self._make_agent(mock_anthropic_client)
        agent.ask("First question")
        agent.ask("Second question")

        assert len(agent.conversation) == 4  # 2 user + 2 assistant

    def test_reset(self, mock_anthropic_client):
        """Agent resets conversation history."""
        response = mock_anthropic_client._make_response("Answer.")
        mock_anthropic_client.messages.create.return_value = response

        agent = self._make_agent(mock_anthropic_client)
        agent.ask("Question")
        assert len(agent.conversation) > 0

        agent.reset()
        assert len(agent.conversation) == 0

    def test_context_window_management(self, mock_anthropic_client):
        """Agent trims conversation when it exceeds 20 messages."""
        response = mock_anthropic_client._make_response("Answer.")
        mock_anthropic_client.messages.create.return_value = response

        agent = self._make_agent(mock_anthropic_client)
        # Fill up conversation beyond limit
        for i in range(15):
            agent.conversation.append({"role": "user", "content": f"Q{i}"})
            agent.conversation.append({"role": "assistant", "content": f"A{i}"})

        assert len(agent.conversation) == 30
        agent.ask("New question")
        # Should have been trimmed: 2 (truncation note) + 20 (kept) + 2 (new Q&A)
        assert len(agent.conversation) <= 26


class TestCreateAgent:
    @patch("src.agent.anthropic.Anthropic")
    @patch("src.agent.get_schema_summary", return_value="- test (1 row)")
    def test_factory_function(self, mock_schema, mock_client_cls):
        from src.agent import create_agent
        agent = create_agent(team="Marketing")
        assert agent.team == "Marketing"
        assert "Marketing" in agent.system_prompt
