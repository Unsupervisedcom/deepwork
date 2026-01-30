"""
================================================================================
                    REQUIREMENTS TESTS - DO NOT MODIFY
================================================================================

These tests verify CRITICAL REQUIREMENTS for the Git comparison utilities.
They ensure the git_utils module behaves correctly with respect to:

1. INTERFACE: All comparators implement a common interface
2. FACTORY: get_comparator() returns the correct comparator type
3. CREATED FILES: CompareToPrompt.get_created_files() detects truly new files
4. CHANGED FILES: get_changed_files() captures all changes since baseline

WARNING: These tests represent contractual requirements for the rules_check hook.
Modifying these tests may violate expected behavior and could cause rules to
not trigger correctly. If a test fails, fix the IMPLEMENTATION, not the test.

Requirements tested:
  - REQ-001: All comparators MUST implement GitComparator interface
  - REQ-002: get_comparator() MUST return correct comparator for each mode
  - REQ-003: CompareToPrompt.get_created_files() MUST correctly detect new files
            (uses tree-based comparison when available, falls back to .last_work_tree)
  - REQ-004: Created files are those NOT present in baseline

================================================================================
"""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

from deepwork.core.git_utils import (
    CompareToBase,
    CompareToDefaultTip,
    CompareToPrompt,
    GitComparator,
    _create_tree_from_working_dir,
    _diff_trees,
    _get_all_changes_vs_ref,
    _parse_file_list,
    get_comparator,
    get_default_branch,
)

# =============================================================================
# REQ-001: All comparators MUST implement GitComparator interface
# =============================================================================
#
# The git_utils module provides multiple comparator classes for different
# comparison modes (base, default_tip, prompt). All comparators MUST implement
# the same interface to allow rules_check.py to use them interchangeably.
#
# Required methods:
#   - get_changed_files() -> list[str]
#   - get_created_files() -> list[str]
#   - get_baseline_ref() -> str
#
# DO NOT MODIFY THESE TESTS - They ensure interface compatibility.
# =============================================================================


class TestGitComparatorInterface:
    """
    REQUIREMENTS TEST: Verify all comparators implement GitComparator interface.

    ============================================================================
    WARNING: DO NOT MODIFY THESE TESTS
    ============================================================================

    These tests verify that all comparator classes implement the required
    interface methods. Modifying these tests could result in rules not
    being triggered correctly due to missing or incorrect method signatures.
    """

    def test_compare_to_base_implements_interface(self) -> None:
        """
        REQ-001: CompareToBase MUST implement GitComparator interface.

        DO NOT MODIFY THIS TEST.
        """
        comparator = CompareToBase()
        assert isinstance(comparator, GitComparator)
        assert hasattr(comparator, "get_changed_files")
        assert hasattr(comparator, "get_created_files")
        assert hasattr(comparator, "get_baseline_ref")
        assert callable(comparator.get_changed_files)
        assert callable(comparator.get_created_files)
        assert callable(comparator.get_baseline_ref)

    def test_compare_to_default_tip_implements_interface(self) -> None:
        """
        REQ-001: CompareToDefaultTip MUST implement GitComparator interface.

        DO NOT MODIFY THIS TEST.
        """
        comparator = CompareToDefaultTip()
        assert isinstance(comparator, GitComparator)
        assert hasattr(comparator, "get_changed_files")
        assert hasattr(comparator, "get_created_files")
        assert hasattr(comparator, "get_baseline_ref")
        assert callable(comparator.get_changed_files)
        assert callable(comparator.get_created_files)
        assert callable(comparator.get_baseline_ref)

    def test_compare_to_prompt_implements_interface(self) -> None:
        """
        REQ-001: CompareToPrompt MUST implement GitComparator interface.

        DO NOT MODIFY THIS TEST.
        """
        comparator = CompareToPrompt()
        assert isinstance(comparator, GitComparator)
        assert hasattr(comparator, "get_changed_files")
        assert hasattr(comparator, "get_created_files")
        assert hasattr(comparator, "get_baseline_ref")
        assert callable(comparator.get_changed_files)
        assert callable(comparator.get_created_files)
        assert callable(comparator.get_baseline_ref)


