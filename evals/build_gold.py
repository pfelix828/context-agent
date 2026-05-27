"""
Populate `expected_answer` for every question in evals/gold.yaml by running
its reference SQL against the live DuckDB at data/gtm.duckdb.

Each reference SQL is expected to return exactly one row and one column.
The value is written back to gold.yaml in place, so the gold answers stay
in sync if the data generator is re-run.

Usage:
    python evals/build_gold.py            # write back to gold.yaml
    python evals/build_gold.py --dry-run  # print results, don't write
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import duckdb
import yaml

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "gtm.duckdb"
GOLD_PATH = ROOT / "evals" / "gold.yaml"


def run_one(con: duckdb.DuckDBPyConnection, sql: str):
    df = con.execute(sql).fetchdf()
    if df.shape != (1, 1):
        raise ValueError(
            f"reference SQL must return exactly one row and one column "
            f"(got shape {df.shape}):\n{sql}"
        )
    value = df.iat[0, 0]
    if hasattr(value, "item"):
        value = value.item()
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="print results without modifying gold.yaml")
    args = parser.parse_args()

    if not DB_PATH.exists():
        print(f"DB not found at {DB_PATH}. Run `python src/generate_data.py` first.",
              file=sys.stderr)
        return 1

    with open(GOLD_PATH) as f:
        gold = yaml.safe_load(f)

    con = duckdb.connect(str(DB_PATH), read_only=True)
    failures = []

    for q in gold["questions"]:
        try:
            value = run_one(con, q["reference_sql"])
        except Exception as e:
            failures.append((q["id"], str(e)))
            print(f"[FAIL] {q['id']}: {e}")
            continue

        q["expected_answer"] = value
        print(f"[ok]   {q['id']:35s} = {value}")

    con.close()

    if failures:
        print(f"\n{len(failures)} reference SQL(s) failed; aborting write.", file=sys.stderr)
        return 1

    if args.dry_run:
        print("\n--dry-run: gold.yaml unchanged.")
        return 0

    with open(GOLD_PATH, "w") as f:
        yaml.safe_dump(gold, f, sort_keys=False, allow_unicode=True, width=100)

    print(f"\nWrote {len(gold['questions'])} expected_answer values to {GOLD_PATH}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
