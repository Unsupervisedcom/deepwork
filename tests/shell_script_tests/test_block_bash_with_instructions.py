"""Tests for block_bash_with_instructions.sh hook.

This hook blocks specific Bash commands (e.g., git commit) and provides
alternative instructions via stderr when exit code 2 is returned.

Hook Contract (PreToolUse with exit code 2):
  - Exit code 0: Allow the command
  - Exit code 2: Block the command, stderr message shown to Claude
  - stderr: Contains the instruction message when blocking

See: https://docs.anthropic.com/en/docs/claude-code/hooks
"""

import json
import os
import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def block_bash_hook_path() -> Path:
    """Return the path to the block_bash_with_instructions.sh script."""
    return (
        Path(__file__).parent.parent.parent
        / ".claude"
        / "hooks"
        / "block_bash_with_instructions.sh"
    )


def run_block_bash_hook(
    script_path: Path,
    tool_name: str,
    command: str,
) -> tuple[str, str, int]:
    """
    Run the block_bash_with_instructions.sh hook with simulated input.

    Args:
        script_path: Path to the hook script
        tool_name: The tool name (e.g., "Bash")
        command: The bash command being executed

    Returns:
        Tuple of (stdout, stderr, return_code)
    """
    hook_input = {
        "session_id": "test123",
        "hook_event_name": "PreToolUse",
        "tool_name": tool_name,
        "tool_input": {
            "command": command,
        },
    }

    result = subprocess.run(
        ["bash", str(script_path)],
        capture_output=True,
        text=True,
        input=json.dumps(hook_input),
        env=os.environ.copy(),
    )

    return result.stdout, result.stderr, result.returncode


class TestBlockBashHookExists:
    """Tests that the hook script exists and is properly configured."""

    def test_script_exists(self, block_bash_hook_path: Path) -> None:
        """Test that the hook script exists."""
        assert block_bash_hook_path.exists(), "block_bash_with_instructions.sh should exist"

    def test_script_is_executable(self, block_bash_hook_path: Path) -> None:
        """Test that the hook script is executable."""
        assert os.access(block_bash_hook_path, os.X_OK), (
            "block_bash_with_instructions.sh should be executable"
        )


class TestGitCommitBlocking:
    """Tests for git commit command blocking."""

    @pytest.mark.parametrize(
        "command",
        [
            "git commit -m 'message'",
            "git commit --amend",
            "git commit -a -m 'message'",
            "git  commit -m 'message'",  # Extra space
            "git commit --allow-empty -m 'test'",
            "  git commit -m 'with leading space'",
        ],
    )
    def test_blocks_git_commit_variants(self, block_bash_hook_path: Path, command: str) -> None:
        """Test that git commit variants are blocked with exit code 2."""
        stdout, stderr, code = run_block_bash_hook(block_bash_hook_path, "Bash", command)
        assert code == 2, f"Should block '{command}' with exit code 2, got {code}"
        assert "/commit" in stderr, f"Should mention /commit skill in stderr: {stderr}"

    def test_stderr_contains_instructions(self, block_bash_hook_path: Path) -> None:
        """Test that blocking message contains helpful instructions."""
        stdout, stderr, code = run_block_bash_hook(
            block_bash_hook_path, "Bash", "git commit -m 'test'"
        )
        assert code == 2
        assert "/commit" in stderr, "Should mention the /commit skill"
        assert "skill" in stderr.lower() or "workflow" in stderr.lower(), (
            "Should explain the alternative workflow"
        )


class TestAllowedCommands:
    """Tests for commands that should be allowed."""

    @pytest.mark.parametrize(
        "command",
        [
            # Git commands (non-commit)
            "git status",
            "git add .",
            "git diff HEAD",
            "git log --oneline -5",
            "git push origin main",
            "git pull",
            "git fetch",
            "git branch -a",
            # Non-git commands
            "ls -la",
            "echo hello",
            "python --version",
            "cat README.md",
            # Commands with 'commit' substring (not at start)
            "echo 'commit message'",
            "grep -r 'commit' .",
            "cat commits.txt",
            # 'git commit' in message body (anchored pattern should allow)
            "echo 'use git commit to save changes'",
            "grep 'git commit' README.md",
            ".claude/hooks/commit_job_git_commit.sh -m 'message about git commit'",
        ],
    )
    def test_allows_command(self, block_bash_hook_path: Path, command: str) -> None:
        """Test that non-blocked commands are allowed."""
        stdout, stderr, code = run_block_bash_hook(block_bash_hook_path, "Bash", command)
        assert code == 0, f"Should allow '{command}' with exit code 0, got {code}"