# =============================================================================
# REQ-002: get_comparator() MUST return correct comparator for each mode
# =============================================================================
#
# The get_comparator() factory function is the primary entry point for
# rules_check.py. It MUST return the correct comparator type based on the
# mode parameter to ensure rules are checked against the correct baseline.
#
# DO NOT MODIFY THESE TESTS - They ensure correct factory behavior.
# =============================================================================


class TestGetComparatorFactory:
    """
    REQUIREMENTS TEST: Verify get_comparator() returns correct comparator types.

    ============================================================================
    WARNING: DO NOT MODIFY THESE TESTS
    ============================================================================

    These tests verify that the factory function returns the correct comparator
    for each mode. Modifying these tests could result in rules being checked
    against the wrong baseline.
    """

    def test_returns_compare_to_base_for_base_mode(self) -> None:
        """
        REQ-002: get_comparator("base") MUST return CompareToBase.

        DO NOT MODIFY THIS TEST.
        """
        comparator = get_comparator("base")
        assert isinstance(comparator, CompareToBase)

    def test_returns_compare_to_default_tip_for_default_tip_mode(self) -> None:
        """
        REQ-002: get_comparator("default_tip") MUST return CompareToDefaultTip.

        DO NOT MODIFY THIS TEST.
        """
        comparator = get_comparator("default_tip")
        assert isinstance(comparator, CompareToDefaultTip)

    def test_returns_compare_to_prompt_for_prompt_mode(self) -> None:
        """
        REQ-002: get_comparator("prompt") MUST return CompareToPrompt.

        DO NOT MODIFY THIS TEST.
        """
        comparator = get_comparator("prompt")
        assert isinstance(comparator, CompareToPrompt)

    def test_defaults_to_compare_to_base_for_unknown_mode(self) -> None:
        """
        REQ-002: get_comparator() MUST default to CompareToBase for unknown modes.

        DO NOT MODIFY THIS TEST.
        """
        comparator = get_comparator("unknown_mode")
        assert isinstance(comparator, CompareToBase)


# =============================================================================
# REQ-003: CompareToPrompt.get_created_files() MUST correctly detect new files
# =============================================================================
#
# CRITICAL REQUIREMENT: The get_created_files() method for CompareToPrompt
# MUST accurately detect files that were created AFTER the prompt was submitted.
#
# PRIMARY METHOD: Tree-based comparison using .last_tree_hash
#   - Uses Git plumbing (git write-tree / git diff-tree) for accurate comparison
#   - Captures the complete working directory state at prompt time
#   - Handles all edge cases: modified, new, deleted, staged, unstaged
#
# FALLBACK METHOD: File-list comparison using .last_work_tree
#   - Used when .last_tree_hash doesn't exist (backwards compatibility)
#   - Contains list of files that existed at prompt time
#   - MUST NOT use .last_head_ref (would miss uncommitted files)
#
# This is essential for:
#   - Rules that trigger on newly created files only
#   - Avoiding false positives for pre-existing uncommitted files
#
# DO NOT MODIFY THESE TESTS - They prevent critical bugs in file detection.
# =============================================================================


