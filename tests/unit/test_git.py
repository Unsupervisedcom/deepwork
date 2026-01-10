"""Tests for Git utilities."""

from pathlib import Path

import pytest

from deepwork.utils.git import (
    GitError,
    branch_exists,
    create_branch,
    get_current_branch,
    get_repo,
    get_repo_root,
    get_untracked_files,
    has_uncommitted_changes,
    is_git_repo,
)


class TestIsGitRepo:
    """Tests for is_git_repo function."""

    def test_returns_true_for_git_repo(self, mock_git_repo: Path) -> None:
        """Test that is_git_repo returns True for Git repository."""
        assert is_git_repo(mock_git_repo)

    def test_returns_true_for_subdirectory(self, mock_git_repo: Path) -> None:
        """Test that is_git_repo returns True for subdirectory in Git repo."""
        subdir = mock_git_repo / "subdir"
        subdir.mkdir()

        assert is_git_repo(subdir)

    def test_returns_false_for_non_git_directory(self, temp_dir: Path) -> None:
        """Test that is_git_repo returns False for non-Git directory."""
        assert not is_git_repo(temp_dir)

    def test_accepts_string_path(self, mock_git_repo: Path) -> None:
        """Test that is_git_repo accepts string paths."""
        assert is_git_repo(str(mock_git_repo))


class TestGetRepo:
    """Tests for get_repo function."""

    def test_returns_repo_object(self, mock_git_repo: Path) -> None:
        """Test that get_repo returns Repo object."""
        repo = get_repo(mock_git_repo)

        assert repo is not None
        assert Path(repo.working_tree_dir) == mock_git_repo

    def test_works_from_subdirectory(self, mock_git_repo: Path) -> None:
        """Test that get_repo works from subdirectory."""
        subdir = mock_git_repo / "subdir"
        subdir.mkdir()

        repo = get_repo(subdir)

        assert Path(repo.working_tree_dir) == mock_git_repo

    def test_raises_for_non_git_directory(self, temp_dir: Path) -> None:
        """Test that get_repo raises GitError for non-Git directory."""
        with pytest.raises(GitError, match="Not a Git repository"):
            get_repo(temp_dir)


class TestGetRepoRoot:
    """Tests for get_repo_root function."""

    def test_returns_repo_root(self, mock_git_repo: Path) -> None:
        """Test that get_repo_root returns repository root."""
        root = get_repo_root(mock_git_repo)

        assert root == mock_git_repo

    def test_returns_root_from_subdirectory(self, mock_git_repo: Path) -> None:
        """Test that get_repo_root returns root from subdirectory."""
        subdir = mock_git_repo / "nested" / "subdir"
        subdir.mkdir(parents=True)

        root = get_repo_root(subdir)

        assert root == mock_git_repo


class TestGetCurrentBranch:
    """Tests for get_current_branch function."""

    def test_returns_current_branch(self, mock_git_repo: Path) -> None:
        """Test that get_current_branch returns current branch name."""
        # Default branch is typically 'master' or 'main'
        branch_name = get_current_branch(mock_git_repo)

        assert isinstance(branch_name, str)
        assert len(branch_name) > 0

    def test_returns_correct_branch_after_switch(self, mock_git_repo: Path) -> None:
        """Test that get_current_branch returns correct branch after switch."""
        create_branch(mock_git_repo, "test-branch", checkout=True)

        branch_name = get_current_branch(mock_git_repo)

        assert branch_name == "test-branch"


class TestBranchExists:
    """Tests for branch_exists function."""

    def test_returns_true_for_existing_branch(self, mock_git_repo: Path) -> None:
        """Test that branch_exists returns True for existing branch."""
        current_branch = get_current_branch(mock_git_repo)

        assert branch_exists(mock_git_repo, current_branch)

    def test_returns_false_for_nonexistent_branch(self, mock_git_repo: Path) -> None:
        """Test that branch_exists returns False for nonexistent branch."""
        assert not branch_exists(mock_git_repo, "nonexistent-branch")

    def test_returns_true_after_creating_branch(self, mock_git_repo: Path) -> None:
        """Test that branch_exists returns True after creating branch."""
        create_branch(mock_git_repo, "new-branch")

        assert branch_exists(mock_git_repo, "new-branch")


