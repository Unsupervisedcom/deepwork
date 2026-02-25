"""Tests for deprecated install/sync CLI commands -- validates DW-REQ-005.5.

SCHEDULED REMOVAL: June 1st, 2026; details in PR https://github.com/Unsupervisedcom/deepwork/pull/227
Delete this entire file when DW-REQ-005.5 and the install/sync commands are removed.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from click.testing import CliRunner

from deepwork.cli.install import install, sync
from deepwork.cli.main import cli


class TestInstallCommandOutput:
    """Tests for the install command's deprecation message."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-005.5.8).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_install_prints_deprecation_message(self, tmp_path: Path) -> None:
        """install must print a deprecation message with uninstall instructions."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(install)

        assert result.exit_code == 0
        assert "no longer installed" in result.output.lower()
        assert "brew uninstall deepwork" in result.output
        assert "uv tool uninstall deepwork" in result.output

    # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-005.5.8).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_sync_prints_deprecation_message(self, tmp_path: Path) -> None:
        """sync must print the same deprecation message as install."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(sync)

        assert result.exit_code == 0
        assert "brew uninstall deepwork" in result.output
        assert "uv tool uninstall deepwork" in result.output

    # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-005.5.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_install_and_sync_produce_identical_output(self, tmp_path: Path) -> None:
        """Both commands must execute the same shared implementation."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            install_result = runner.invoke(install)
        with runner.isolated_filesystem(temp_dir=tmp_path):
            sync_result = runner.invoke(sync)

        assert install_result.output == sync_result.output


class TestInstallHiddenFromHelp:
    """Tests that install and sync are hidden from CLI help."""

    @staticmethod
    def _get_command_names_from_help(output: str) -> list[str]:
        """Parse CLI --help output and return the list of visible command names."""
        command_lines = []
        in_commands = False
        for line in output.splitlines():
            if line.strip().lower().startswith("commands:"):
                in_commands = True
                continue
            if in_commands and line.strip():
                command_lines.append(line)
        return [line.split()[0] for line in command_lines if line.strip()]

    # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-005.5.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_install_not_in_help(self) -> None:
        """install must not appear in --help output."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        command_names = self._get_command_names_from_help(result.output)
        assert "install" not in command_names

    # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-005.5.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_sync_not_in_help(self) -> None:
        """sync must not appear in --help output."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        command_names = self._get_command_names_from_help(result.output)
        assert "sync" not in command_names

    # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-005.5.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_install_still_invocable(self, tmp_path: Path) -> None:
        """Hidden commands must still be invocable directly."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["install"])

        assert result.exit_code == 0

    # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-005.5.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_sync_still_invocable(self, tmp_path: Path) -> None:
        """Hidden commands must still be invocable directly."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["sync"])

        assert result.exit_code == 0


class TestPluginConfigCreation:
    """Tests for auto-installing plugin config into .claude/settings.json."""

    @staticmethod
    def _read_settings() -> dict[str, Any]:
        """Read .claude/settings.json relative to CWD."""
        result: dict[str, Any] = json.loads(Path(".claude/settings.json").read_text())
        return result

    # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-005.5.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_creates_settings_file_from_scratch(self, tmp_path: Path) -> None:
        """install must create .claude/settings.json when it does not exist."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(install)
            assert result.exit_code == 0
            settings = self._read_settings()

        assert "extraKnownMarketplaces" in settings
        assert "enabledPlugins" in settings

    # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-005.5.5).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_marketplace_entry_is_correct(self, tmp_path: Path) -> None:
        """extraKnownMarketplaces must contain deepwork-plugins with correct source."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(install)
            settings = self._read_settings()

        mp = settings["extraKnownMarketplaces"]["deepwork-plugins"]
        assert mp == {
            "source": {
                "source": "github",
                "repo": "Unsupervisedcom/deepwork",
            }
        }

    # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-005.5.6).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_enabled_plugins_are_correct(self, tmp_path: Path) -> None:
        """enabledPlugins must include both deepwork and learning-agents plugins."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(install)
            settings = self._read_settings()

        assert settings["enabledPlugins"]["deepwork@deepwork-plugins"] is True
        assert settings["enabledPlugins"]["learning-agents@deepwork-plugins"] is True

    # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-005.5.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_merges_with_existing_settings(self, tmp_path: Path) -> None:
        """install must preserve existing keys in settings.json."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            Path(".claude").mkdir()
            existing = {
                "permissions": {"allow": ["Bash(git:*)"]},
                "enabledPlugins": {},
            }
            Path(".claude/settings.json").write_text(json.dumps(existing))

            runner.invoke(install)
            settings = self._read_settings()

        # Original permissions must still be present
        assert settings["permissions"] == {"allow": ["Bash(git:*)"]}
        # New plugin config must be added
        assert "deepwork-plugins" in settings["extraKnownMarketplaces"]
        assert settings["enabledPlugins"]["deepwork@deepwork-plugins"] is True

    # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-005.5.7).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_handles_invalid_json_gracefully(self, tmp_path: Path) -> None:
        """install must not crash if settings.json contains invalid JSON."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            Path(".claude").mkdir()
            Path(".claude/settings.json").write_text("{invalid json!!")

            result = runner.invoke(install)
            assert result.exit_code == 0
            settings = self._read_settings()

        assert "extraKnownMarketplaces" in settings
        assert "enabledPlugins" in settings

    # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-005.5.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_creates_claude_directory_if_missing(self, tmp_path: Path) -> None:
        """install must create the .claude/ directory if it does not exist."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            assert not Path(".claude").exists()
            result = runner.invoke(install)
            assert result.exit_code == 0
            assert Path(".claude/settings.json").exists()
