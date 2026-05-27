"""
Run the Adaptive Analyst Agent against one or both evaluation sets.

Sets:
  gold        — 20 well-specified questions with reference SQL and
                deterministic numeric scoring (evals/gold.yaml)
  adversarial — 12 questions designed to surface failure modes
                (hallucination, ambiguity, SQL traps, leading questions).
                Scored by an LLM judge against PASS/FAIL criteria, plus a
                deterministic numeric check when applicable
                (evals/adversarial.yaml)

A question with both numeric and judge checks passes only if both pass.

Cost note: each agent call runs Claude Sonnet with tool use; each judge
call runs Claude Haiku. Use --limit / --ids to scope down.

Usage:
    python evals/run_eval.py                       # both sets
    python evals/run_eval.py --set gold
    python evals/run_eval.py --set adversarial
    python evals/run_eval.py --set adversarial --limit 3
    python evals/run_eval.py --ids q_open_opp_count,q_churn_rate
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import anthropic
import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from src.agent import create_agent  # noqa: E402
from evals.judge import judge_response, Verdict  # noqa: E402


GOLD_PATH = ROOT / "evals" / "gold.yaml"
ADVERSARIAL_PATH = ROOT / "evals" / "adversarial.yaml"
RESULTS_DIR = ROOT / "evals" / "results"

ANSWER_RE = re.compile(r"<answer>\s*([^<]+?)\s*</answer>", re.IGNORECASE)
NUMERIC_RE = re.compile(r"-?\d[\d,]*\.?\d*")

NUMERIC_SUFFIX = (
    "\n\nWhen you have your final answer, wrap the single numeric value in "
    "<answer>VALUE</answer> tags with no units, commas, or extra characters. "
    "Example: <answer>123.45</answer>."
)


@dataclass
class Result:
    id: str
    set_name: str
    category: str
    passed: bool
    expected: float | int | None = None
    observed: float | int | None = None
    raw_answer_tag: str | None = None
    numeric_passed: bool | None = None
    judge_passed: bool | None = None
    judge_reason: str | None = None
    response_excerpt: str = ""
    error: str | None = None
    latency_s: float = 0.0


def parse_number(text: str) -> float | None:
    if text is None:
        return None
    cleaned = text.replace("$", "").replace(",", "").strip()
    m = NUMERIC_RE.search(cleaned)
    if not m:
        return None
    try:
        return float(m.group(0).replace(",", ""))
    except ValueError:
        return None


def extract_answer(response_text: str) -> tuple[str | None, float | None]:
    m = ANSWER_RE.search(response_text)
    if not m:
        return None, None
    return m.group(1), parse_number(m.group(1))


def within_tolerance(expected, observed, tol: dict) -> bool:
    if expected is None or observed is None:
        return False
    t = tol.get("type")
    if t == "exact":
        try:
            return int(expected) == int(observed)
        except (TypeError, ValueError):
            return expected == observed
    if t == "abs":
        return abs(float(observed) - float(expected)) <= float(tol["value"])
    if t == "rel":
        denom = abs(float(expected))
        if denom == 0:
            return abs(float(observed) - float(expected)) <= float(tol["value"])
        return abs(float(observed) - float(expected)) / denom <= float(tol["value"])
    raise ValueError(f"unknown tolerance type: {t}")


def run_one(question: dict, set_name: str,
            judge_client: anthropic.Anthropic | None) -> Result:
    has_numeric = "expected_answer" in question and question["expected_answer"] is not None
    has_judge = "judge_criteria" in question and question["judge_criteria"]

    agent = create_agent(team=None)
    prompt = question["question"].rstrip()
    if has_numeric:
        prompt += NUMERIC_SUFFIX

    r = Result(
        id=question["id"],
        set_name=set_name,
        category=question["category"],
        passed=False,
        expected=question.get("expected_answer"),
    )

    start = time.monotonic()
    try:
        response = agent.ask(prompt)
    except Exception as e:
        r.latency_s = time.monotonic() - start
        r.error = f"{type(e).__name__}: {e}"
        return r
    r.latency_s = time.monotonic() - start
    r.response_excerpt = response.text[:500]

    numeric_ok = None
    if has_numeric:
        raw, observed = extract_answer(response.text)
        r.raw_answer_tag = raw
        r.observed = observed
        numeric_ok = within_tolerance(question["expected_answer"], observed,
                                       question["tolerance"])
        r.numeric_passed = numeric_ok
        if observed is None and not has_judge:
            r.error = "no <answer> tag found or value not numeric"

    judge_ok = None
    if has_judge:
        if judge_client is None:
            r.error = (r.error or "") + " (judge unavailable)"
            judge_ok = False
        else:
            try:
                verdict: Verdict = judge_response(
                    judge_client,
                    question["question"],
                    question["judge_criteria"],
                    response.text,
                )
                judge_ok = verdict.passed
                r.judge_passed = verdict.passed
                r.judge_reason = verdict.reason
            except Exception as e:
                r.judge_passed = False
                r.judge_reason = f"judge error: {type(e).__name__}: {e}"
                judge_ok = False

    checks = [c for c in (numeric_ok, judge_ok) if c is not None]
    r.passed = all(checks) if checks else False
    return r


def load_questions(set_name: str, ids: set[str] | None,
                   limit: int | None) -> list[tuple[str, dict]]:
    """Return list of (set_name, question_dict) tuples."""
    paths: list[tuple[str, Path]] = []
    if set_name in ("gold", "all"):
        paths.append(("gold", GOLD_PATH))
    if set_name in ("adversarial", "all"):
        paths.append(("adversarial", ADVERSARIAL_PATH))

    items: list[tuple[str, dict]] = []
    for name, p in paths:
        if not p.exists():
            print(f"warning: {p} not found, skipping {name}", file=sys.stderr)
            continue
        with open(p) as f:
            data = yaml.safe_load(f)
        questions = data["questions"]
        if ids:
            questions = [q for q in questions if q["id"] in ids]
        if limit:
            questions = questions[:limit]
        for q in questions:
            items.append((name, q))
    return items


def print_summary(results: list[Result]) -> None:
    by_set: dict[str, list[Result]] = {}
    for r in results:
        by_set.setdefault(r.set_name, []).append(r)

    print()
    print("=" * 64)
    for set_name in ("gold", "adversarial"):
        rs = by_set.get(set_name)
        if not rs:
            continue
        n_pass = sum(1 for r in rs if r.passed)
        print(f"{set_name.upper():12s}  {n_pass}/{len(rs)}  "
              f"({100.0 * n_pass / len(rs):.1f}%)")
        # category breakdown
        by_cat: dict[str, list[Result]] = {}
        for r in rs:
            by_cat.setdefault(r.category, []).append(r)
        for cat, crs in sorted(by_cat.items()):
            p = sum(1 for r in crs if r.passed)
            print(f"  {cat:25s}  {p}/{len(crs)}")
        print()

    total_pass = sum(1 for r in results if r.passed)
    total_latency = sum(r.latency_s for r in results)
    print(f"OVERALL       {total_pass}/{len(results)}  "
          f"({100.0 * total_pass / len(results):.1f}%)")
    print(f"Total latency: {total_latency:.1f}s  "
          f"(avg {total_latency / len(results):.1f}s per question)")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--set", dest="set_name",
                        choices=("gold", "adversarial", "all"),
                        default="all",
                        help="which evaluation set to run (default: all)")
    parser.add_argument("--limit", type=int, default=None,
                        help="cap the first N questions per set")
    parser.add_argument("--ids", type=str, default=None,
                        help="comma-separated question IDs to run")
    parser.add_argument("--out", type=str, default=None,
                        help="path to write JSON results")
    args = parser.parse_args()

    ids = {s.strip() for s in args.ids.split(",")} if args.ids else None
    items = load_questions(args.set_name, ids, args.limit)
    if not items:
        print("no questions selected.", file=sys.stderr)
        return 1

    needs_judge = any("judge_criteria" in q and q["judge_criteria"]
                      for _, q in items)
    judge_client = anthropic.Anthropic() if needs_judge else None

    print(f"running {len(items)} question(s) "
          f"({sum(1 for s, _ in items if s == 'gold')} gold, "
          f"{sum(1 for s, _ in items if s == 'adversarial')} adversarial)\n")

    results: list[Result] = []
    for i, (set_name, q) in enumerate(items, 1):
        print(f"[{i:2d}/{len(items)}] [{set_name[:3]}] {q['id']:32s}",
              end="  ", flush=True)
        r = run_one(q, set_name, judge_client)
        results.append(r)
        status = "PASS" if r.passed else "FAIL"
        bits = []
        if r.numeric_passed is not None:
            bits.append(f"num={'P' if r.numeric_passed else 'F'} "
                        f"obs={r.observed}")
        if r.judge_passed is not None:
            bits.append(f"judge={'P' if r.judge_passed else 'F'}")
        print(f"{status:4s}  {'  '.join(bits)}  ({r.latency_s:.1f}s)")
        if r.judge_reason and not r.judge_passed:
            print(f"        judge: {r.judge_reason}")
        if r.error:
            print(f"        ! {r.error}")

    print_summary(results)

    out_path = (Path(args.out) if args.out
                else RESULTS_DIR /
                f"eval_{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H-%M-%SZ')}.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "set_name": args.set_name,
        "n_questions": len(results),
        "n_pass": sum(1 for r in results if r.passed),
        "pass_rate": sum(1 for r in results if r.passed) / len(results),
        "total_latency_s": sum(r.latency_s for r in results),
        "by_set": {
            s: {
                "n": sum(1 for r in results if r.set_name == s),
                "pass": sum(1 for r in results if r.set_name == s and r.passed),
            }
            for s in {r.set_name for r in results}
        },
        "results": [asdict(r) for r in results],
    }
    with open(out_path, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"\nResults written to {out_path}")

    return 0 if all(r.passed for r in results) else 2


if __name__ == "__main__":
    sys.exit(main())