class TestCreatedFilesDetection:
    """
    REQUIREMENTS TEST: Verify created files detection uses correct comparison.

    ============================================================================
    WARNING: DO NOT MODIFY THESE TESTS
    ============================================================================

    These tests verify that get_created_files() correctly identifies files
    created after the prompt was submitted.

    PRIMARY: Uses tree-based comparison (.last_tree_hash) when available
    FALLBACK: Uses file-list comparison (.last_work_tree) for backwards compat

    The fallback tests below verify the file-based comparison works correctly
    when no tree hash exists. This is critical for correctly identifying files
    created during the current session without false positives for pre-existing
    uncommitted files.
    """

    def test_get_created_files_uses_work_tree_not_head_ref(self, temp_dir: Path) -> None:
        """
        REQ-003: get_created_files() MUST use .last_work_tree, NOT .last_head_ref.

        This test simulates a scenario where:
        - .last_tree_hash does NOT exist (so fallback to file-based comparison)
        - .last_head_ref exists (pointing to a git commit)
        - .last_work_tree exists (with a list of files including uncommitted ones)
        - An uncommitted file (existing_uncommitted.py) was present at prompt time

        The method MUST use .last_work_tree, so existing_uncommitted.py should
        NOT be flagged as "created" (it was in the baseline).

        DO NOT MODIFY THIS TEST.
        """
        ref_file = temp_dir / ".last_head_ref"
        ref_file.write_text("abc123")
        work_tree_file = temp_dir / ".last_work_tree"
        work_tree_file.write_text("existing_uncommitted.py\n")

        with (
            patch("deepwork.core.git_utils._stage_all_changes"),
            patch(
                "deepwork.core.git_utils._get_all_changes_vs_ref",
                return_value={"existing_uncommitted.py", "new_file.py"},
            ),
            patch("deepwork.core.git_utils._get_untracked_files", return_value=set()),
            # No tree hash - tests fallback to file-based comparison
            patch.object(CompareToPrompt, "BASELINE_TREE_PATH", temp_dir / "nonexistent"),
            patch.object(CompareToPrompt, "BASELINE_REF_PATH", ref_file),
            patch.object(CompareToPrompt, "BASELINE_WORK_TREE_PATH", work_tree_file),
        ):
            comparator = CompareToPrompt()
            created = comparator.get_created_files()

            # CRITICAL: existing_uncommitted.py was in .last_work_tree baseline
            # so it MUST NOT be flagged as created
            assert "existing_uncommitted.py" not in created, (
                "CRITICAL BUG: File from .last_work_tree flagged as created! "
                "get_created_files() must use .last_work_tree for comparison, "
                "not .last_head_ref. Pre-existing uncommitted files should not "
                "be flagged as 'created'."
            )

            # new_file.py was NOT in .last_work_tree, so it IS created
            assert "new_file.py" in created


# =============================================================================
# REQ-004: Created files are those NOT present in baseline
# =============================================================================
#
# The definition of "created file" is: a file that exists now but was NOT
# present in the baseline at prompt time. This requirement ensures consistent
# behavior across different scenarios.
#
# DO NOT MODIFY THESE TESTS - They define the contract for created file logic.
# =============================================================================


