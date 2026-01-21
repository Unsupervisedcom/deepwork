"""
================================================================================
                    REQUIREMENTS TESTS - DO NOT MODIFY
================================================================================

These tests verify CRITICAL REQUIREMENTS for the DeepWork install process.
They ensure the install command behaves correctly with respect to:

1. LOCAL vs PROJECT settings isolation
2. Idempotency of project settings

WARNING: These tests represent contractual requirements for the install process.
Modifying these tests may violate user expectations and could cause data loss
or unexpected behavior. If a test fails, fix the IMPLEMENTATION, not the test.

Requirements tested:
  - REQ-001: Install MUST NOT modify local (user home) Claude settings
  - REQ-002: Install MUST be idempotent for project settings

================================================================================
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from deepwork.cli.main import cli

# =============================================================================
# REQ-001: Install MUST NOT modify local (user home) Claude settings
# =============================================================================
#
# Claude Code has two levels of settings:
# - LOCAL settings: ~/.claude/settings.json (user's global settings)
# - PROJECT settings: <project>/.claude/settings.json (project-specific)
#
# DeepWork install MUST ONLY modify project settings and NEVER touch
# the user's local settings, which may contain personal configurations,
# API keys, or other sensitive data.
#
# DO NOT MODIFY THIS TEST - It protects user data integrity.
# =============================================================================


class TestLocalSettingsProtection:
    """
    REQUIREMENTS TEST: Verify install does not modify local Claude settings.

    ============================================================================
    WARNING: DO NOT MODIFY THESE TESTS
    ============================================================================

    These tests verify that the install process respects the boundary between
    project-level and user-level settings. Modifying these tests could result
    in DeepWork overwriting user's personal Claude configurations.
    """

    def test_install_does_not_modify_local_claude_settings(
        self, mock_claude_project: Path, tmp_path: Path
    ) -> None:
        """
        REQ-001: Install MUST NOT modify local (home directory) Claude settings.

        This test creates a mock local settings file and verifies that the
        DeepWork install process does not modify it in any way.

        DO NOT MODIFY THIS TEST.
        """
        # Create a mock local Claude settings directory in tmp_path
        mock_home = tmp_path / "mock_home"
        mock_local_claude_dir = mock_home / ".claude"
        mock_local_claude_dir.mkdir(parents=True)

        # Create local settings with known content
        local_settings_file = mock_local_claude_dir / "settings.json"
        original_local_settings = {
            "user_preference": "do_not_change",
            "api_key_encrypted": "sensitive_data_here",
            "custom_config": {"setting1": True, "setting2": "value"},
        }
        local_settings_file.write_text(json.dumps(original_local_settings, indent=2))

        # Record the original file modification time
        original_mtime = local_settings_file.stat().st_mtime

        # Run install with mocked home directory
        runner = CliRunner()
        with patch.dict("os.environ", {"HOME": str(mock_home)}):
            result = runner.invoke(
                cli,
                ["install", "--platform", "claude", "--path", str(mock_claude_project)],
                catch_exceptions=False,
            )

        # Verify install succeeded
        assert result.exit_code == 0, f"Install failed: {result.output}"

        # CRITICAL: Verify local settings were NOT modified
        assert local_settings_file.exists(), "Local settings file should still exist"

        # Check content is unchanged
        current_local_settings = json.loads(local_settings_file.read_text())
        assert current_local_settings == original_local_settings, (
            "LOCAL SETTINGS WERE MODIFIED! "
            "Install MUST NOT touch user's home directory Claude settings. "
            f"Expected: {original_local_settings}, Got: {current_local_settings}"
        )

        # Check modification time is unchanged
        current_mtime = local_settings_file.stat().st_mtime
        assert current_mtime == original_mtime, (
            "LOCAL SETTINGS FILE WAS TOUCHED! "
            "Install MUST NOT access user's home directory Claude settings."
        )

    def test_install_only_modifies_project_settings(
        self, mock_claude_project: Path, tmp_path: Path
    ) -> None:
        """
        REQ-001 (corollary): Install MUST modify only project-level settings.

        Verifies that the install process correctly modifies project settings
        while leaving local settings untouched.

        DO NOT MODIFY THIS TEST.
        """
        # Create mock local Claude settings
        mock_home = tmp_path / "mock_home"
        mock_local_claude_dir = mock_home / ".claude"
        mock_local_claude_dir.mkdir(parents=True)

        local_settings_file = mock_local_claude_dir / "settings.json"
        original_local_content = '{"local": "unchanged"}'
        local_settings_file.write_text(original_local_content)

        # Record project settings path for later verification
        project_settings_file = mock_claude_project / ".claude" / "settings.json"

        # Run install
        runner = CliRunner()
        with patch.dict("os.environ", {"HOME": str(mock_home)}):
            result = runner.invoke(
                cli,
                ["install", "--platform", "claude", "--path", str(mock_claude_project)],
                catch_exceptions=False,
            )

        assert result.exit_code == 0

        # Verify LOCAL settings unchanged
        assert local_settings_file.read_text() == original_local_content, (
            "Local settings were modified! Install must only modify project settings."
        )

        # Verify PROJECT settings were modified (hooks should be added)
        current_project_content = project_settings_file.read_text()
        project_settings = json.loads(current_project_content)

        # The install should have added hooks to project settings
        assert "hooks" in project_settings, "Project settings should have hooks after install"


# =============================================================================
# REQ-002: Install MUST be idempotent for project settings
# =============================================================================
#
# Running `deepwork install` multiple times on the same project MUST produce
# identical results. The second and subsequent installs should not:
# - Add duplicate entries
# - Modify timestamps unnecessarily
# - Change the structure or content of settings
#
# This ensures that users can safely re-run install without side effects,
# which is important for CI/CD pipelines, onboarding scripts, and
# troubleshooting scenarios.
#
# DO NOT MODIFY THIS TEST - It ensures installation reliability.
# =============================================================================


class TestProjectSettingsIdempotency:
    """
    REQUIREMENTS TEST: Verify install is idempotent for project settings.

    ============================================================================
    WARNING: DO NOT MODIFY THESE TESTS
    ============================================================================

    These tests verify that running install multiple times produces identical
    results. This is critical for:
    - CI/CD reliability
    - Safe re-installation
    - Troubleshooting without side effects
    """

    def test_project_settings_unchanged_on_second_install(self, mock_claude_project: Path) -> None:
        """
        REQ-002: Second install MUST NOT change project settings.

        Running install twice should produce identical settings.json content.
        The first install MUST modify settings (add hooks), and the second
        install should be a no-op for settings.

        DO NOT MODIFY THIS TEST.
        """
        runner = CliRunner()

        # Capture settings BEFORE first install
        settings_file = mock_claude_project / ".claude" / "settings.json"
        settings_before_install = json.loads(settings_file.read_text())

        # First install
        result1 = runner.invoke(
            cli,
            ["install", "--platform", "claude", "--path", str(mock_claude_project)],
            catch_exceptions=False,
        )
        assert result1.exit_code == 0, f"First install failed: {result1.output}"

        # Capture settings after first install
        settings_after_first_install = settings_file.read_text()
        settings_json_first = json.loads(settings_after_first_install)

        # CRITICAL: First install MUST actually modify settings (add hooks)
        # This ensures the test is meaningful - if install does nothing,
        # idempotency would trivially pass but the test would be useless.
        assert "hooks" in settings_json_first, (
            "FIRST INSTALL DID NOT ADD HOOKS! "
            "Install must add hooks to project settings. "
            "This test requires install to actually modify settings to verify idempotency."
        )
        assert settings_json_first != settings_before_install, (
            "FIRST INSTALL DID NOT MODIFY SETTINGS! "
            "Install must modify project settings on first run. "
            "This test requires install to actually do something to verify idempotency."
        )

        # Second install
        result2 = runner.invoke(
            cli,
            ["install", "--platform", "claude", "--path", str(mock_claude_project)],
            catch_exceptions=False,
        )
        assert result2.exit_code == 0, f"Second install failed: {result2.output}"

        # Capture settings after second install
        settings_after_second_install = settings_file.read_text()
        settings_json_second = json.loads(settings_after_second_install)

        # CRITICAL: Settings must be identical after second install
        assert settings_json_first == settings_json_second, (
            "PROJECT SETTINGS CHANGED ON SECOND INSTALL! "
            "Install MUST be idempotent. "
            f"After first: {json.dumps(settings_json_first, indent=2)}\n"
            f"After second: {json.dumps(settings_json_second, indent=2)}"
        )

    def test_no_duplicate_hooks_on_multiple_installs(self, mock_claude_project: Path) -> None:
        """
        REQ-002 (corollary): Multiple installs MUST NOT create duplicate hooks.

        This specifically tests that hooks are not duplicated, which would
        cause performance issues and unexpected behavior.

        DO NOT MODIFY THIS TEST.
        """
        runner = CliRunner()

        # Run install three times
        for i in range(3):
            result = runner.invoke(
                cli,
                ["install", "--platform", "claude", "--path", str(mock_claude_project)],
                catch_exceptions=False,
            )
            assert result.exit_code == 0, f"Install #{i + 1} failed: {result.output}"

        # Load final settings
        settings_file = mock_claude_project / ".claude" / "settings.json"
        settings = json.loads(settings_file.read_text())

        # CRITICAL: Hooks must exist for this test to be meaningful
        assert "hooks" in settings, (
            "NO HOOKS FOUND AFTER INSTALL! "
            "Install must add hooks to project settings. "
            "This test requires hooks to exist to verify no duplicates are created."
        )

        # Verify no duplicate hooks
        for event_name, hooks_list in settings["hooks"].items():
            # Extract all hook commands for duplicate detection
            commands = []
            for hook_entry in hooks_list:
                for hook in hook_entry.get("hooks", []):
                    if "command" in hook:
                        commands.append(hook["command"])

            # Check for duplicates
            unique_commands = set(commands)
            assert len(commands) == len(unique_commands), (
                f"DUPLICATE HOOKS DETECTED for event '{event_name}'! "
                f"Install MUST be idempotent. "
                f"Commands: {commands}"
            )

    def test_third_install_identical_to_first(self, mock_claude_project: Path) -> None:
        """
        REQ-002 (extended): Nth install MUST produce same result as first.

        This tests the general idempotency property across multiple runs.
        The first install MUST modify settings, and all subsequent installs
        MUST produce identical results.

        DO NOT MODIFY THIS TEST.
        """
        runner = CliRunner()

        # Capture settings BEFORE any install
        settings_file = mock_claude_project / ".claude" / "settings.json"
        settings_before = json.loads(settings_file.read_text())

        # First install
        result = runner.invoke(
            cli,
            ["install", "--platform", "claude", "--path", str(mock_claude_project)],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, f"First install failed: {result.output}"

        settings_after_first = json.loads(settings_file.read_text())

        # CRITICAL: First install MUST actually modify settings
        assert "hooks" in settings_after_first, (
            "FIRST INSTALL DID NOT ADD HOOKS! "
            "Install must add hooks to verify idempotency is meaningful."
        )
        assert settings_after_first != settings_before, (
            "FIRST INSTALL DID NOT MODIFY SETTINGS! "
            "Install must modify settings on first run to verify idempotency."
        )

        # Run multiple more installs
        for i in range(5):
            result = runner.invoke(
                cli,
                ["install", "--platform", "claude", "--path", str(mock_claude_project)],
                catch_exceptions=False,
            )
            assert result.exit_code == 0, f"Install #{i + 2} failed: {result.output}"

        # Final state should match first install
        settings_after_many = json.loads(settings_file.read_text())

        assert settings_after_first == settings_after_many, (
            "SETTINGS DIVERGED AFTER MULTIPLE INSTALLS! "
            "Install must be idempotent regardless of how many times it runs."
        )


# =============================================================================
# FIXTURE EXTENSIONS
# =============================================================================
# Additional fixtures needed for these requirement tests


@pytest.fixture
def tmp_path(temp_dir: Path) -> Path:
    """Alias for temp_dir to match pytest naming convention."""
    return temp_dir
