# Evaluation Harness

Two evaluation sets that score the Adaptive Analyst Agent on
complementary dimensions: numerical correctness on well-specified
questions, and behavioral quality on intentionally hard ones.

## Why this exists

"Chat with your data" agents demo well but rarely show whether they get
answers right. The gold set gives a defensible correctness number; the
adversarial set surfaces the failure modes a demo never reveals
(hallucination, ambiguity, SQL traps, leading questions). Both run from
one command and produce a single results JSON per run.

## Files

```
evals/
├── gold.yaml          # 20 well-specified questions with reference SQL
├── adversarial.yaml   # 12 questions designed to surface failure modes
├── build_gold.py      # populates expected_answer fields from the live DB
├── judge.py           # LLM judge (Haiku) for qualitative PASS/FAIL scoring
├── run_eval.py        # runs questions through the agent and scores them
├── results/           # timestamped JSON results, one per run
└── README.md
```

## How to run

```bash
# Refresh gold expected answers from the live DB (do this whenever the
# data generator is re-run).
python evals/build_gold.py

# Run both sets (default)
python evals/run_eval.py

# One set only
python evals/run_eval.py --set gold
python evals/run_eval.py --set adversarial

# Scope down while iterating
python evals/run_eval.py --limit 3
python evals/run_eval.py --ids q_open_opp_count,q_churn_rate
```

Results are printed to stdout and written as JSON to `evals/results/`.

## Gold set — deterministic numeric scoring

Each gold question is sent to the agent with a suffix asking it to wrap
its final numeric answer in `<answer>VALUE</answer>` tags. The runner
extracts that value and compares against the expected answer using a
tolerance declared in `gold.yaml`:

| Tolerance type | Definition                                                   | Used for                           |
|----------------|--------------------------------------------------------------|------------------------------------|
| `exact`        | integer match                                                | counts, top-N counts               |
| `abs`          | `\|observed - expected\| <= value` (percentage points)       | rates between 0 and 100            |
| `rel`          | `\|observed - expected\| / \|expected\| <= value`            | dollar amounts, large means        |

If no `<answer>` tag is found, or the contents are not numeric, the
question fails with `error: "no <answer> tag found or value not numeric"`.

## Adversarial set — LLM-judged behaviors

Each adversarial question has a `judge_criteria` block describing what
PASS and FAIL look like. The agent's full response (no `<answer>` suffix
unless the question also has a numeric expected answer) is sent to a
Haiku judge along with the criteria. The judge returns `PASS` or `FAIL`
on the first line and a one-line reason on the second.

Categories:

| Category                 | Tests whether the agent…                                  |
|--------------------------|-----------------------------------------------------------|
| `hallucination_refusal`  | …refuses to invent metrics that aren't in the schema     |
| `ambiguous_metric`       | …surfaces ambiguity or states its assumption explicitly  |
| `sql_trap`               | …avoids an obvious-but-wrong SQL pattern                 |
| `distinct_count`         | …deduplicates correctly across a many-to-many bridge     |
| `cross_table_math`       | …joins multiple tables and does the date math right      |
| `date_boundary`          | …picks and states a date convention for ambiguous spans  |
| `leading_question`       | …verifies a premise instead of accepting it on faith     |

For questions that also carry an `expected_answer`, both the numeric
check and the judge verdict must pass.

## How to read failures

Each result records the agent's response excerpt, numeric verdict (if
applicable), judge verdict, and judge reason. Common patterns:

- **Hallucinated proxy.** Agent computes a number from unrelated columns
  and presents it as the requested metric, sometimes adding a footnote
  caveat. The judge fails this when the criteria require an upfront
  refusal.
- **No methodology shown.** Agent gets the right number but never says
  which query it ran. Strict judges fail this even when the number is
  correct.
- **Premise accepted.** Agent dives into analysis of a false premise
  ("Why is Technology our top industry?") instead of verifying it.
- **Wrong SQL.** Numeric check fails; the response excerpt usually
  reveals which join or filter went wrong.

## Limitations

- **Judge calibration noise.** A strict judge sometimes fails responses
  that produced the right number but didn't show methodology, or that
  added a caveat in a footnote instead of upfront. A second judge model
  or a multi-judge ensemble would tighten this. For now, the run logs
  the judge's reason so you can spot-check borderline calls.
- **Gold tolerances are conservative.** `rel: 0.001` would catch rounding
  drift but mostly add noise; the current settings flag real arithmetic
  mistakes without false alarms.
- **Stakeholder adaptation is not scored.** Whether the marketing answer
  meaningfully differs from the exec answer remains a manual review.
- **Each run costs Claude API spend.** Sonnet (agent) + Haiku (judge);
  use `--limit` or `--ids` when iterating.
