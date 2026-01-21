"""
Git utilities for DeepWork rules system.

This module provides abstractions for comparing file changes against different
baselines. The main interface is GitComparator with implementations for:

- CompareToBase: Compare against merge-base with origin's default branch
- CompareToDefaultTip: Compare against the tip of origin's default branch
- CompareToPrompt: Compare against the state captured when a prompt was submitted

Usage:
    comparator = get_comparator("base")  # or "default_tip" or "prompt"
    changed_files = comparator.get_changed_files()
    created_files = comparator.get_created_files()
    baseline_ref = comparator.get_baseline_ref()
"""

from __future__ import annotations

import subprocess
from abc import ABC, abstractmethod
from pathlib import Path


def get_default_branch() -> str:
    """Get the default branch name (main or master)."""
    try:
        result = subprocess.run(
            ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip().split("/")[-1]
    except subprocess.CalledProcessError:
        pass

    for branch in ["main", "master"]:
        try:
            subprocess.run(
                ["git", "rev-parse", "--verify", f"origin/{branch}"],
                capture_output=True,
                check=True,
            )
            return branch
        except subprocess.CalledProcessError:
            continue

    return "main"


def _parse_file_list(output: str) -> set[str]:
    """Parse newline-separated git output into a set of non-empty file paths."""
    if not output.strip():
        return set()
    return {f for f in output.strip().split("\n") if f}


def _run_git(*args: str, check: bool = False) -> subprocess.CompletedProcess[str]:
    """Run a git command and return the result."""
    return subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        check=check,
    )


def _get_untracked_files() -> set[str]:
    """Get untracked files (excluding ignored)."""
    return _parse_file_list(_run_git("ls-files", "--others", "--exclude-standard").stdout)


def _stage_all_changes() -> None:
    """Stage all changes including untracked files."""
    _run_git("add", "-A")


def _get_all_changes_vs_ref(ref: str, diff_filter: str | None = None) -> set[str]:
    """Get all files that differ between the index and a ref.

    After staging all changes (git add -A), the index contains the complete
    current state. Comparing the index to a ref captures:
    - Files changed in commits since ref
    - Files staged but not yet committed
    - Files that were untracked (now staged)

    Args:
        ref: The git ref to compare against
        diff_filter: Optional diff filter (e.g., "A" for added files only)

    Returns:
        Set of file paths that differ from the ref
    """
    args = ["diff", "--name-only", "--cached", ref]
    if diff_filter:
        args.insert(2, f"--diff-filter={diff_filter}")
    return _parse_file_list(_run_git(*args).stdout)


class GitComparator(ABC):
    """Abstract base class for comparing git changes against a baseline."""

    @abstractmethod
    def get_changed_files(self) -> list[str]:
        """Get list of files that changed relative to the baseline."""
        pass

    @abstractmethod
    def get_created_files(self) -> list[str]:
        """Get list of files that were newly created relative to the baseline."""
        pass

    @abstractmethod
    def get_baseline_ref(self) -> str:
        """Get the git reference or identifier for the baseline."""
        pass


class RefBasedComparator(GitComparator):
    """Base class for comparators that compare against a git ref.

    Subclasses only need to implement _get_ref() and _get_fallback_name().
    """

    def __init__(self) -> None:
        self._cached_ref: str | None = None

    @abstractmethod
    def _get_ref(self) -> str | None:
        """Get the git ref to compare against. Returns None if unavailable."""
        pass

    @abstractmethod
    def _get_fallback_name(self) -> str:
        """Get the fallback name to use when ref is unavailable."""
        pass

    def _resolve_ref(self) -> str | None:
        """Get and cache the ref."""
        if self._cached_ref is None:
            ref = self._get_ref()
            self._cached_ref = ref if ref else ""
        return self._cached_ref if self._cached_ref else None

    def get_baseline_ref(self) -> str:
        ref = self._resolve_ref()
        return ref if ref else self._get_fallback_name()

    def get_changed_files(self) -> list[str]:
        ref = self._resolve_ref()
        if not ref:
            return []

        try:
            _stage_all_changes()
            # After staging, comparing index to ref captures all changes
            changed = _get_all_changes_vs_ref(ref)
            return sorted(changed)
        except subprocess.CalledProcessError:
            return []

    def get_created_files(self) -> list[str]:
        ref = self._resolve_ref()
        if not ref:
            return []

        try:
            _stage_all_changes()
            # After staging, comparing index to ref with --diff-filter=A captures all new files
            created = _get_all_changes_vs_ref(ref, diff_filter="A")
            return sorted(created)
        except subprocess.CalledProcessError:
            return []


