"""Tests for check_version.sh SessionStart hook.

Tests version checking logic, JSON output format, and warning behavior.
"""

import os
import subprocess
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def check_version_script(hooks_dir: Path) -> Path:
    """Return path to check_version.sh."""
    return hooks_dir / "check_version.sh"


def run_check_version_with_mock_claude(
    script_path: Path,
    mock_version: str | None,
    cwd: Path | None = None,
    mock_deepwork: bool = True,
) -> tuple[str, str, int]:
    """
    Run check_version.sh with a mocked claude command.

    Args:
        script_path: Path to check_version.sh
        mock_version: Version string to return from mock claude, or None for failure
        cwd: Working directory
        mock_deepwork: If True, create a mock deepwork command that succeeds.
                       If False, do not create mock deepwork (simulates not installed).

    Returns:
        Tuple of (stdout, stderr, return_code)
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create mock claude command
        mock_claude = Path(tmpdir) / "claude"
        if mock_version is not None:
            mock_claude.write_text(f'#!/bin/bash\necho "{mock_version} (Claude Code)"\n')
        else:
            mock_claude.write_text("#!/bin/bash\nexit 1\n")
        mock_claude.chmod(0o755)

        # Create mock deepwork command
        # When mock_deepwork=True, create a working mock
        # When mock_deepwork=False, create a failing mock that shadows the real one
        mock_deepwork_cmd = Path(tmpdir) / "deepwork"
        if mock_deepwork:
            mock_deepwork_cmd.write_text('#!/bin/bash\necho "deepwork 0.1.0"\n')
        else:
            # Create a mock that fails (simulating deepwork not being installed)
            mock_deepwork_cmd.write_text("#!/bin/bash\nexit 127\n")
        mock_deepwork_cmd.chmod(0o755)

        # Prepend mock dir to PATH
        env = os.environ.copy()
        env["PATH"] = f"{tmpdir}:{env.get('PATH', '')}"

        result = subprocess.run(
            ["bash", str(script_path)],
            capture_output=True,
            text=True,
            cwd=cwd or tmpdir,
            env=env,
        )

        return result.stdout, result.stderr, result.returncode


class TestVersionComparison:
    """Tests for version comparison logic."""

    def test_equal_versions(self, check_version_script: Path) -> None:
        """Test that equal versions don't trigger warning."""
        # Mock version equals minimum (2.1.14)
        stdout, stderr, code = run_check_version_with_mock_claude(check_version_script, "2.1.14")

        assert code == 0
        assert "WARNING" not in stderr

    def test_greater_patch_version(self, check_version_script: Path) -> None:
        """Test that greater patch version doesn't trigger warning."""
        stdout, stderr, code = run_check_version_with_mock_claude(check_version_script, "2.1.15")

        assert code == 0
        assert "WARNING" not in stderr

    def test_greater_minor_version(self, check_version_script: Path) -> None:
        """Test that greater minor version doesn't trigger warning."""
        stdout, stderr, code = run_check_version_with_mock_claude(check_version_script, "2.2.0")

        assert code == 0
        assert "WARNING" not in stderr

    def test_greater_major_version(self, check_version_script: Path) -> None:
        """Test that greater major version doesn't trigger warning."""
        stdout, stderr, code = run_check_version_with_mock_claude(check_version_script, "3.0.0")

        assert code == 0
        assert "WARNING" not in stderr

    def test_lesser_patch_version(self, check_version_script: Path) -> None:
        """Test that lesser patch version triggers warning."""
        stdout, stderr, code = run_check_version_with_mock_claude(check_version_script, "2.1.13")

        assert code == 0
        assert "WARNING" in stderr
        assert "2.1.13" in stderr  # Shows current version

    def test_lesser_minor_version(self, check_version_script: Path) -> None:
        """Test that lesser minor version triggers warning."""
        stdout, stderr, code = run_check_version_with_mock_claude(check_version_script, "2.0.99")

        assert code == 0
        assert "WARNING" in stderr

    def test_lesser_major_version(self, check_version_script: Path) -> None:
        """Test that lesser major version triggers warning."""
        stdout, stderr, code = run_check_version_with_mock_claude(check_version_script, "1.9.99")

        assert code == 0
        assert "WARNING" in stderr


class TestWarningOutput:
    """Tests for warning message content."""

    def test_warning_contains_current_version(self, check_version_script: Path) -> None:
        """Test that warning shows the current version."""
        stdout, stderr, code = run_check_version_with_mock_claude(check_version_script, "2.0.0")

        assert "2.0.0" in stderr

    def test_warning_contains_minimum_version(self, check_version_script: Path) -> None:
        """Test that warning shows the minimum version."""
        stdout, stderr, code = run_check_version_with_mock_claude(check_version_script, "2.0.0")

        assert "2.1.14" in stderr

    def test_warning_suggests_update(self, check_version_script: Path) -> None:
        """Test that warning suggests updating Claude Code."""
        stdout, stderr, code = run_check_version_with_mock_claude(check_version_script, "2.0.0")

        assert "Update your version of Claude Code" in stderr

    def test_warning_mentions_bugs(self, check_version_script: Path) -> None:
        """Test that warning mentions bugs in older versions."""
        stdout, stderr, code = run_check_version_with_mock_claude(check_version_script, "2.0.0")

        assert "bugs" in stderr.lower()


