"""Tests for deepwork setup (Claude platform). Validates DW-REQ-005.6."""

from __future__ import annotations

import json
from pathlib import Path

import click.testing
import pytest

from deepwork.cli.main import cli
from deepwork.setup.claude import (
    DEEPWORK_DIR_PERMISSIONS,
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-005.6.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_creates_settings(self, claude_home: Path) -> None:
        changes = claude_setup()
        assert len(changes) == 6
        settings = _read_settings(claude_home)

        # marketplace registered
        assert MARKETPLACE_KEY in settings["extraKnownMarketplaces"]
        src = settings["extraKnownMarketplaces"][MARKETPLACE_KEY]["source"]
        assert src["source"] == "github"
        assert src["repo"] == "Unsupervisedcom/deepwork"
        assert settings["extraKnownMarketplaces"][MARKETPLACE_KEY]["autoUpdate"] is True

        # plugin enabled
        assert settings["enabledPlugins"][PLUGIN_KEY] is True

        # MCP permission
        assert MCP_PERMISSION in settings["permissions"]["allow"]

        # .deepwork directory permissions (project-relative via leading slash)
        for perm in DEEPWORK_DIR_PERMISSIONS:
            assert perm in settings["permissions"]["allow"]


class TestClaudeSetupIdempotent:
    """Running setup twice should be a no-op the second time."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-005.6.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_no_changes_on_rerun(self, claude_home: Path) -> None:
        claude_setup()
        changes = claude_setup()
        assert changes == []


class TestClaudeSetupPreservesExisting:
    """Existing settings are preserved when adding DeepWork entries."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-005.6.5).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-005.6.6).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_creates_claude_dir(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        fake_home = tmp_path / "empty"
        fake_home.mkdir()
        monkeypatch.setattr(Path, "home", staticmethod(lambda: fake_home))

        changes = claude_setup()
        assert len(changes) == 6
        assert (fake_home / ".claude" / "settings.json").exists()


class TestSetupCLI:
    """Tests for the setup CLI command itself."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-005.6.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_setup_is_click_command(self) -> None:
        assert "setup" in cli.commands

    # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-005.6.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_detects_claude_code(self, claude_home: Path) -> None:
        runner = click.testing.CliRunner()
        result = runner.invoke(cli, ["setup"])
        assert result.exit_code == 0
        assert "Claude Code" in result.output

    # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-005.6.7).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_no_platform_detected(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        fake_home = tmp_path / "noclaudehere"
        fake_home.mkdir()
        monkeypatch.setattr(Path, "home", staticmethod(lambda: fake_home))
        runner = click.testing.CliRunner()
        result = runner.invoke(cli, ["setup"])
        assert result.exit_code == 0
        assert "No supported" in result.output
