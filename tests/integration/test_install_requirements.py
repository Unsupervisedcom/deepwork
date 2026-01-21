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
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from deepwork.cli.main import cli

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
# These helpers reduce repetition while keeping individual tests readable.
# The helpers themselves are simple and should not mask test intent.


def run_install(project_path: Path) -> None:
    """Run deepwork install for Claude on the given project path.

    Raises AssertionError if install fails.
    """
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["install", "--platform", "claude", "--path", str(project_path)],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, f"Install failed: {result.output}"


def get_project_settings(project_path: Path) -> dict:
    """Read and parse the project's Claude settings.json."""
    settings_file = project_path / ".claude" / "settings.json"
    return json.loads(settings_file.read_text())


def assert_install_added_hooks(settings_before: dict, settings_after: dict) -> None:
    """Assert that install actually modified settings by adding hooks.

    This ensures idempotency tests are meaningful - if install does nothing,
    idempotency would trivially pass but the test would be useless.
    """
    assert "hooks" in settings_after, (
        "FIRST INSTALL DID NOT ADD HOOKS! "
        "Install must add hooks to project settings. "
        "This test requires install to actually modify settings to verify idempotency."
    )
    assert settings_after != settings_before, (
        "FIRST INSTALL DID NOT MODIFY SETTINGS! "
        "Install must modify project settings on first run. "
        "This test requires install to actually do something to verify idempotency."
    )


@contextmanager
def mock_local_claude_settings(
    tmp_path: Path, content: str | dict = '{"local": "unchanged"}'
) -> Iterator[Path]:
    """Create mock local Claude settings and patch HOME to use them.

    Args:
        tmp_path: Temporary directory to create mock home in
        content: Settings content (string or dict to be JSON-serialized)

    Yields:
        Path to the local settings file (for verification after install)
    """
    mock_home = tmp_path / "mock_home"
    mock_local_claude_dir = mock_home / ".claude"
    mock_local_claude_dir.mkdir(parents=True)

    local_settings_file = mock_local_claude_dir / "settings.json"
    if isinstance(content, dict):
        local_settings_file.write_text(json.dumps(content, indent=2))
    else:
        local_settings_file.write_text(content)

    with patch.dict("os.environ", {"HOME": str(mock_home)}):
        yield local_settings_file


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
        original_local_settings = {
            "user_preference": "do_not_change",
            "api_key_encrypted": "sensitive_data_here",
            "custom_config": {"setting1": True, "setting2": "value"},
        }

        with mock_local_claude_settings(tmp_path, original_local_settings) as local_file:
            original_mtime = local_file.stat().st_mtime
            run_install(mock_claude_project)

            # CRITICAL: Verify local settings were NOT modified
            assert local_file.exists(), "Local settings file should still exist"

            current_local_settings = json.loads(local_file.read_text())
            assert current_local_settings == original_local_settings, (
                "LOCAL SETTINGS WERE MODIFIED! "
                "Install MUST NOT touch user's home directory Claude settings. "
                f"Expected: {original_local_settings}, Got: {current_local_settings}"
            )

            assert local_file.stat().st_mtime == original_mtime, (
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
        original_local_content = '{"local": "unchanged"}'

        with mock_local_claude_settings(tmp_path, original_local_content) as local_file:
            run_install(mock_claude_project)

            # Verify LOCAL settings unchanged
            assert local_file.read_text() == original_local_content, (
                "Local settings were modified! Install must only modify project settings."
            )

            # Verify PROJECT settings were modified (hooks should be added)
            project_settings = get_project_settings(mock_claude_project)
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
        # Capture settings BEFORE first install
        settings_before = get_project_settings(mock_claude_project)

        # First install
        run_install(mock_claude_project)
        settings_after_first = get_project_settings(mock_claude_project)

        # CRITICAL: First install MUST actually modify settings
        assert_install_added_hooks(settings_before, settings_after_first)

        # Second install
        run_install(mock_claude_project)
        settings_after_second = get_project_settings(mock_claude_project)

        # CRITICAL: Settings must be identical after second install
        assert settings_after_first == settings_after_second, (
            "PROJECT SETTINGS CHANGED ON SECOND INSTALL! "
            "Install MUST be idempotent. "
            f"After first: {json.dumps(settings_after_first, indent=2)}\n"
            f"After second: {json.dumps(settings_after_second, indent=2)}"
        )

    def test_no_duplicate_hooks_on_multiple_installs(self, mock_claude_project: Path) -> None:
        """
        REQ-002 (corollary): Multiple installs MUST NOT create duplicate hooks.

        This specifically tests that hooks are not duplicated, which would
        cause performance issues and unexpected behavior.

        DO NOT MODIFY THIS TEST.
        """
        # Run install three times
        for _ in range(3):
            run_install(mock_claude_project)

        # Load final settings
        settings = get_project_settings(mock_claude_project)

        # CRITICAL: Hooks must exist for this test to be meaningful
        assert "hooks" in settings, (
            "NO HOOKS FOUND AFTER INSTALL! "
            "Install must add hooks to project settings. "
            "This test requires hooks to exist to verify no duplicates are created."
        )

        # Verify no duplicate hooks
        for event_name, hooks_list in settings["hooks"].items():
            # Extract all hook commands for duplicate detection
            commands = [
                hook["command"]
                for hook_entry in hooks_list
                for hook in hook_entry.get("hooks", [])
                if "command" in hook
            ]

            # Check for duplicates
            assert len(commands) == len(set(commands)), (
                f"DUPLICATE HOOKS DETECTED for event '{event_name}'! "
                f"Install MUST be idempotent. Commands: {commands}"
            )

    def test_third_install_identical_to_first(self, mock_claude_project: Path) -> None:
        """
        REQ-002 (extended): Nth install MUST produce same result as first.

        This tests the general idempotency property across multiple runs.
        The first install MUST modify settings, and all subsequent installs
        MUST produce identical results.

        DO NOT MODIFY THIS TEST.
        """
        # Capture settings BEFORE any install
        settings_before = get_project_settings(mock_claude_project)

        # First install
        run_install(mock_claude_project)
        settings_after_first = get_project_settings(mock_claude_project)

        # CRITICAL: First install MUST actually modify settings
        assert_install_added_hooks(settings_before, settings_after_first)

        # Run multiple more installs
        for _ in range(5):
            run_install(mock_claude_project)

        # Final state should match first install
        settings_after_many = get_project_settings(mock_claude_project)

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
