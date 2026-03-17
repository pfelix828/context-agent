"""
Executes SQL and Python code against the DuckDB database.

Parses code blocks from the agent's response, runs them,
and returns results as formatted strings.
"""

import re
import io
import duckdb
import pandas as pd
from pathlib import Path
from contextlib import redirect_stdout


DB_PATH = Path(__file__).parent.parent / "data" / "gtm.duckdb"


def get_connection() -> duckdb.DuckDBPyConnection:
    """Get a read-only DuckDB connection."""
    return duckdb.connect(str(DB_PATH), read_only=True)


def get_schema_summary() -> str:
    """Get a summary of all tables and their row counts from the live database."""
    con = get_connection()
    tables = con.execute("SHOW TABLES").fetchall()
    lines = []
    for (table,) in tables:
        count = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        cols = con.execute(f"DESCRIBE {table}").fetchall()
        col_list = ", ".join(f"{c[0]} ({c[1]})" for c in cols)
        lines.append(f"- **{table}** ({count:,} rows): {col_list}")
    con.close()
    return "\n".join(lines)


def extract_code_blocks(text: str) -> list[dict]:
    """
    Extract executable code blocks from the agent's response.
    Looks for ```sql [EXECUTE] or ```python [EXECUTE] blocks.
    """
    pattern = r"```(sql|python)\s*\[EXECUTE\]\s*\n(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
    return [{"language": lang.lower(), "code": code.strip()} for lang, code in matches]


def execute_sql(query: str) -> str:
    """Execute a SQL query and return results as a formatted string."""
    con = get_connection()
    try:
        result = con.execute(query)
        df = result.fetchdf()
        if df.empty:
            return "Query returned no results."
        return df.to_markdown(index=False)
    except Exception as e:
        return f"SQL Error: {e}"
    finally:
        con.close()


def _query_via_duckdb(query: str) -> pd.DataFrame:
    """Helper for Python code to query DuckDB and get a DataFrame."""
    con = get_connection()
    try:
        return con.execute(query).fetchdf()
    finally:
        con.close()


def execute_python(code: str) -> str:
    """
    Execute Python code with pandas and duckdb available.
    Captures printed output and the last expression's value.
    Uses a safe helper function instead of raw DuckDB connections
    to avoid fork issues in Streamlit's threaded environment.
    """
    import numpy as np

    local_vars = {
        "pd": pd,
        "np": np,
        "query": _query_via_duckdb,
    }

    # Use a restricted builtins to prevent subprocess/os access
    safe_builtins = {k: v for k, v in __builtins__.__dict__.items()
                     if k not in ("__import__", "exec", "eval", "compile", "open")}
    safe_builtins["__import__"] = _safe_import

    stdout = io.StringIO()
    try:
        with redirect_stdout(stdout):
            exec(code, {"__builtins__": safe_builtins}, local_vars)
        output = stdout.getvalue()
        if not output and "result" in local_vars:
            result = local_vars["result"]
            if isinstance(result, pd.DataFrame):
                output = result.to_markdown(index=False)
            else:
                output = str(result)
        return output if output else "Code executed successfully (no output)."
    except Exception as e:
        return f"Python Error: {e}"


def _safe_import(name, *args, **kwargs):
    """Only allow importing safe data analysis packages."""
    allowed = {"math", "statistics", "collections", "itertools", "functools",
               "datetime", "json", "re", "decimal", "fractions"}
    if name in allowed:
        return __import__(name, *args, **kwargs)
    raise ImportError(f"Import of '{name}' is not allowed. Use pd, np, or query() instead.")


def run_code_blocks(blocks: list[dict]) -> list[dict]:
    """Execute a list of code blocks and return results."""
    results = []
    for block in blocks:
        if block["language"] == "sql":
            output = execute_sql(block["code"])
        elif block["language"] == "python":
            output = execute_python(block["code"])
        else:
            output = f"Unsupported language: {block['language']}"

        results.append({
            "language": block["language"],
            "code": block["code"],
            "output": output,
        })
    return results
