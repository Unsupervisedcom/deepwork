"""Tests for deepwork setup (Claude platform)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from deepwork.setup.claude import (
    MARKETPLACE_KEY,
    MCP_PERMISSION,
    PLUGIN_KEY,
    claude_setup,
)


@pytest.fixture()
def claude_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a fake ~/.claude directory and patch Path.home()."""
    fake_home = tmp_path / "fakehome"
    fake_home.mkdir()
    (fake_home / ".claude").mkdir()
    monkeypatch.setattr(Path, "home", staticmethod(lambda: fake_home))
    return fake_home


def _read_settings(claude_home: Path) -> dict:
    return json.loads((claude_home / ".claude" / "settings.json").read_text())


class TestClaudeSetupFreshFile:
    """When settings.json does not exist yet."""

    def test_creates_settings(self, claude_home: Path) -> None:
        changes = claude_setup()
        assert len(changes) == 3
        settings = _read_settings(claude_home)

        # marketplace registered
        assert MARKETPLACE_KEY in settings["extraKnownMarketplaces"]
        src = settings["extraKnownMarketplaces"][MARKETPLACE_KEY]["source"]
        assert src["source"] == "github"
        assert src["repo"] == "Unsupervisedcom/deepwork"

        # plugin enabled
        assert settings["enabledPlugins"][PLUGIN_KEY] is True

        # MCP permission
        assert MCP_PERMISSION in settings["permissions"]["allow"]


class TestClaudeSetupIdempotent:
    """Running setup twice should be a no-op the second time."""

    def test_no_changes_on_rerun(self, claude_home: Path) -> None:
        claude_setup()
        changes = claude_setup()
        assert changes == []


class TestClaudeSetupPreservesExisting:
    """Existing settings are preserved when adding DeepWork entries."""

    def test_existing_allow_rules_kept(self, claude_home: Path) -> None:
        settings_path = claude_home / ".claude" / "settings.json"
        existing = {
            "permissions": {"allow": ["Bash(git:*)"]},
            "enabledPlugins": {"other@marketplace": True},
        }
        settings_path.write_text(json.dumps(existing))

        claude_setup()
        settings = _read_settings(claude_home)

        assert "Bash(git:*)" in settings["permissions"]["allow"]
        assert settings["enabledPlugins"]["other@marketplace"] is True


class TestClaudeSetupNoClaudeDir:
    """When ~/.claude does not exist, setup creates it."""

    def test_creates_claude_dir(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        fake_home = tmp_path / "empty"
        fake_home.mkdir()
        monkeypatch.setattr(Path, "home", staticmethod(lambda: fake_home))

        changes = claude_setup()
        assert len(changes) == 3
        assert (fake_home / ".claude" / "settings.json").exists()
