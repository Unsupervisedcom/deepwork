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
) -> tuple[str, str, int]:
    """
    Run check_version.sh with a mocked claude command.

    Args:
        script_path: Path to check_version.sh
        mock_version: Version string to return from mock claude, or None for failure
        cwd: Working directory

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
        """Test that warning suggests running /update."""
        stdout, stderr, code = run_check_version_with_mock_claude(check_version_script, "2.0.0")

        assert "/update" in stderr

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
