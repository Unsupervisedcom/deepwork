"""Tests for user_prompt_submit.sh shell script.

This script is called as a Claude Code UserPromptSubmit hook.
It should:
1. Execute successfully (exit code 0)
2. Output valid JSON or no output (hooks allow both)
3. Capture work tree state by calling capture_prompt_work_tree.sh
"""

import json
from pathlib import Path

import pytest
from git import Repo

from .conftest import run_shell_script


def run_user_prompt_submit_hook(
    script_path: Path,
    cwd: Path,
    hook_input: dict | None = None,
) -> tuple[str, str, int]:
    """Run the user_prompt_submit.sh script and return its output."""
    return run_shell_script(script_path, cwd, hook_input=hook_input)


class TestUserPromptSubmitHookExecution:
    """Tests for user_prompt_submit.sh execution behavior."""

    def test_exits_successfully(self, policy_hooks_dir: Path, git_repo: Path) -> None:
        """Test that the hook exits with code 0."""
        script_path = policy_hooks_dir / "user_prompt_submit.sh"
        stdout, stderr, code = run_user_prompt_submit_hook(script_path, git_repo)

        assert code == 0, f"Expected exit code 0, got {code}. stderr: {stderr}"

    def test_creates_deepwork_directory(self, policy_hooks_dir: Path, git_repo: Path) -> None:
        """Test that the hook creates .deepwork directory if it doesn't exist."""
        deepwork_dir = git_repo / ".deepwork"
        assert not deepwork_dir.exists(), "Precondition: .deepwork should not exist"

        script_path = policy_hooks_dir / "user_prompt_submit.sh"
        stdout, stderr, code = run_user_prompt_submit_hook(script_path, git_repo)

        assert code == 0, f"Script failed with stderr: {stderr}"
        assert deepwork_dir.exists(), "Hook should create .deepwork directory"

    def test_creates_last_work_tree_file(self, policy_hooks_dir: Path, git_repo: Path) -> None:
        """Test that the hook creates .deepwork/.last_work_tree file."""
        script_path = policy_hooks_dir / "user_prompt_submit.sh"
        stdout, stderr, code = run_user_prompt_submit_hook(script_path, git_repo)

        work_tree_file = git_repo / ".deepwork" / ".last_work_tree"
        assert code == 0, f"Script failed with stderr: {stderr}"
        assert work_tree_file.exists(), "Hook should create .last_work_tree file"

    def test_captures_staged_changes(self, policy_hooks_dir: Path, git_repo: Path) -> None:
        """Test that the hook captures staged file changes."""
        # Create and stage a new file
        new_file = git_repo / "new_file.py"
        new_file.write_text("# New file\n")
        repo = Repo(git_repo)
        repo.index.add(["new_file.py"])

        script_path = policy_hooks_dir / "user_prompt_submit.sh"
        stdout, stderr, code = run_user_prompt_submit_hook(script_path, git_repo)

        assert code == 0, f"Script failed with stderr: {stderr}"

        work_tree_file = git_repo / ".deepwork" / ".last_work_tree"
        content = work_tree_file.read_text()
        assert "new_file.py" in content, "Staged file should be captured"

    def test_captures_untracked_files(self, policy_hooks_dir: Path, git_repo: Path) -> None:
        """Test that the hook captures untracked files."""
        # Create an untracked file (don't stage it)
        untracked = git_repo / "untracked.txt"
        untracked.write_text("untracked content\n")

        script_path = policy_hooks_dir / "user_prompt_submit.sh"
        stdout, stderr, code = run_user_prompt_submit_hook(script_path, git_repo)

        assert code == 0, f"Script failed with stderr: {stderr}"

        work_tree_file = git_repo / ".deepwork" / ".last_work_tree"
        content = work_tree_file.read_text()
        # After running the hook, files are staged, so check for the file
        assert "untracked.txt" in content, "Untracked file should be captured"


class TestUserPromptSubmitHookJsonOutput:
    """Tests for user_prompt_submit.sh JSON output format.

    Claude Code UserPromptSubmit hooks can output:
    - Empty output (most common for side-effect-only hooks)
    - Valid JSON (if the hook needs to communicate something)

    Either is acceptable; invalid JSON is NOT acceptable.
    """

    def test_output_is_empty_or_valid_json(self, policy_hooks_dir: Path, git_repo: Path) -> None:
        """Test that output is either empty or valid JSON."""
        script_path = policy_hooks_dir / "user_prompt_submit.sh"
        stdout, stderr, code = run_user_prompt_submit_hook(script_path, git_repo)

        output = stdout.strip()

        if output:
            # If there's output, it must be valid JSON
            try:
                result = json.loads(output)
                assert isinstance(result, dict), "JSON output should be an object"
            except json.JSONDecodeError as e:
                pytest.fail(f"Output is not valid JSON: {output!r}. Error: {e}")

    def test_does_not_block_prompt(self, policy_hooks_dir: Path, git_repo: Path) -> None:
        """Test that the hook does not return a blocking response."""
        script_path = policy_hooks_dir / "user_prompt_submit.sh"
        stdout, stderr, code = run_user_prompt_submit_hook(script_path, git_repo)

        output = stdout.strip()

        if output:
            try:
                result = json.loads(output)
                # UserPromptSubmit hooks should not block
                assert result.get("decision") != "block", (
                    "UserPromptSubmit hook should not block prompt submission"
                )
            except json.JSONDecodeError:
                pass  # Empty or non-JSON output is fine


class TestUserPromptSubmitHookIdempotence:
    """Tests for idempotent behavior of user_prompt_submit.sh."""

    def test_multiple_runs_succeed(self, policy_hooks_dir: Path, git_repo: Path) -> None:
        """Test that the hook can be run multiple times successfully."""
        script_path = policy_hooks_dir / "user_prompt_submit.sh"

        # Run multiple times
        for i in range(3):
            stdout, stderr, code = run_user_prompt_submit_hook(script_path, git_repo)
            assert code == 0, f"Run {i + 1} failed with stderr: {stderr}"

    def test_updates_work_tree_on_new_changes(self, policy_hooks_dir: Path, git_repo: Path) -> None:
        """Test that subsequent runs update the work tree state."""
        script_path = policy_hooks_dir / "user_prompt_submit.sh"
        repo = Repo(git_repo)

        # First run - capture initial state
        run_user_prompt_submit_hook(script_path, git_repo)
        work_tree_file = git_repo / ".deepwork" / ".last_work_tree"
        assert work_tree_file.exists(), "Work tree file should exist after first run"

        # Create and stage a new file
        new_file = git_repo / "another_file.py"
        new_file.write_text("# Another file\n")
        repo.index.add(["another_file.py"])

        # Second run - should capture new file
        run_user_prompt_submit_hook(script_path, git_repo)
        updated_content = work_tree_file.read_text()

        assert "another_file.py" in updated_content, "New file should be captured"
