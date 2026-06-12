"""Export everything the web app (web/) needs.

- demo_sessions/*.json -> web/public/data/sessions/ (fetched on demand)
  plus a lightweight manifest at web/src/data/sessions_index.json
- context/stakeholders/*.md + skills/*.md parsed into web/src/data/context.json
- evals/results/*.json + question text from the YAML sets -> web/src/data/quality.json

Transcripts are copied verbatim — they are unedited recordings of real runs.

Usage: .venv/bin/python scripts/export_web_data.py
"""

import json
import re
import shutil
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent
WEB = ROOT / "web"
SESS_OUT = WEB / "public" / "data" / "sessions"
DATA_OUT = WEB / "src" / "data"

GOLD_RESULTS = ROOT / "evals" / "results" / "eval_2026-05-27T18-37-49Z.json"
ADV_RESULTS = ROOT / "evals" / "results" / "eval_2026-05-27T23-41-20Z.json"

TEAM_ORDER = ["Executive", "Marketing", "Sales", "Product"]


def md_sections(path: Path) -> dict[str, str]:
    """Split a markdown file into {heading: body} for '## ' headings."""
    text = path.read_text()
    parts = re.split(r"^## ", text, flags=re.M)
    out = {}
    for part in parts[1:]:
        head, _, body = part.partition("\n")
        out[head.strip()] = body.strip()
    return out


def bullets(block: str) -> list[str]:
    return [ln.lstrip("- ").strip() for ln in block.splitlines() if ln.strip().startswith("- ")]


def numbered(block: str) -> list[str]:
    return [re.sub(r"^\d+\.\s*", "", ln).strip() for ln in block.splitlines() if re.match(r"^\d+\.", ln.strip())]


def main() -> None:
    SESS_OUT.mkdir(parents=True, exist_ok=True)
    DATA_OUT.mkdir(parents=True, exist_ok=True)

    # --- Sessions: copy verbatim + manifest ---
    index = []
    for f in sorted((ROOT / "demo_sessions").glob("*.json")):
        shutil.copy(f, SESS_OUT / f.name)
        s = json.loads(f.read_text())
        index.append({
            "file": f.name,
            "team": s["team"],
            "question": s["question"],
            "n_steps": len(s["steps"]),
            "n_errors": sum(1 for st in s["steps"] if st.get("output") and "Error" in str(st["output"])[:300]),
            "n_figures": len(s["figures"]),
            "elapsed_s": s["elapsed_s"],
            "model": s["model"],
            "recorded_at": s["recorded_at"],
        })
    index.sort(key=lambda r: (TEAM_ORDER.index(r["team"]), r["file"]))
    (DATA_OUT / "sessions_index.json").write_text(json.dumps(index, indent=1))
    print(f"sessions: {len(index)} copied, manifest written")

    # --- Context layer ---
    stakeholders = []
    for team in TEAM_ORDER:
        sec = md_sections(ROOT / "context" / "stakeholders" / f"{team.lower()}.md")
        stakeholders.append({
            "team": team,
            "mission": sec.get("Team Mission", ""),
            "cares_about": bullets(sec.get("What They Care About", "")),
            "communication": bullets(sec.get("Communication Preferences", "")),
            "usage": bullets(sec.get("How They Use Data", "")),
        })
    skills = []
    for f in sorted((ROOT / "skills").glob("*.md")):
        sec = md_sections(f)
        first_line = f.read_text().splitlines()[0]
        skills.append({
            "name": first_line.replace("# Skill:", "").strip(),
            "description": sec.get("Description", ""),
            "when": bullets(sec.get("When to Use", "")),
            "steps": numbered(sec.get("Analysis Steps", "")),
        })
    (DATA_OUT / "context.json").write_text(json.dumps({"stakeholders": stakeholders, "skills": skills}, indent=1))
    print(f"context: {len(stakeholders)} stakeholders, {len(skills)} skills")

    # --- Quality / evals ---
    gold = json.loads(GOLD_RESULTS.read_text())
    adv = json.loads(ADV_RESULTS.read_text())
    gold_qs = {q["id"]: q for q in yaml.safe_load((ROOT / "evals" / "gold.yaml").read_text())["questions"]}
    adv_qs = {q["id"]: q for q in yaml.safe_load((ROOT / "evals" / "adversarial.yaml").read_text())["questions"]}

    quality = {
        "gold": {
            "n": gold["n_questions"],
            "pass": gold["n_pass"],
            "by_category": gold["by_category"],
            "examples": [
                {
                    "id": r["id"],
                    "category": r["category"],
                    "question": gold_qs.get(r["id"], {}).get("question", ""),
                    "expected": r["expected"],
                    "observed": r["observed"],
                    "passed": r["passed"],
                }
                for r in gold["results"]
            ],
        },
        "adversarial": {
            "n": adv["n_questions"],
            "pass": adv["n_pass"],
            "results": [
                {
                    "id": r["id"],
                    "category": r["category"],
                    "question": adv_qs.get(r["id"], {}).get("question", ""),
                    "passed": r["passed"],
                    "judge_reason": r["judge_reason"],
                    "excerpt": (r["response_excerpt"] or "")[:400],
                }
                for r in adv["results"]
            ],
        },
        "gold_recorded_at": gold["timestamp_utc"][:10],
        "adv_recorded_at": adv["timestamp_utc"][:10],
    }
    (DATA_OUT / "quality.json").write_text(json.dumps(quality, indent=1))
    print(f"quality: gold {gold['n_pass']}/{gold['n_questions']}, adversarial {adv['n_pass']}/{adv['n_questions']}")


if __name__ == "__main__":
    main()
