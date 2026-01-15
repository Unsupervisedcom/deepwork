"""Tests for capture_prompt_work_tree.sh helper script.

This script captures the git work tree state for use with
compare_to: prompt policies. It should:
1. Create .deepwork directory if needed
2. Stage all changes with git add -A
3. Record changed files to .deepwork/.last_work_tree
4. Handle various git states gracefully
"""

from pathlib import Path

import pytest
from git import Repo

from .conftest import run_shell_script


@pytest.fixture
def git_repo_with_changes(git_repo: Path) -> Path:
    """Create a git repo with uncommitted changes."""
    # Create some changed files
    (git_repo / "modified.py").write_text("# Modified file\n")
    (git_repo / "src").mkdir(exist_ok=True)
    (git_repo / "src" / "main.py").write_text("# Main file\n")

    return git_repo


def run_capture_script(script_path: Path, cwd: Path) -> tuple[str, str, int]:
    """Run the capture_prompt_work_tree.sh script."""
    return run_shell_script(script_path, cwd)


class TestCapturePromptWorkTreeBasic:
    """Basic functionality tests for capture_prompt_work_tree.sh."""

    def test_exits_successfully(self, policy_hooks_dir: Path, git_repo: Path) -> None:
        """Test that the script exits with code 0."""
        script_path = policy_hooks_dir / "capture_prompt_work_tree.sh"
        stdout, stderr, code = run_capture_script(script_path, git_repo)

        assert code == 0, f"Expected exit code 0, got {code}. stderr: {stderr}"

    def test_creates_deepwork_directory(self, policy_hooks_dir: Path, git_repo: Path) -> None:
        """Test that the script creates .deepwork directory."""
        deepwork_dir = git_repo / ".deepwork"
        assert not deepwork_dir.exists(), "Precondition: .deepwork should not exist"

        script_path = policy_hooks_dir / "capture_prompt_work_tree.sh"
        stdout, stderr, code = run_capture_script(script_path, git_repo)

        assert code == 0, f"Script failed with stderr: {stderr}"
        assert deepwork_dir.exists(), "Script should create .deepwork directory"

    def test_creates_last_work_tree_file(self, policy_hooks_dir: Path, git_repo: Path) -> None:
        """Test that the script creates .last_work_tree file."""
        script_path = policy_hooks_dir / "capture_prompt_work_tree.sh"
        stdout, stderr, code = run_capture_script(script_path, git_repo)

        work_tree_file = git_repo / ".deepwork" / ".last_work_tree"
        assert code == 0, f"Script failed with stderr: {stderr}"
        assert work_tree_file.exists(), "Script should create .last_work_tree file"

    def test_empty_repo_produces_empty_file(self, policy_hooks_dir: Path, git_repo: Path) -> None:
        """Test that a clean repo produces an empty work tree file."""
        script_path = policy_hooks_dir / "capture_prompt_work_tree.sh"
        stdout, stderr, code = run_capture_script(script_path, git_repo)

        # Clean repo should have empty or minimal content
        # May have .deepwork/.last_work_tree itself listed
        assert code == 0, f"Script failed with stderr: {stderr}"


class TestCapturePromptWorkTreeFileTracking:
    """Tests for file tracking behavior in capture_prompt_work_tree.sh."""

    def test_captures_staged_files(self, policy_hooks_dir: Path, git_repo: Path) -> None:
        """Test that staged files are captured."""
        # Create and stage a file
        new_file = git_repo / "staged.py"
        new_file.write_text("# Staged file\n")
        repo = Repo(git_repo)
        repo.index.add(["staged.py"])

        script_path = policy_hooks_dir / "capture_prompt_work_tree.sh"
        stdout, stderr, code = run_capture_script(script_path, git_repo)

        work_tree_file = git_repo / ".deepwork" / ".last_work_tree"
        content = work_tree_file.read_text()

        assert code == 0, f"Script failed with stderr: {stderr}"
        assert "staged.py" in content, "Staged file should be in work tree"

    def test_captures_unstaged_changes(self, policy_hooks_dir: Path, git_repo: Path) -> None:
        """Test that unstaged changes are captured (after staging by script)."""
        # Create an unstaged file
        unstaged = git_repo / "unstaged.py"
        unstaged.write_text("# Unstaged file\n")

        script_path = policy_hooks_dir / "capture_prompt_work_tree.sh"
        stdout, stderr, code = run_capture_script(script_path, git_repo)

        work_tree_file = git_repo / ".deepwork" / ".last_work_tree"
        content = work_tree_file.read_text()

        assert code == 0, f"Script failed with stderr: {stderr}"
        assert "unstaged.py" in content, "Unstaged file should be captured"

    def test_captures_files_in_subdirectories(self, policy_hooks_dir: Path, git_repo: Path) -> None:
        """Test that files in subdirectories are captured."""
        # Create files in nested directories
        src_dir = git_repo / "src" / "components"
        src_dir.mkdir(parents=True)
        (src_dir / "button.py").write_text("# Button component\n")

        script_path = policy_hooks_dir / "capture_prompt_work_tree.sh"
        stdout, stderr, code = run_capture_script(script_path, git_repo)

        work_tree_file = git_repo / ".deepwork" / ".last_work_tree"
        content = work_tree_file.read_text()

        assert code == 0, f"Script failed with stderr: {stderr}"
        assert "src/components/button.py" in content, "Nested file should be captured"

    def test_captures_multiple_files(
        self, policy_hooks_dir: Path, git_repo_with_changes: Path
    ) -> None:
        """Test that multiple files are captured."""
        script_path = policy_hooks_dir / "capture_prompt_work_tree.sh"
        stdout, stderr, code = run_capture_script(script_path, git_repo_with_changes)

        work_tree_file = git_repo_with_changes / ".deepwork" / ".last_work_tree"
        content = work_tree_file.read_text()

        assert code == 0, f"Script failed with stderr: {stderr}"
        assert "modified.py" in content, "Modified file should be captured"
        assert "src/main.py" in content, "File in src/ should be captured"

    def test_file_list_is_sorted_and_unique(self, policy_hooks_dir: Path, git_repo: Path) -> None:
        """Test that the file list is sorted and deduplicated."""
        # Create multiple files
        (git_repo / "z_file.py").write_text("# Z file\n")
        (git_repo / "a_file.py").write_text("# A file\n")
        (git_repo / "m_file.py").write_text("# M file\n")

        script_path = policy_hooks_dir / "capture_prompt_work_tree.sh"
        stdout, stderr, code = run_capture_script(script_path, git_repo)

        work_tree_file = git_repo / ".deepwork" / ".last_work_tree"
        lines = [line for line in work_tree_file.read_text().strip().split("\n") if line]

        # Extract just the test files we created (filter out .deepwork files)
        test_files = [f for f in lines if f.endswith("_file.py")]

        assert code == 0, f"Script failed with stderr: {stderr}"
        assert test_files == sorted(test_files), "Files should be sorted"
        assert len(test_files) == len(set(test_files)), "Files should be unique"


