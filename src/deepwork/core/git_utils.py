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

=============================================================================
GIT PLUMBING APPROACH FOR "COMPARE TO PROMPT"
=============================================================================

The CompareToPrompt comparator uses Git "plumbing" commands with a temporary
index to safely capture and compare working directory snapshots.

HOW IT WORKS:

1. At prompt submission time (capture_prompt_work_tree.sh):
   - Create a temporary index file (GIT_INDEX_FILE env var)
   - Stage all files to this temp index (git add -A)
   - Write the index to a tree object (git write-tree) -> returns SHA hash
   - Save the tree hash to .deepwork/.last_tree_hash

2. At comparison time (CompareToPrompt class):
   - Create another temporary index for the current state
   - Stage all current files and write to a tree object
   - Compare the two trees using "git diff-tree"

WHY THIS IS ROBUST:
- FAST: Git is optimized for tree comparisons
- SAFE: Does not touch HEAD, current Index, or Stashes
- COMPLETE: Handles modified, new (untracked), and deleted files
- CLEAN: Respects .gitignore automatically

WHAT WE CAN DETECT:
| Scenario              | Handled? | Explanation                                |
|-----------------------|----------|-------------------------------------------|
| Modified files        | ✅ Yes   | Git detects content hash changed          |
| New untracked files   | ✅ Yes   | git add -A captures them in temp index    |
| Deleted files         | ✅ Yes   | Tree comparison shows them as missing     |
| Staged vs Unstaged    | ✅ Yes   | We look at disk state, ignore staging     |
| Ignored files         | ❌ No    | git add respects .gitignore (by design)   |

KEY GIT PLUMBING CONCEPTS:
- GIT_INDEX_FILE: By setting this env var, Git uses a different index file.
  This lets us stage files without affecting the user's actual staging area.
- git write-tree: Plumbing command that writes the current index state to
  Git's object database as a tree object. Returns the SHA hash.
- git diff-tree: Compares two tree objects and reports differences.
  Much more reliable than comparing file lists manually.