class TestNonBashTools:
    """Tests for non-Bash tool calls."""

    @pytest.mark.parametrize("tool_name", ["Read", "Write", "Edit", "Glob", "Grep"])
    def test_allows_non_bash_tools(self, block_bash_hook_path: Path, tool_name: str) -> None:
        """Test that non-Bash tools are not blocked even with git commit in input."""
        stdout, stderr, code = run_block_bash_hook(
            block_bash_hook_path, tool_name, "git commit -m 'test'"
        )
        assert code == 0, f"Should allow {tool_name} tool with exit code 0, got {code}"


class TestEdgeCases:
    """Tests for edge cases and malformed input."""

    def test_empty_input(self, block_bash_hook_path: Path) -> None:
        """Test that empty input is handled gracefully."""
        result = subprocess.run(
            ["bash", str(block_bash_hook_path)],
            capture_output=True,
            text=True,
            input="",
            env=os.environ.copy(),
        )
        assert result.returncode == 0, "Should allow with exit code 0 for empty input"

    def test_no_command_in_input(self, block_bash_hook_path: Path) -> None:
        """Test that missing command is handled gracefully."""
        hook_input = {"tool_name": "Bash", "tool_input": {}}
        result = subprocess.run(
            ["bash", str(block_bash_hook_path)],
            capture_output=True,
            text=True,
            input=json.dumps(hook_input),
            env=os.environ.copy(),
        )
        assert result.returncode == 0, "Should allow with exit code 0 for missing command"

    def test_invalid_json(self, block_bash_hook_path: Path) -> None:
        """Test that invalid JSON is handled gracefully."""
        result = subprocess.run(
            ["bash", str(block_bash_hook_path)],
            capture_output=True,
            text=True,
            input="not valid json",
            env=os.environ.copy(),
        )
        # Script uses set -e and jq, so invalid JSON causes jq to fail with exit 5
        # This is acceptable behavior - Claude Code won't send invalid JSON
        assert result.returncode in (0, 1, 5), (
            f"Should handle invalid JSON without crashing unexpectedly, got {result.returncode}"
        )


# ******************************************************************************
# ***                     CLAUDE CODE CONTRACT TEST                          ***
# ******************************************************************************
#
# DO NOT MODIFY this test without consulting Claude Code hook documentation:
# https://docs.anthropic.com/en/docs/claude-code/hooks
#
# PreToolUse hooks with exit code 2 MUST:
#   - Output error message to stderr (NOT stdout)
#   - Exit with code 2
#
# PreToolUse hooks that allow MUST:
#   - Exit with code 0
#   - Produce no output on stderr
#
# ******************************************************************************
class TestOutputsAndExitsAccordingToClaudeSpec:
    """Tests that hook output conforms to Claude Code's required format."""

    def test_claude_code_hook_contract(self, block_bash_hook_path: Path) -> None:
        """Verify hook follows Claude Code PreToolUse contract for block/allow."""
        # Test BLOCK behavior
        stdout, stderr, code = run_block_bash_hook(
            block_bash_hook_path, "Bash", "git commit -m 'test'"
        )
        assert code == 2, "Blocked command must exit with code 2"
        assert stderr.strip() != "", "Blocked command must output message to stderr"
        assert stdout.strip() == "", "Blocked command must not output to stdout"

        # Test ALLOW behavior
        stdout, stderr, code = run_block_bash_hook(block_bash_hook_path, "Bash", "git status")
        assert code == 0, "Allowed command must exit with code 0"
        assert stderr.strip() == "", "Allowed command must not output to stderr"