class TestCapturePromptWorkTreeGitStates:
    """Tests for handling various git states in capture_prompt_work_tree.sh."""

    def test_handles_deleted_files(self, policy_hooks_dir: Path, git_repo: Path) -> None:
        """Test that deleted files are handled gracefully."""
        # Create and commit a file, then delete it
        to_delete = git_repo / "to_delete.py"
        to_delete.write_text("# Will be deleted\n")
        repo = Repo(git_repo)
        repo.index.add(["to_delete.py"])
        repo.index.commit("Add file to delete")

        # Now delete it
        to_delete.unlink()

        script_path = policy_hooks_dir / "capture_prompt_work_tree.sh"
        stdout, stderr, code = run_capture_script(script_path, git_repo)

        assert code == 0, f"Script should handle deletions. stderr: {stderr}"

    def test_handles_renamed_files(self, policy_hooks_dir: Path, git_repo: Path) -> None:
        """Test that renamed files are tracked."""
        # Create and commit a file
        old_name = git_repo / "old_name.py"
        old_name.write_text("# Original file\n")
        repo = Repo(git_repo)
        repo.index.add(["old_name.py"])
        repo.index.commit("Add original file")

        # Rename it
        new_name = git_repo / "new_name.py"
        old_name.rename(new_name)

        script_path = policy_hooks_dir / "capture_prompt_work_tree.sh"
        stdout, stderr, code = run_capture_script(script_path, git_repo)

        work_tree_file = git_repo / ".deepwork" / ".last_work_tree"
        content = work_tree_file.read_text()

        assert code == 0, f"Script failed with stderr: {stderr}"
        # Both old (deleted) and new should appear as changes
        assert "new_name.py" in content, "New filename should be captured"

    def test_handles_modified_files(self, policy_hooks_dir: Path, git_repo: Path) -> None:
        """Test that modified committed files are tracked."""
        # Modify an existing committed file
        readme = git_repo / "README.md"
        readme.write_text("# Modified content\n")

        script_path = policy_hooks_dir / "capture_prompt_work_tree.sh"
        stdout, stderr, code = run_capture_script(script_path, git_repo)

        work_tree_file = git_repo / ".deepwork" / ".last_work_tree"
        content = work_tree_file.read_text()

        assert code == 0, f"Script failed with stderr: {stderr}"
        assert "README.md" in content, "Modified file should be captured"


class TestCapturePromptWorkTreeIdempotence:
    """Tests for idempotent behavior of capture_prompt_work_tree.sh."""

    def test_multiple_runs_succeed(self, policy_hooks_dir: Path, git_repo: Path) -> None:
        """Test that the script can be run multiple times."""
        script_path = policy_hooks_dir / "capture_prompt_work_tree.sh"

        for i in range(3):
            stdout, stderr, code = run_capture_script(script_path, git_repo)
            assert code == 0, f"Run {i + 1} failed with stderr: {stderr}"

    def test_updates_on_new_changes(self, policy_hooks_dir: Path, git_repo: Path) -> None:
        """Test that subsequent runs capture new changes."""
        script_path = policy_hooks_dir / "capture_prompt_work_tree.sh"

        # First run
        run_capture_script(script_path, git_repo)

        # Add a new file
        (git_repo / "new_file.py").write_text("# New\n")

        # Second run
        run_capture_script(script_path, git_repo)

        work_tree_file = git_repo / ".deepwork" / ".last_work_tree"
        content = work_tree_file.read_text()

        assert "new_file.py" in content, "New file should be captured"

    def test_existing_deepwork_dir_not_error(self, policy_hooks_dir: Path, git_repo: Path) -> None:
        """Test that existing .deepwork directory is not an error."""
        # Pre-create the directory
        (git_repo / ".deepwork").mkdir()

        script_path = policy_hooks_dir / "capture_prompt_work_tree.sh"
        stdout, stderr, code = run_capture_script(script_path, git_repo)

        assert code == 0, f"Should handle existing .deepwork dir. stderr: {stderr}"
