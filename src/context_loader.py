"""
Loads context files and skills from the project directory.

Reads stakeholder profiles, domain knowledge, data dictionaries,
agent instructions, and analysis skills to build the system prompt
for the agent.
"""

from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent
CONTEXT_DIR = PROJECT_ROOT / "context"
STAKEHOLDERS_DIR = CONTEXT_DIR / "stakeholders"
SKILLS_DIR = PROJECT_ROOT / "skills"


def load_file(path: Path) -> str:
    """Read a file and return its contents."""
    if path.exists():
        return path.read_text().strip()
    return ""


def list_teams() -> list[str]:
    """Return available team names from the stakeholders directory."""
    if not STAKEHOLDERS_DIR.exists():
        return []
    return sorted(f.stem.title() for f in STAKEHOLDERS_DIR.glob("*.md"))


def load_context(team: str | None = None) -> dict[str, str]:
    """Load all context files into a dictionary, using team-specific stakeholder."""
    context = {}
    for file in sorted(CONTEXT_DIR.glob("*.md")):
        # Skip the old single stakeholder.md — we use team profiles now
        if file.stem == "stakeholder":
            continue
        context[file.stem] = load_file(file)

    # Load team-specific stakeholder profile
    if team:
        team_file = STAKEHOLDERS_DIR / f"{team.lower()}.md"
        if team_file.exists():
            context["stakeholder"] = load_file(team_file)

    return context


def load_skills() -> dict[str, str]:
    """Load all skill definitions."""
    skills = {}
    for file in sorted(SKILLS_DIR.glob("*.md")):
        skills[file.stem] = load_file(file)
    return skills


def build_system_prompt(context: dict[str, str], skills: dict[str, str], schema_summary: str) -> str:
    """
    Assemble the full system prompt from context files, skills, and live schema.
    """
    sections = []

    # Agent instructions come first — they set tone and behavior
    if "agent" in context:
        sections.append(context["agent"])

    # Stakeholder profile
    if "stakeholder" in context:
        sections.append(context["stakeholder"])

    # Domain knowledge
    if "domain" in context:
        sections.append(context["domain"])

    # Data dictionary
    if "data_dictionary" in context:
        sections.append(context["data_dictionary"])

    # Live schema from the database
    if schema_summary:
        sections.append(f"# Live Database Schema\n\n{schema_summary}")

    # Skills
    if skills:
        skill_text = "# Available Analysis Skills\n\n"
        skill_text += "You have the following pre-built analysis frameworks. "
        skill_text += "Use them when the user's question matches a skill's trigger. "
        skill_text += "Follow the analysis steps and output format defined in the skill.\n"
        for name, content in skills.items():
            skill_text += f"\n---\n\n{content}"
        sections.append(skill_text)

    # Execution instructions
    sections.append("""# How to Answer Questions

When the user asks a question about the data:

1. **Think** about which tables and columns are needed
2. Use the `run_sql` tool to query the database
3. If you need calculations or transformations, use `run_python`
4. **Interpret** the results for the stakeholder following the agent instructions
5. You can run multiple queries if needed to build a complete picture

Always use the metric definitions from the domain knowledge. Never invent metrics.

SQL rules:
- Use DuckDB SQL syntax (very close to PostgreSQL)
- Always include column aliases for clarity
- Limit results to what's needed — don't SELECT * from large tables
- Use CTEs for complex queries to keep them readable""")

    return "\n\n---\n\n".join(sections)
