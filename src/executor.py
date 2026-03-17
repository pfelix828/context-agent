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


def execute_python(code: str) -> str:
    """
    Execute Python code with pandas and duckdb available.
    Captures printed output and the last expression's value.
    """
    con = get_connection()
    local_vars = {
        "pd": pd,
        "duckdb": duckdb,
        "con": con,
    }

    stdout = io.StringIO()
    try:
        with redirect_stdout(stdout):
            exec(code, {"__builtins__": __builtins__}, local_vars)
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
    finally:
        con.close()


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
