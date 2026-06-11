"""Headless UI tests for the hybrid demo via streamlit.testing.AppTest.

These run the real app script with no browser and no API key, which is exactly
the situation a visitor hits if the deployment secret were ever missing —
demo mode must work regardless.
"""

from pathlib import Path

import dotenv
import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).parent.parent / "app" / "streamlit_app.py")


@pytest.fixture()
def no_api_key(monkeypatch):
    """No key in the environment, and .env must not sneak it back in.

    AppTest executes the app script in-process, so patching dotenv here
    affects the app's own `load_dotenv` call.
    """
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(dotenv, "load_dotenv", lambda *a, **k: False)


def test_demo_mode_renders_without_key(no_api_key):
    at = AppTest.from_file(APP, default_timeout=30)
    at.run()

    assert not at.exception, f"App raised: {at.exception}"
    # Demo mode is the default: the recorded-session banner is shown
    infos = " ".join(str(b.value) for b in at.info)
    assert "recordings of real runs" in infos
    # A transcript rendered, labeled with its provenance
    captions = " ".join(str(c.value) for c in at.caption)
    assert "unedited transcript of a real run" in captions


def test_demo_mode_team_switch(no_api_key):
    at = AppTest.from_file(APP, default_timeout=30)
    at.run()
    at.sidebar.selectbox[0].select("Product").run()
    assert not at.exception
    captions = " ".join(str(c.value) for c in at.caption)
    assert "unedited transcript of a real run" in captions


def test_live_mode_without_key_warns(no_api_key):
    at = AppTest.from_file(APP, default_timeout=30)
    at.run()
    at.sidebar.radio[0].set_value("Ask live questions").run()
    assert not at.exception
    warnings = " ".join(str(w.value) for w in at.warning)
    assert "needs an Anthropic API key" in warnings


def test_live_mode_session_cap(monkeypatch):
    """With a key present but the per-visit cap spent, the app stops before
    any agent is created — no API call can happen."""
    monkeypatch.setattr(dotenv, "load_dotenv", lambda *a, **k: False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-not-a-real-key")
    at = AppTest.from_file(APP, default_timeout=30)
    at.session_state["live_questions_asked"] = 3
    at.run()
    at.sidebar.radio[0].set_value("Ask live questions").run()
    assert not at.exception
    infos = " ".join(str(b.value) for b in at.info)
    assert "live questions for this visit" in infos
