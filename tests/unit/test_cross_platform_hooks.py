"""Tests for cross-platform hook implementations."""

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest


class TestCapturePromptHook:
    """Tests for the capture_prompt hook."""

    def test_capture_work_tree(self, tmp_path: Path) -> None:
        """Test capture_work_tree creates expected files."""
        from deepwork.hooks.capture_prompt import capture_work_tree

        # Initialize a git repo with signing disabled
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=tmp_path,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=tmp_path,
            capture_output=True,
            check=True,
        )
        # Disable commit signing for this test
        subprocess.run(
            ["git", "config", "commit.gpgsign", "false"],
            cwd=tmp_path,
            capture_output=True,
            check=True,
        )

        # Create a tracked file
        (tmp_path / "test.txt").write_text("hello")
        subprocess.run(["git", "add", "test.txt"], cwd=tmp_path, capture_output=True, check=True)
        subprocess.run(
            ["git", "commit", "-m", "initial", "--no-gpg-sign"],
            cwd=tmp_path,
            capture_output=True,
            check=True,
        )

        # Run capture
        result = capture_work_tree(tmp_path)

        # Verify files were created
        assert result == 0
        assert (tmp_path / ".deepwork" / ".last_head_ref").exists()
        assert (tmp_path / ".deepwork" / ".last_work_tree").exists()

        # Verify content
        work_tree = (tmp_path / ".deepwork" / ".last_work_tree").read_text()
        assert "test.txt" in work_tree


class TestUserPromptSubmitHook:
    """Tests for the user_prompt_submit hook."""

    def test_main_returns_zero(self, tmp_path: Path) -> None:
        """Test main returns 0 even if capture fails."""
        from deepwork.hooks.user_prompt_submit import main

        # Set up environment to use tmp_path
        with patch.dict("os.environ", {"CLAUDE_PROJECT_DIR": str(tmp_path)}):
            # Provide empty JSON input
            with patch("sys.stdin.isatty", return_value=True):
                result = main()

        # Should succeed (returns 0 even on errors to not block prompt)
        assert result == 0


class TestHookCommandFormat:
    """Tests for hook command generation."""

    def test_module_hook_command_is_cross_platform(self, tmp_path: Path) -> None:
        """Test that module hooks generate cross-platform commands."""
        from deepwork.core.hooks_syncer import HookEntry

        entry = HookEntry(
            job_name="test_job",
            job_dir=tmp_path / ".deepwork" / "jobs" / "test_job",
            module="deepwork.hooks.rules_check",
        )

        command = entry.get_command(tmp_path)

        # Should use deepwork CLI, not bash scripts
        assert command == "deepwork hook rules_check"
        assert ".sh" not in command

    def test_script_hook_uses_forward_slashes(self, tmp_path: Path) -> None:
        """Test that script hooks use forward slashes for cross-platform compatibility."""
        from deepwork.core.hooks_syncer import HookEntry

        job_dir = tmp_path / ".deepwork" / "jobs" / "test_job"
        job_dir.mkdir(parents=True)
        (job_dir / "hooks").mkdir()
        (job_dir / "hooks" / "test.sh").write_text("#!/bin/bash\nexit 0")

        entry = HookEntry(
            job_name="test_job",
            job_dir=job_dir,
            script="test.sh",
        )

        command = entry.get_command(tmp_path)

        # Should use forward slashes, even on Windows-style paths
        assert "\\" not in command
        assert "/" in command
