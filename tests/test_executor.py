"""
Tests for the SQL and Python execution engine.
"""

import pytest
from unittest.mock import patch

from src.executor import (
    execute_sql, execute_python, get_schema_summary,
    ExecutionResult, _safe_import, DB_PATH,
)


# --- SQL Execution ---

class TestExecuteSQL:
    def test_valid_query(self, test_db):
        with patch("src.executor.DB_PATH", test_db):
            result = execute_sql("SELECT company_name, segment FROM dim_accounts ORDER BY company_name")
        assert "Acme Corp" in result
        assert "Enterprise" in result

    def test_empty_result(self, test_db):
        with patch("src.executor.DB_PATH", test_db):
            result = execute_sql("SELECT * FROM dim_accounts WHERE segment = 'Nonexistent'")
        assert result == "Query returned no results."

    def test_sql_error(self, test_db):
        with patch("src.executor.DB_PATH", test_db):
            result = execute_sql("SELECT * FROM nonexistent_table")
        assert "SQL Error" in result

    def test_read_only(self, test_db):
        with patch("src.executor.DB_PATH", test_db):
            result = execute_sql("DROP TABLE dim_accounts")
        assert "SQL Error" in result


# --- Python Execution ---

class TestExecutePython:
    def test_stdout_capture(self, test_db):
        with patch("src.executor.DB_PATH", test_db):
            result = execute_python("print('hello world')")
        assert isinstance(result, ExecutionResult)
        assert result.text == "hello world\n"
        assert result.figures == []

    def test_result_variable(self, test_db):
        with patch("src.executor.DB_PATH", test_db):
            result = execute_python("result = 42")
        assert "42" in result.text

    def test_dataframe_result(self, test_db):
        with patch("src.executor.DB_PATH", test_db):
            result = execute_python("result = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})")
        assert "a" in result.text
        assert "b" in result.text

    def test_query_helper(self, test_db):
        with patch("src.executor.DB_PATH", test_db):
            result = execute_python("df = query('SELECT COUNT(*) as n FROM dim_accounts')\nprint(df['n'].iloc[0])")
        assert "3" in result.text

    def test_safe_import_allowed(self, test_db):
        with patch("src.executor.DB_PATH", test_db):
            result = execute_python("import math\nprint(math.pi)")
        assert "3.14" in result.text

    def test_blocked_import(self, test_db):
        with patch("src.executor.DB_PATH", test_db):
            result = execute_python("import os")
        assert "Python Error" in result.text
        assert "not allowed" in result.text

    def test_no_open(self, test_db):
        with patch("src.executor.DB_PATH", test_db):
            result = execute_python("f = open('/etc/passwd')")
        assert "Python Error" in result.text

    def test_plotly_figure_capture(self, test_db):
        with patch("src.executor.DB_PATH", test_db):
            code = """
import plotly.express as px
df = pd.DataFrame({'x': [1, 2, 3], 'y': [4, 5, 6]})
fig = px.line(df, x='x', y='y', title='Test Chart')
"""
            result = execute_python(code)
        assert isinstance(result, ExecutionResult)
        assert len(result.figures) == 1
        assert "Test Chart" in result.figures[0]

    def test_no_output(self, test_db):
        with patch("src.executor.DB_PATH", test_db):
            result = execute_python("x = 1 + 1")
        assert result.text == "Code executed successfully (no output)."


# --- Schema Summary ---

class TestGetSchemaSummary:
    def test_returns_table_info(self, test_db):
        with patch("src.executor.DB_PATH", test_db):
            summary = get_schema_summary()
        assert "dim_accounts" in summary
        assert "dim_leads" in summary
        assert "rows" in summary


# --- Safe Import ---

class TestSafeImport:
    def test_allowed_modules(self):
        for mod in ["math", "statistics", "datetime", "json", "re"]:
            result = _safe_import(mod)
            assert result is not None

    def test_blocked_modules(self):
        for mod in ["os", "subprocess", "sys", "shutil"]:
            with pytest.raises(ImportError, match="not allowed"):
                _safe_import(mod)

    def test_plotly_allowed(self):
        result = _safe_import("plotly")
        assert result is not None