class TestCreateBranch:
    """Tests for create_branch function."""

    def test_creates_new_branch(self, mock_git_repo: Path) -> None:
        """Test that create_branch creates a new branch."""
        create_branch(mock_git_repo, "feature-branch")

        assert branch_exists(mock_git_repo, "feature-branch")

    def test_creates_and_checks_out_branch(self, mock_git_repo: Path) -> None:
        """Test that create_branch can checkout new branch."""
        create_branch(mock_git_repo, "feature-branch", checkout=True)

        assert get_current_branch(mock_git_repo) == "feature-branch"

    def test_creates_without_checkout(self, mock_git_repo: Path) -> None:
        """Test that create_branch can create without checkout."""
        original_branch = get_current_branch(mock_git_repo)
        create_branch(mock_git_repo, "feature-branch", checkout=False)

        assert branch_exists(mock_git_repo, "feature-branch")
        assert get_current_branch(mock_git_repo) == original_branch

    def test_raises_for_duplicate_branch(self, mock_git_repo: Path) -> None:
        """Test that create_branch raises for duplicate branch name."""
        create_branch(mock_git_repo, "duplicate-branch")

        with pytest.raises(GitError, match="already exists"):
            create_branch(mock_git_repo, "duplicate-branch")


class TestHasUncommittedChanges:
    """Tests for has_uncommitted_changes function."""

    def test_returns_false_for_clean_repo(self, mock_git_repo: Path) -> None:
        """Test that has_uncommitted_changes returns False for clean repo."""
        assert not has_uncommitted_changes(mock_git_repo)

    def test_returns_true_for_modified_file(self, mock_git_repo: Path) -> None:
        """Test that has_uncommitted_changes returns True for modified file."""
        readme = mock_git_repo / "README.md"
        readme.write_text("Modified content")

        assert has_uncommitted_changes(mock_git_repo)

    def test_returns_true_for_new_file(self, mock_git_repo: Path) -> None:
        """Test that has_uncommitted_changes returns True for new file."""
        new_file = mock_git_repo / "new_file.txt"
        new_file.write_text("New file content")

        assert has_uncommitted_changes(mock_git_repo)

    def test_returns_false_after_commit(self, mock_git_repo: Path) -> None:
        """Test that has_uncommitted_changes returns False after commit."""
        new_file = mock_git_repo / "test.txt"
        new_file.write_text("Test content")

        repo = get_repo(mock_git_repo)
        repo.index.add([str(new_file)])
        repo.index.commit("Add test file")

        assert not has_uncommitted_changes(mock_git_repo)


class TestGetUntrackedFiles:
    """Tests for get_untracked_files function."""

    def test_returns_empty_list_for_clean_repo(self, mock_git_repo: Path) -> None:
        """Test that get_untracked_files returns empty list for clean repo."""
        untracked = get_untracked_files(mock_git_repo)

        assert untracked == []

    def test_returns_untracked_files(self, mock_git_repo: Path) -> None:
        """Test that get_untracked_files returns untracked files."""
        (mock_git_repo / "file1.txt").write_text("Content 1")
        (mock_git_repo / "file2.txt").write_text("Content 2")

        untracked = get_untracked_files(mock_git_repo)

        assert len(untracked) == 2
        assert "file1.txt" in untracked
        assert "file2.txt" in untracked

    def test_excludes_tracked_files(self, mock_git_repo: Path) -> None:
        """Test that get_untracked_files excludes tracked files."""
        new_file = mock_git_repo / "new.txt"
        new_file.write_text("New content")

        repo = get_repo(mock_git_repo)
        repo.index.add([str(new_file)])

        untracked = get_untracked_files(mock_git_repo)

        assert "new.txt" not in untracked
