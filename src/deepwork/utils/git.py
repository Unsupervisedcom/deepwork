"""Git utilities for repository operations."""

from pathlib import Path
from typing import Optional

from git import GitCommandError, InvalidGitRepositoryError, Repo


class GitError(Exception):
    """Exception raised for Git-related errors."""

    pass


def is_git_repo(path: Path | str) -> bool:
    """
    Check if path is inside a Git repository.

    Args:
        path: Path to check

    Returns:
        True if path is in a Git repository, False otherwise
    """
    try:
        Repo(path, search_parent_directories=True)
        return True
    except InvalidGitRepositoryError:
        return False


def get_repo(path: Path | str) -> Repo:
    """
    Get GitPython Repo object for path.

    Args:
        path: Path inside Git repository

    Returns:
        GitPython Repo object

    Raises:
        GitError: If path is not in a Git repository
    """
    try:
        return Repo(path, search_parent_directories=True)
    except InvalidGitRepositoryError as e:
        raise GitError(f"Not a Git repository: {path}") from e


def get_repo_root(path: Path | str) -> Path:
    """
    Get root directory of Git repository.

    Args:
        path: Path inside Git repository

    Returns:
        Path to repository root directory

    Raises:
        GitError: If path is not in a Git repository
    """
    repo = get_repo(path)
    return Path(repo.working_tree_dir)


def get_current_branch(path: Path | str) -> str:
    """
    Get name of current branch.

    Args:
        path: Path inside Git repository

    Returns:
        Name of current branch

    Raises:
        GitError: If path is not in a Git repository or HEAD is detached
    """
    repo = get_repo(path)

    if repo.head.is_detached:
        raise GitError("HEAD is detached, not on any branch")

    return repo.active_branch.name


def branch_exists(path: Path | str, name: str) -> bool:
    """
    Check if branch exists.

    Args:
        path: Path inside Git repository
        name: Branch name to check

    Returns:
        True if branch exists, False otherwise

    Raises:
        GitError: If path is not in a Git repository
    """
    repo = get_repo(path)
    return name in [ref.name for ref in repo.heads]


def create_branch(path: Path | str, name: str, checkout: bool = False) -> None:
    """
    Create a new branch.

    Args:
        path: Path inside Git repository
        name: Name for the new branch
        checkout: If True, checkout the new branch after creation

    Raises:
        GitError: If path is not in a Git repository, branch already exists, or creation fails
    """
    repo = get_repo(path)

    # Check if branch already exists
    if branch_exists(path, name):
        raise GitError(f"Branch '{name}' already exists")

    try:
        new_branch = repo.create_head(name)
        if checkout:
            repo.head.reference = new_branch
            repo.head.reset(index=True, working_tree=True)
    except GitCommandError as e:
        raise GitError(f"Failed to create branch '{name}': {e}") from e


def has_uncommitted_changes(path: Path | str) -> bool:
    """
    Check if repository has uncommitted changes.

    Args:
        path: Path inside Git repository

    Returns:
        True if there are uncommitted changes, False otherwise

    Raises:
        GitError: If path is not in a Git repository
    """
    repo = get_repo(path)
    return repo.is_dirty(untracked_files=True)


def get_untracked_files(path: Path | str) -> list[str]:
    """
    Get list of untracked files.

    Args:
        path: Path inside Git repository

    Returns:
        List of untracked file paths

    Raises:
        GitError: If path is not in a Git repository
    """
    repo = get_repo(path)
    return repo.untracked_files
