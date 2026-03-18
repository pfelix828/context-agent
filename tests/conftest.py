"""
Shared test fixtures for the context-agent test suite.
"""

import duckdb
import pytest
from pathlib import Path
from unittest.mock import MagicMock


@pytest.fixture
def test_db(tmp_path):
    """Create a small temporary DuckDB database for testing."""
    db_path = tmp_path / "test.duckdb"
    con = duckdb.connect(str(db_path))

    con.execute("""
        CREATE TABLE dim_accounts (
            account_id VARCHAR, company_name VARCHAR, segment VARCHAR,
            is_customer BOOLEAN, arr DOUBLE
        )
    """)
    con.execute("""
        INSERT INTO dim_accounts VALUES
        ('ACC-001', 'Acme Corp', 'Enterprise', true, 120000),
        ('ACC-002', 'Small Co', 'SMB', true, 8000),
        ('ACC-003', 'Mid Inc', 'Mid-Market', false, 0)
    """)

    con.execute("""
        CREATE TABLE dim_leads (
            lead_id VARCHAR, account_id VARCHAR, lead_source VARCHAR,
            status VARCHAR, lead_score INTEGER
        )
    """)
    con.execute("""
        INSERT INTO dim_leads VALUES
        ('LEAD-001', 'ACC-001', 'organic', 'mql', 85),
        ('LEAD-002', 'ACC-002', 'paid_search', 'sql', 92),
        ('LEAD-003', 'ACC-003', 'events', 'new', 45)
    """)

    con.execute("""
        CREATE TABLE fct_campaigns (
            campaign_id VARCHAR, campaign_name VARCHAR, channel VARCHAR,
            budget DOUBLE, spend DOUBLE
        )
    """)
    con.execute("""
        INSERT INTO fct_campaigns VALUES
        ('CAMP-001', 'Google Brand', 'paid_search', 50000, 42000),
        ('CAMP-002', 'Blog Posts', 'organic', 10000, 8500)
    """)

    con.close()
    return db_path


@pytest.fixture
def mock_anthropic_client():
    """Create a mock Anthropic client that returns canned responses."""
    client = MagicMock()

    def make_response(text, stop_reason="end_turn", tool_calls=None):
        """Helper to build a mock API response."""
        response = MagicMock()
        response.stop_reason = stop_reason
        content = []

        if text:
            text_block = MagicMock()
            text_block.type = "text"
            text_block.text = text
            content.append(text_block)

        if tool_calls:
            for tc in tool_calls:
                tool_block = MagicMock()
                tool_block.type = "tool_use"
                tool_block.name = tc["name"]
                tool_block.input = tc["input"]
                tool_block.id = tc.get("id", "tool_001")
                content.append(tool_block)

        response.content = content
        return response

    client._make_response = make_response
    return client


@pytest.fixture
def sample_context():
    """Load real context files from the project."""
    from src.context_loader import load_context, load_skills
    context = load_context(team="Marketing")
    skills = load_skills()
    return context, skills