class TestHookConformance:
    """Tests for Claude Code hook format compliance."""

    def test_always_exits_zero(self, check_version_script: Path) -> None:
        """Test that script always exits 0 (informational only)."""
        # Test with warning
        stdout, stderr, code = run_check_version_with_mock_claude(check_version_script, "2.0.0")
        assert code == 0

        # Test without warning
        stdout, stderr, code = run_check_version_with_mock_claude(check_version_script, "3.0.0")
        assert code == 0

    def test_outputs_valid_json_when_version_ok(self, check_version_script: Path) -> None:
        """Test that stdout is valid JSON when version is OK."""
        import json

        stdout, stderr, code = run_check_version_with_mock_claude(check_version_script, "3.0.0")

        # Should output empty JSON object
        output = json.loads(stdout.strip())
        assert output == {}

    def test_outputs_structured_json_when_version_low(self, check_version_script: Path) -> None:
        """Test that stdout has hookSpecificOutput when version is low."""
        import json

        stdout, stderr, code = run_check_version_with_mock_claude(check_version_script, "2.0.0")

        output = json.loads(stdout.strip())
        assert "hookSpecificOutput" in output
        assert output["hookSpecificOutput"]["hookEventName"] == "SessionStart"
        assert "additionalContext" in output["hookSpecificOutput"]
        assert "VERSION WARNING" in output["hookSpecificOutput"]["additionalContext"]

    def test_warning_goes_to_stderr_and_stdout(self, check_version_script: Path) -> None:
        """Test that warning is on stderr (visual) and stdout (context)."""
        stdout, stderr, code = run_check_version_with_mock_claude(check_version_script, "2.0.0")

        # Visual warning should be in stderr
        assert "WARNING" in stderr
        # JSON with context should be in stdout
        assert "hookSpecificOutput" in stdout


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_claude_command_not_found(self, check_version_script: Path) -> None:
        """Test graceful handling when claude command fails."""
        stdout, stderr, code = run_check_version_with_mock_claude(
            check_version_script,
            None,  # Mock failure
        )

        # Should exit 0 and output JSON even if version check fails
        assert code == 0
        assert stdout.strip() == "{}"
        # No warning since we couldn't determine version
        assert "WARNING" not in stderr

    def test_version_with_extra_text(self, check_version_script: Path) -> None:
        """Test parsing version from output with extra text."""
        # Real output format: "2.1.1 (Claude Code)"
        stdout, stderr, code = run_check_version_with_mock_claude(check_version_script, "2.1.14")

        assert code == 0
        # Version 2.1.14 equals minimum, no warning
        assert "WARNING" not in stderr


class TestDeepworkInstallationCheck:
    """Tests for deepwork installation check (blocking)."""

    def test_deepwork_installed_allows_session(self, check_version_script: Path) -> None:
        """Test that script proceeds when deepwork is installed."""
        # With mock_deepwork=True (default), deepwork is available
        stdout, stderr, code = run_check_version_with_mock_claude(
            check_version_script, "3.0.0", mock_deepwork=True
        )

        assert code == 0
        assert "DEEPWORK NOT INSTALLED" not in stderr

    def test_deepwork_not_installed_blocks_session(self, check_version_script: Path) -> None:
        """Test that script blocks when deepwork is not installed."""
        stdout, stderr, code = run_check_version_with_mock_claude(
            check_version_script, "3.0.0", mock_deepwork=False
        )

        # Should exit with code 2 (blocking error)
        assert code == 2
        assert "DEEPWORK NOT INSTALLED" in stderr

    def test_deepwork_error_message_content(self, check_version_script: Path) -> None:
        """Test that deepwork error message has helpful content."""
        stdout, stderr, code = run_check_version_with_mock_claude(
            check_version_script, "3.0.0", mock_deepwork=False
        )

        # Should mention direct invocation requirement
        assert "directly invok" in stderr.lower()
        # Should mention NOT using wrappers
        assert "uv run deepwork" in stderr
        # Should suggest installation options
        assert "pipx" in stderr or "pip install" in stderr

    def test_deepwork_error_outputs_json(self, check_version_script: Path) -> None:
        """Test that deepwork error outputs valid JSON with error info."""
        import json

        stdout, stderr, code = run_check_version_with_mock_claude(
            check_version_script, "3.0.0", mock_deepwork=False
        )

        output = json.loads(stdout.strip())
        assert "hookSpecificOutput" in output
        assert "error" in output
        assert "deepwork" in output["error"].lower()
        # Should have additional context for Claude
        assert "additionalContext" in output["hookSpecificOutput"]
        assert "DEEPWORK" in output["hookSpecificOutput"]["additionalContext"]

    def test_deepwork_check_happens_before_version_check(self, check_version_script: Path) -> None:
        """Test that deepwork check runs before version check."""
        # Even with a low version that would trigger warning,
        # missing deepwork should block first
        stdout, stderr, code = run_check_version_with_mock_claude(
            check_version_script, "1.0.0", mock_deepwork=False
        )

        # Should exit with deepwork error, not version warning
        assert code == 2
        assert "DEEPWORK NOT INSTALLED" in stderr
        # Should NOT show version warning
        assert "CLAUDE CODE VERSION WARNING" not in stderr