class TestCreatedFilesDefinition:
    """
    REQUIREMENTS TEST: Verify correct definition of "created files".

    ============================================================================
    WARNING: DO NOT MODIFY THESE TESTS
    ============================================================================

    These tests verify the fundamental definition of what constitutes a
    "created file" - a file that exists now but was NOT present at baseline.
    """

    def test_files_in_baseline_are_not_created(self, temp_dir: Path) -> None:
        """
        REQ-004: Files present in baseline MUST NOT be flagged as created.

        DO NOT MODIFY THIS TEST.
        """
        work_tree_file = temp_dir / ".last_work_tree"
        work_tree_file.write_text("existing.py\n")

        with (
            patch("deepwork.core.git_utils._stage_all_changes"),
            patch(
                "deepwork.core.git_utils._get_all_changes_vs_ref",
                return_value={"existing.py", "new.py"},
            ),
            patch("deepwork.core.git_utils._get_untracked_files", return_value=set()),
            # No tree hash - tests fallback to file-based comparison
            patch.object(CompareToPrompt, "BASELINE_TREE_PATH", temp_dir / "nonexistent"),
            patch.object(CompareToPrompt, "BASELINE_REF_PATH", temp_dir / "nonexistent2"),
            patch.object(CompareToPrompt, "BASELINE_WORK_TREE_PATH", work_tree_file),
        ):
            comparator = CompareToPrompt()
            created = comparator.get_created_files()

            assert "existing.py" not in created, (
                "File in baseline was incorrectly flagged as created"
            )
            assert "new.py" in created

    def test_all_current_files_created_when_no_baseline(self, temp_dir: Path) -> None:
        """
        REQ-004: When no baseline exists, ALL current files are considered created.

        DO NOT MODIFY THIS TEST.
        """
        with (
            patch("deepwork.core.git_utils._stage_all_changes"),
            patch(
                "deepwork.core.git_utils._get_all_changes_vs_ref",
                return_value={"file1.py"},
            ),
            patch(
                "deepwork.core.git_utils._get_untracked_files",
                return_value={"file2.py"},
            ),
            # No tree hash or any baseline files
            patch.object(CompareToPrompt, "BASELINE_TREE_PATH", temp_dir / "nonexistent"),
            patch.object(CompareToPrompt, "BASELINE_REF_PATH", temp_dir / "nonexistent2"),
            patch.object(
                CompareToPrompt,
                "BASELINE_WORK_TREE_PATH",
                temp_dir / "nonexistent3",
            ),
        ):
            comparator = CompareToPrompt()
            created = comparator.get_created_files()

            assert "file1.py" in created, "Staged file should be created when no baseline"
            assert "file2.py" in created, "Untracked file should be created when no baseline"


# =============================================================================
#                    IMPLEMENTATION TESTS
# =============================================================================
#
# The tests below verify implementation details and helper functions.
# These may be modified if the implementation changes, as long as the
# REQUIREMENTS tests above continue to pass.
#
# =============================================================================


class TestParseFileList:
    """Tests for _parse_file_list helper function."""

    def test_parses_newline_separated_files(self) -> None:
        output = "file1.py\nfile2.py\nfile3.py"
        result = _parse_file_list(output)
        assert result == {"file1.py", "file2.py", "file3.py"}

    def test_returns_empty_set_for_empty_string(self) -> None:
        assert _parse_file_list("") == set()

    def test_returns_empty_set_for_whitespace_only(self) -> None:
        assert _parse_file_list("   \n\n  ") == set()

    def test_filters_empty_lines(self) -> None:
        output = "file1.py\n\nfile2.py\n"
        result = _parse_file_list(output)
        assert result == {"file1.py", "file2.py"}

    def test_strips_outer_whitespace_only(self) -> None:
        """Document that _parse_file_list strips outer whitespace but not per-line.

        This is fine because git commands don't output whitespace-padded filenames.
        """
        output = "  file1.py  \n  file2.py  "
        result = _parse_file_list(output)
        # After strip(): "file1.py  \n  file2.py" -> split -> ["file1.py  ", "  file2.py"]
        assert result == {"file1.py  ", "  file2.py"}


class TestGetAllChangesVsRef:
    """Tests for _get_all_changes_vs_ref helper function."""

    def test_returns_files_from_git_diff(self) -> None:
        with patch("deepwork.core.git_utils._run_git") as mock_run:
            mock_run.return_value = MagicMock(stdout="file1.py\nfile2.py\n")
            result = _get_all_changes_vs_ref("abc123")
            assert result == {"file1.py", "file2.py"}
            mock_run.assert_called_once_with("diff", "--name-only", "--cached", "abc123")

    def test_applies_diff_filter(self) -> None:
        with patch("deepwork.core.git_utils._run_git") as mock_run:
            mock_run.return_value = MagicMock(stdout="new_file.py\n")
            result = _get_all_changes_vs_ref("abc123", diff_filter="A")
            assert result == {"new_file.py"}
            mock_run.assert_called_once_with(
                "diff", "--name-only", "--diff-filter=A", "--cached", "abc123"
            )

    def test_returns_empty_set_for_no_changes(self) -> None:
        with patch("deepwork.core.git_utils._run_git") as mock_run:
            mock_run.return_value = MagicMock(stdout="")
            result = _get_all_changes_vs_ref("abc123")
            assert result == set()


