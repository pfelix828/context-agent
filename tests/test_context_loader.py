"""
Tests for the context loader and system prompt builder.
"""

import pytest

from src.context_loader import (
    list_teams, load_context, load_skills, build_system_prompt, load_file,
    CONTEXT_DIR, STAKEHOLDERS_DIR, SKILLS_DIR,
)


class TestListTeams:
    def test_returns_known_teams(self):
        teams = list_teams()
        assert "Marketing" in teams
        assert "Sales" in teams
        assert "Product" in teams
        assert "Executive" in teams

    def test_returns_sorted(self):
        teams = list_teams()
        assert teams == sorted(teams)


class TestLoadContext:
    def test_loads_base_context(self):
        context = load_context()
        assert "agent" in context
        assert "domain" in context
        assert "data_dictionary" in context

    def test_loads_team_context(self):
        context = load_context(team="Marketing")
        assert "stakeholder" in context
        assert "Marketing" in context["stakeholder"]

    def test_no_team_no_stakeholder(self):
        context = load_context()
        assert "stakeholder" not in context

    def test_invalid_team(self):
        context = load_context(team="Nonexistent")
        assert "stakeholder" not in context

    def test_skips_old_stakeholder_file(self):
        # The old stakeholder.md should not be loaded as a key
        context = load_context()
        # It should not appear as its own key (it's skipped in the loader)
        assert "stakeholder" not in context


class TestLoadSkills:
    def test_loads_skills(self):
        skills = load_skills()
        assert len(skills) >= 4
        assert "funnel_analysis" in skills
        assert "campaign_roi" in skills
        assert "revenue_analysis" in skills
        assert "cohort_retention" in skills

    def test_skill_content(self):
        skills = load_skills()
        assert "When to Use" in skills["funnel_analysis"]


class TestBuildSystemPrompt:
    def test_prompt_structure(self):
        context = load_context(team="Marketing")
        skills = load_skills()
        prompt = build_system_prompt(context, skills, "- dim_accounts (3 rows)")

        assert "Agent Instructions" in prompt or "Role" in prompt
        assert "Marketing" in prompt
        assert "Domain Knowledge" in prompt or "Business Context" in prompt
        assert "dim_accounts" in prompt
        assert "run_sql" in prompt or "SQL" in prompt

    def test_prompt_includes_skills(self):
        context = load_context(team="Sales")
        skills = load_skills()
        prompt = build_system_prompt(context, skills, "")
        assert "Analysis Skills" in prompt
        assert "Funnel Analysis" in prompt or "funnel" in prompt.lower()

    def test_prompt_includes_schema(self):
        context = load_context()
        prompt = build_system_prompt(context, {}, "- test_table (100 rows)")
        assert "test_table" in prompt
        assert "Live Database Schema" in prompt

    def test_prompt_includes_visualization_guidance(self):
        context = load_context(team="Marketing")
        prompt = build_system_prompt(context, {}, "")
        assert "Visualization" in prompt or "chart" in prompt.lower()