=============================================================================
"""

from __future__ import annotations

import os
import subprocess
import tempfile
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


# =============================================================================
# GIT PLUMBING HELPERS FOR TREE-BASED COMPARISON
# =============================================================================


def _create_tree_from_working_dir() -> str | None:
    """Create a tree object representing the current working directory state.

    This function uses Git plumbing commands with a temporary index to create
    a tree object without affecting the actual staging area.

    HOW IT WORKS:
    1. Create a temporary file to act as a separate git index
    2. Set GIT_INDEX_FILE to use this temp index instead of .git/index
    3. Stage all files (git add -A) to the temp index
    4. Write the temp index to a tree object (git write-tree)
    5. Clean up the temp index file

    WHY A TEMPORARY INDEX:
    - We need to capture the ENTIRE working directory state (including untracked)
    - git add -A stages everything, but we don't want to mess with the user's
      actual staging area
    - By setting GIT_INDEX_FILE, Git uses our temp file instead of .git/index

    Returns:
        The SHA hash of the tree object, or None if creation failed.
    """
    temp_index = None
    original_env = os.environ.get("GIT_INDEX_FILE")

    try:
        # Create a temporary file for the index
        fd, temp_index = tempfile.mkstemp(prefix="deepwork_index_")
        os.close(fd)

        # Tell Git to use our temp index instead of .git/index
        os.environ["GIT_INDEX_FILE"] = temp_index

        # Stage everything to the temp index
        # -A handles new files, deletions, and modifications
        # Respects .gitignore automatically
        subprocess.run(
            ["git", "add", "-A"],
            capture_output=True,
            text=True,
            check=False,  # Don't fail if no files to add
        )

        # Write the index to a tree object and get the SHA hash
        result = subprocess.run(
            ["git", "write-tree"],
            capture_output=True,
            text=True,
            check=True,
        )

        return result.stdout.strip() or None

    except subprocess.CalledProcessError:
        return None

    finally:
        # Restore the original GIT_INDEX_FILE environment
        if original_env is None:
            os.environ.pop("GIT_INDEX_FILE", None)
        else:
            os.environ["GIT_INDEX_FILE"] = original_env

        # Clean up the temp index file
        if temp_index and os.path.exists(temp_index):
            os.unlink(temp_index)


def _diff_trees(
    tree_a: str, tree_b: str, diff_filter: str | None = None
) -> set[str]:
    """Compare two tree objects and return the files that differ.

    Uses git diff-tree to compare tree objects. This is Git's native way to
    compare directory snapshots and is highly optimized.

    Args:
        tree_a: SHA hash of the first tree (baseline/before)
        tree_b: SHA hash of the second tree (current/after)
        diff_filter: Optional filter for diff types:
            - "A" = Added files only (new in tree_b)
            - "D" = Deleted files only (removed from tree_b)
            - "M" = Modified files only
            - None = All changed files

    Returns:
        Set of file paths that differ between the trees.
    """
    args = ["diff-tree", "--name-only", "-r"]
    if diff_filter:
        args.append(f"--diff-filter={diff_filter}")
    args.extend([tree_a, tree_b])

    result = _run_git(*args)
    return _parse_file_list(result.stdout)


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

    ==========================================================================
    GIT PLUMBING APPROACH FOR ACCURATE CHANGE DETECTION
    ==========================================================================

    This comparator uses Git plumbing commands with temporary indexes to create
    and compare tree objects. This is the most robust way to detect what changed
    during an agent response because:

    1. COMPLETE: Captures ALL changes including untracked files
    2. SAFE: Uses temporary index, doesn't touch actual staging area
    3. ACCURATE: git diff-tree is Git's native tree comparison
    4. HANDLES COMMITS: Works even if changes were committed during response

    HOW IT WORKS:

    At prompt submission (capture_prompt_work_tree.sh):
    1. Create temporary index file
    2. Set GIT_INDEX_FILE to temp index
    3. git add -A (stage everything to temp index)
    4. git write-tree -> returns tree SHA hash
    5. Save hash to .deepwork/.last_tree_hash

    At comparison time (this class):
    1. Create another tree for current state (_create_tree_from_working_dir)
    2. Compare trees with git diff-tree (_diff_trees)
    3. Return the differences

    FALLBACK BEHAVIOR:
    If .last_tree_hash is missing (e.g., old capture script), falls back to:
    - .last_head_ref for get_changed_files() (compares commits)
    - .last_work_tree for get_created_files() (compares file lists)
    ==========================================================================
    """

    # Primary: Tree hash for robust git-plumbing comparison
    BASELINE_TREE_PATH = Path(".deepwork/.last_tree_hash")
    # Legacy fallbacks for backwards compatibility
    BASELINE_REF_PATH = Path(".deepwork/.last_head_ref")
    BASELINE_WORK_TREE_PATH = Path(".deepwork/.last_work_tree")

    def get_baseline_ref(self) -> str:
        """Return the baseline tree hash or fallback identifier."""
        if self.BASELINE_TREE_PATH.exists():
            tree_hash = self.BASELINE_TREE_PATH.read_text().strip()
            if tree_hash:
                return tree_hash[:12]  # Short hash for display
        if self.BASELINE_WORK_TREE_PATH.exists():
            return str(int(self.BASELINE_WORK_TREE_PATH.stat().st_mtime))
        return "prompt"

    def get_changed_files(self) -> list[str]:
        """Get files that changed since the prompt was submitted.

        Uses git diff-tree to compare the baseline tree (captured at prompt time)
        against the current working directory tree. This accurately captures:
        - Modified files
        - New files (including previously untracked)
        - Deleted files
        - Files that were committed during the response
        """
        try:
            # Try tree-based comparison first (most robust)
            if self.BASELINE_TREE_PATH.exists():
                baseline_tree = self.BASELINE_TREE_PATH.read_text().strip()
                if baseline_tree:
                    current_tree = _create_tree_from_working_dir()
                    if current_tree:
                        return sorted(_diff_trees(baseline_tree, current_tree))

            # Fallback to ref-based comparison
            _stage_all_changes()
            if self.BASELINE_REF_PATH.exists():
                baseline_ref = self.BASELINE_REF_PATH.read_text().strip()
                if baseline_ref:
                    return sorted(_get_all_changes_vs_ref(baseline_ref))

            # Last resort: compare against HEAD
            return sorted(_get_all_changes_vs_ref("HEAD") | _get_untracked_files())

        except (subprocess.CalledProcessError, OSError):
            return []

    def get_created_files(self) -> list[str]:
        """Get files created since the prompt was submitted.

        Uses git diff-tree with --diff-filter=A to find files that were added
        (exist in current tree but not in baseline tree). This accurately
        detects truly new files even if:
        - They were untracked before and are now tracked
        - They were committed during the response
        - The staging area was in an unusual state
        """
        try:
            # Try tree-based comparison first (most robust)
            if self.BASELINE_TREE_PATH.exists():
                baseline_tree = self.BASELINE_TREE_PATH.read_text().strip()
                if baseline_tree:
                    current_tree = _create_tree_from_working_dir()
                    if current_tree:
                        # diff-filter=A returns files Added in current tree
                        return sorted(_diff_trees(baseline_tree, current_tree, diff_filter="A"))

            # Fallback to file-list comparison for backwards compatibility
            # This handles cases where .last_tree_hash doesn't exist yet
            _stage_all_changes()
            current_files = _get_all_changes_vs_ref("HEAD") | _get_untracked_files()

            if self.BASELINE_WORK_TREE_PATH.exists():
                baseline_files = _parse_file_list(self.BASELINE_WORK_TREE_PATH.read_text())
                return sorted(current_files - baseline_files)
            else:
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