class TestCreateTreeFromWorkingDir:
    """Tests for _create_tree_from_working_dir helper function.

    This function creates a tree object from the current working directory
    using a temporary index to avoid touching the actual staging area.
    """

    def test_returns_tree_hash_on_success(self) -> None:
        with patch("deepwork.core.git_utils.subprocess.run") as mock_run:
            # git add -A succeeds, git write-tree returns hash
            mock_run.side_effect = [
                MagicMock(returncode=0),  # git add -A
                MagicMock(stdout="abc123def456\n", returncode=0),  # git write-tree
            ]
            result = _create_tree_from_working_dir()
            assert result == "abc123def456"

    def test_returns_none_on_write_tree_failure(self) -> None:
        with patch("deepwork.core.git_utils.subprocess.run") as mock_run:
            mock_run.side_effect = [
                MagicMock(returncode=0),  # git add -A
                subprocess.CalledProcessError(1, "git write-tree"),
            ]
            result = _create_tree_from_working_dir()
            assert result is None

    def test_uses_temporary_index_file(self) -> None:
        import os

        original_env = os.environ.get("GIT_INDEX_FILE")

        with patch("deepwork.core.git_utils.subprocess.run") as mock_run:
            captured_env = {}

            def capture_env(*args, **kwargs):
                captured_env["GIT_INDEX_FILE"] = os.environ.get("GIT_INDEX_FILE")
                if args[0][1] == "write-tree":
                    return MagicMock(stdout="abc123\n", returncode=0)
                return MagicMock(returncode=0)

            mock_run.side_effect = capture_env
            _create_tree_from_working_dir()

            # Should have used a temp index file during execution
            assert captured_env.get("GIT_INDEX_FILE") is not None
            assert captured_env["GIT_INDEX_FILE"] != original_env

        # Should restore original env after execution
        assert os.environ.get("GIT_INDEX_FILE") == original_env


class TestDiffTrees:
    """Tests for _diff_trees helper function.

    This function compares two tree objects using git diff-tree.
    """

    def test_returns_changed_files(self) -> None:
        with patch("deepwork.core.git_utils._run_git") as mock_run:
            mock_run.return_value = MagicMock(stdout="file1.py\nfile2.py\n")
            result = _diff_trees("tree_a", "tree_b")
            assert result == {"file1.py", "file2.py"}
            mock_run.assert_called_once_with(
                "diff-tree", "--name-only", "-r", "tree_a", "tree_b"
            )

    def test_applies_diff_filter(self) -> None:
        with patch("deepwork.core.git_utils._run_git") as mock_run:
            mock_run.return_value = MagicMock(stdout="new_file.py\n")
            result = _diff_trees("tree_a", "tree_b", diff_filter="A")
            assert result == {"new_file.py"}
            mock_run.assert_called_once_with(
                "diff-tree", "--name-only", "-r", "--diff-filter=A", "tree_a", "tree_b"
            )

    def test_returns_empty_set_for_identical_trees(self) -> None:
        with patch("deepwork.core.git_utils._run_git") as mock_run:
            mock_run.return_value = MagicMock(stdout="")
            result = _diff_trees("same_tree", "same_tree")
            assert result == set()