class CompareToBase(RefBasedComparator):
    """Compare changes against merge-base with the default branch."""

    def __init__(self) -> None:
        super().__init__()
        self._default_branch = get_default_branch()

    def _get_ref(self) -> str | None:
        try:
            result = _run_git("merge-base", "HEAD", f"origin/{self._default_branch}", check=True)
            return result.stdout.strip() or None
        except subprocess.CalledProcessError:
            return None

    def _get_fallback_name(self) -> str:
        return "base"


class CompareToDefaultTip(RefBasedComparator):
    """Compare changes against the tip of the default branch."""

    def __init__(self) -> None:
        super().__init__()
        self._default_branch = get_default_branch()

    def _get_ref(self) -> str | None:
        try:
            result = _run_git("rev-parse", f"origin/{self._default_branch}", check=True)
            return result.stdout.strip() or None
        except subprocess.CalledProcessError:
            return None

    def _get_fallback_name(self) -> str:
        return "default_tip"


class CompareToPrompt(GitComparator):
    """Compare changes against the state when a prompt was submitted.

    Uses baseline files captured at prompt submission time to detect
    what changed during the agent's response.
    """

    BASELINE_REF_PATH = Path(".deepwork/.last_head_ref")
    BASELINE_WORK_TREE_PATH = Path(".deepwork/.last_work_tree")

    def get_baseline_ref(self) -> str:
        if self.BASELINE_WORK_TREE_PATH.exists():
            return str(int(self.BASELINE_WORK_TREE_PATH.stat().st_mtime))
        return "prompt"

    def get_changed_files(self) -> list[str]:
        try:
            _stage_all_changes()

            if self.BASELINE_REF_PATH.exists():
                baseline_ref = self.BASELINE_REF_PATH.read_text().strip()
                if baseline_ref:
                    # Use simplified approach: after staging, index vs ref captures all changes
                    return sorted(_get_all_changes_vs_ref(baseline_ref))

            # No baseline ref - return all staged and untracked files
            return sorted(_get_all_changes_vs_ref("HEAD") | _get_untracked_files())

        except (subprocess.CalledProcessError, OSError):
            return []

    def get_created_files(self) -> list[str]:
        """Get files created since the prompt was submitted.

        Unlike get_changed_files(), this method always uses .last_work_tree
        for comparison (not .last_head_ref) because .last_work_tree contains
        the actual list of files that existed at prompt time, including
        uncommitted files. Using git-based detection would incorrectly flag
        uncommitted files from before the prompt as "created".
        """
        try:
            _stage_all_changes()

            # Get all current files (staged after git add -A, plus any remaining untracked)
            current_files = _get_all_changes_vs_ref("HEAD") | _get_untracked_files()

            if self.BASELINE_WORK_TREE_PATH.exists():
                # Compare against the file list captured at prompt time
                baseline_files = _parse_file_list(self.BASELINE_WORK_TREE_PATH.read_text())
                return sorted(current_files - baseline_files)
            else:
                # No baseline means all current files are "new" to this prompt
                return sorted(current_files)

        except (subprocess.CalledProcessError, OSError):
            return []


def get_comparator(mode: str) -> GitComparator:
    """Factory function to get the appropriate comparator for a mode."""
    comparators: dict[str, type[GitComparator]] = {
        "base": CompareToBase,
        "default_tip": CompareToDefaultTip,
        "prompt": CompareToPrompt,
    }
    comparator_class = comparators.get(mode, CompareToBase)
    return comparator_class()