class TestGetDefaultBranch:
    """Tests for get_default_branch function."""

    def test_returns_main_when_origin_head_points_to_main(self) -> None:
        with patch("deepwork.core.git_utils.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="refs/remotes/origin/main\n", returncode=0)
            assert get_default_branch() == "main"

    def test_returns_master_when_origin_head_points_to_master(self) -> None:
        with patch("deepwork.core.git_utils.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="refs/remotes/origin/master\n", returncode=0)
            assert get_default_branch() == "master"

    def test_falls_back_to_checking_main_branch(self) -> None:
        with patch("deepwork.core.git_utils.subprocess.run") as mock_run:
            # First call fails (symbolic-ref), second succeeds (rev-parse for main)
            mock_run.side_effect = [
                subprocess.CalledProcessError(1, "git"),
                MagicMock(returncode=0),
            ]
            assert get_default_branch() == "main"

    def test_falls_back_to_master_if_main_not_found(self) -> None:
        with patch("deepwork.core.git_utils.subprocess.run") as mock_run:
            # First call fails, second fails (main), third succeeds (master)
            mock_run.side_effect = [
                subprocess.CalledProcessError(1, "git"),
                subprocess.CalledProcessError(1, "git"),
                MagicMock(returncode=0),
            ]
            assert get_default_branch() == "master"

    def test_defaults_to_main_when_nothing_found(self) -> None:
        with patch("deepwork.core.git_utils.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "git")
            assert get_default_branch() == "main"


class TestCompareToBaseImplementation:
    """Implementation tests for CompareToBase comparator."""

    def test_get_fallback_name_returns_base(self) -> None:
        comparator = CompareToBase()
        assert comparator._get_fallback_name() == "base"

    def test_get_baseline_ref_returns_fallback_when_ref_unavailable(self) -> None:
        with patch.object(CompareToBase, "_get_ref", return_value=None):
            comparator = CompareToBase()
            assert comparator.get_baseline_ref() == "base"

    def test_get_baseline_ref_returns_commit_sha(self) -> None:
        with patch.object(CompareToBase, "_get_ref", return_value="abc123def456"):
            comparator = CompareToBase()
            assert comparator.get_baseline_ref() == "abc123def456"

    def test_get_changed_files_returns_empty_when_no_ref(self) -> None:
        with patch.object(CompareToBase, "_get_ref", return_value=None):
            comparator = CompareToBase()
            assert comparator.get_changed_files() == []

    def test_get_created_files_returns_empty_when_no_ref(self) -> None:
        with patch.object(CompareToBase, "_get_ref", return_value=None):
            comparator = CompareToBase()
            assert comparator.get_created_files() == []


class TestCompareToDefaultTipImplementation:
    """Implementation tests for CompareToDefaultTip comparator."""

    def test_get_fallback_name_returns_default_tip(self) -> None:
        comparator = CompareToDefaultTip()
        assert comparator._get_fallback_name() == "default_tip"

    def test_get_baseline_ref_returns_fallback_when_ref_unavailable(self) -> None:
        with patch.object(CompareToDefaultTip, "_get_ref", return_value=None):
            comparator = CompareToDefaultTip()
            assert comparator.get_baseline_ref() == "default_tip"


class TestCompareToPromptImplementation:
    """Implementation tests for CompareToPrompt comparator."""

    def test_get_baseline_ref_returns_prompt_when_no_baseline_file(self, temp_dir: Path) -> None:
        with (
            patch.object(CompareToPrompt, "BASELINE_TREE_PATH", temp_dir / "nonexistent"),
            patch.object(CompareToPrompt, "BASELINE_WORK_TREE_PATH", temp_dir / "nonexistent2"),
        ):
            comparator = CompareToPrompt()
            assert comparator.get_baseline_ref() == "prompt"

    def test_get_baseline_ref_returns_tree_hash_when_tree_exists(self, temp_dir: Path) -> None:
        tree_file = temp_dir / ".last_tree_hash"
        tree_file.write_text("abc123def456789012")

        with (
            patch.object(CompareToPrompt, "BASELINE_TREE_PATH", tree_file),
            patch.object(CompareToPrompt, "BASELINE_WORK_TREE_PATH", temp_dir / "nonexistent"),
        ):
            comparator = CompareToPrompt()
            ref = comparator.get_baseline_ref()
            # Should return short hash (first 12 chars)
            assert ref == "abc123def456"

    def test_get_baseline_ref_falls_back_to_mtime_when_no_tree(self, temp_dir: Path) -> None:
        baseline_file = temp_dir / ".last_work_tree"
        baseline_file.write_text("file1.py\nfile2.py")

        with (
            patch.object(CompareToPrompt, "BASELINE_TREE_PATH", temp_dir / "nonexistent"),
            patch.object(CompareToPrompt, "BASELINE_WORK_TREE_PATH", baseline_file),
        ):
            comparator = CompareToPrompt()
            ref = comparator.get_baseline_ref()
            # Should be a numeric timestamp string (fallback)
            assert ref.isdigit()

    # -------------------------------------------------------------------------
    # Tree-based comparison tests (primary path)
    # -------------------------------------------------------------------------

    def test_get_changed_files_uses_tree_comparison_when_available(self, temp_dir: Path) -> None:
        """When tree hash exists, uses git diff-tree for comparison."""
        tree_file = temp_dir / ".last_tree_hash"
        tree_file.write_text("baseline_tree_abc123")

        with (
            patch.object(CompareToPrompt, "BASELINE_TREE_PATH", tree_file),
            patch(
                "deepwork.core.git_utils._create_tree_from_working_dir",
                return_value="current_tree_def456",
            ),
            patch(
                "deepwork.core.git_utils._diff_trees",
                return_value={"changed.py", "new.py"},
            ) as mock_diff,
        ):
            comparator = CompareToPrompt()
            changed = comparator.get_changed_files()

            # Should use tree-based comparison
            mock_diff.assert_called_once_with("baseline_tree_abc123", "current_tree_def456")
            assert changed == ["changed.py", "new.py"]

    def test_get_created_files_uses_tree_comparison_when_available(self, temp_dir: Path) -> None:
        """When tree hash exists, uses git diff-tree with filter=A for created files."""
        tree_file = temp_dir / ".last_tree_hash"
        tree_file.write_text("baseline_tree_abc123")

        with (
            patch.object(CompareToPrompt, "BASELINE_TREE_PATH", tree_file),
            patch(
                "deepwork.core.git_utils._create_tree_from_working_dir",
                return_value="current_tree_def456",
            ),
            patch(
                "deepwork.core.git_utils._diff_trees",
                return_value={"new.py"},
            ) as mock_diff,
        ):
            comparator = CompareToPrompt()
            created = comparator.get_created_files()

            # Should use tree-based comparison with diff_filter=A
            mock_diff.assert_called_once_with(
                "baseline_tree_abc123", "current_tree_def456", diff_filter="A"
            )
            assert created == ["new.py"]

    # -------------------------------------------------------------------------
    # Fallback behavior tests (when tree hash not available)
    # -------------------------------------------------------------------------

    def test_get_changed_files_falls_back_to_ref_when_no_tree(self, temp_dir: Path) -> None:
        """When no tree hash, falls back to .last_head_ref comparison."""
        ref_file = temp_dir / ".last_head_ref"
        ref_file.write_text("abc123")

        with (
            patch.object(CompareToPrompt, "BASELINE_TREE_PATH", temp_dir / "nonexistent"),
            patch.object(CompareToPrompt, "BASELINE_REF_PATH", ref_file),
            patch("deepwork.core.git_utils._stage_all_changes"),
            patch(
                "deepwork.core.git_utils._get_all_changes_vs_ref",
                return_value={"committed.py", "staged.py"},
            ),
        ):
            comparator = CompareToPrompt()
            changed = comparator.get_changed_files()
            assert "committed.py" in changed
            assert "staged.py" in changed

    def test_get_changed_files_with_no_baseline_files(self, temp_dir: Path) -> None:
        """When no baseline files exist, returns staged changes and untracked files."""
        with (
            patch.object(CompareToPrompt, "BASELINE_TREE_PATH", temp_dir / "nonexistent"),
            patch.object(CompareToPrompt, "BASELINE_REF_PATH", temp_dir / "nonexistent2"),
            patch("deepwork.core.git_utils._stage_all_changes"),
            patch(
                "deepwork.core.git_utils._get_all_changes_vs_ref",
                return_value={"staged.py"},
            ),
            patch(
                "deepwork.core.git_utils._get_untracked_files",
                return_value={"untracked.py"},
            ),
        ):
            comparator = CompareToPrompt()
            changed = comparator.get_changed_files()
            assert "staged.py" in changed
            assert "untracked.py" in changed

class TestRefBasedComparatorIntegration:
    """Integration tests for RefBasedComparator."""

    def test_comparator_caches_ref(self) -> None:
        """Test that ref is cached after first resolution."""
        with patch("deepwork.core.git_utils.get_default_branch", return_value="main"):
            comparator = CompareToBase()

            with patch.object(comparator, "_get_ref", return_value="abc123") as mock_get_ref:
                # Call multiple times
                comparator._resolve_ref()
                comparator._resolve_ref()
                comparator._resolve_ref()

                # Should only call _get_ref once due to caching
                assert mock_get_ref.call_count == 1


class TestCompareToPromptIntegration:
    """Integration tests for CompareToPrompt with file system."""

    def test_full_workflow_with_tree_hash(self, temp_dir: Path) -> None:
        """Test complete workflow with tree-based comparison (primary path)."""
        deepwork_dir = temp_dir / ".deepwork"
        deepwork_dir.mkdir()

        # Write tree hash file (primary method)
        tree_file = deepwork_dir / ".last_tree_hash"
        tree_file.write_text("baseline_tree_abc123")

        with (
            patch.object(CompareToPrompt, "BASELINE_TREE_PATH", tree_file),
            patch(
                "deepwork.core.git_utils._create_tree_from_working_dir",
                return_value="current_tree_def456",
            ),
            patch(
                "deepwork.core.git_utils._diff_trees",
                side_effect=lambda a, b, diff_filter=None: (
                    {"new_file.py"} if diff_filter == "A" else {"new_file.py", "modified.py"}
                ),
            ),
        ):
            comparator = CompareToPrompt()

            changed = comparator.get_changed_files()
            created = comparator.get_created_files()

            # new_file.py should be in both changed and created
            assert "new_file.py" in changed
            assert "modified.py" in changed
            assert "new_file.py" in created
            # modified.py was modified, not created
            assert "modified.py" not in created

    def test_full_workflow_with_fallback_files(self, temp_dir: Path) -> None:
        """Test complete workflow with fallback to file-based comparison."""
        deepwork_dir = temp_dir / ".deepwork"
        deepwork_dir.mkdir()

        # Write legacy baseline files (no tree hash)
        ref_file = deepwork_dir / ".last_head_ref"
        ref_file.write_text("abc123")

        work_tree_file = deepwork_dir / ".last_work_tree"
        work_tree_file.write_text("README.md\n")

        # Mock git operations to simulate a new file being created
        with (
            # No tree hash - forces fallback
            patch.object(CompareToPrompt, "BASELINE_TREE_PATH", temp_dir / "nonexistent"),
            patch.object(CompareToPrompt, "BASELINE_REF_PATH", ref_file),
            patch.object(CompareToPrompt, "BASELINE_WORK_TREE_PATH", work_tree_file),
            patch("deepwork.core.git_utils._stage_all_changes"),
            patch(
                "deepwork.core.git_utils._get_all_changes_vs_ref",
                return_value={"new_file.py"},
            ),
        ):
            comparator = CompareToPrompt()

            changed = comparator.get_changed_files()
            created = comparator.get_created_files()

            # new_file.py should appear in both changed and created
            assert "new_file.py" in changed
            assert "new_file.py" in created
            # README.md was in baseline, so not created
            assert "README.md" not in created
