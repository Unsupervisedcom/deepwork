"""
================================================================================
                    REQUIREMENTS TESTS - DO NOT MODIFY
================================================================================

These tests verify CRITICAL REQUIREMENTS for the Git comparison utilities.
They ensure the git_utils module behaves correctly with respect to:

1. INTERFACE: All comparators implement a common interface
2. FACTORY: get_comparator() returns the correct comparator type
3. CREATED FILES: CompareToPrompt.get_created_files() uses file-based comparison
4. CHANGED FILES: get_changed_files() captures all changes since baseline

WARNING: These tests represent contractual requirements for the rules_check hook.
Modifying these tests may violate expected behavior and could cause rules to
not trigger correctly. If a test fails, fix the IMPLEMENTATION, not the test.

Requirements tested:
  - REQ-001: All comparators MUST implement GitComparator interface
  - REQ-002: get_comparator() MUST return correct comparator for each mode
  - REQ-003: CompareToPrompt.get_created_files() MUST use .last_work_tree
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
# REQ-003: CompareToPrompt.get_created_files() MUST use .last_work_tree
# =============================================================================
#
# CRITICAL REQUIREMENT: The get_created_files() method for CompareToPrompt
# MUST always use file-based comparison (.last_work_tree), NOT git-based
# comparison (.last_head_ref).
#
# Rationale:
#   .last_work_tree contains the actual list of files that existed at prompt
#   time, INCLUDING uncommitted files. Using git-based detection (via
#   .last_head_ref) would incorrectly flag uncommitted files from before the
#   prompt as "created" because they wouldn't exist in the git commit.
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

    These tests verify that get_created_files() uses file-based comparison
    (.last_work_tree) instead of git-based comparison. This is critical for
    correctly identifying files created during the current session.

    A bug was previously introduced where .last_head_ref was preferred over
    .last_work_tree for created file detection, causing pre-existing uncommitted
    files to be incorrectly flagged as "created".
    """

    def test_get_created_files_uses_work_tree_not_head_ref(self, temp_dir: Path) -> None:
        """
        REQ-003: get_created_files() MUST use .last_work_tree, NOT .last_head_ref.

        This test simulates a scenario where:
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
            patch.object(CompareToPrompt, "BASELINE_REF_PATH", temp_dir / "nonexistent"),
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
            patch.object(CompareToPrompt, "BASELINE_REF_PATH", temp_dir / "nonexistent"),
            patch.object(
                CompareToPrompt,
                "BASELINE_WORK_TREE_PATH",
                temp_dir / "nonexistent2",
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
        with patch.object(
            CompareToPrompt,
            "BASELINE_WORK_TREE_PATH",
            temp_dir / "nonexistent",
        ):
            comparator = CompareToPrompt()
            assert comparator.get_baseline_ref() == "prompt"

    def test_get_baseline_ref_returns_mtime_when_baseline_exists(self, temp_dir: Path) -> None:
        baseline_file = temp_dir / ".last_work_tree"
        baseline_file.write_text("file1.py\nfile2.py")

        with patch.object(CompareToPrompt, "BASELINE_WORK_TREE_PATH", baseline_file):
            comparator = CompareToPrompt()
            ref = comparator.get_baseline_ref()
            # Should be a numeric timestamp string
            assert ref.isdigit()

    def test_get_changed_files_with_no_baseline_ref(self, temp_dir: Path) -> None:
        """When no baseline ref exists, returns staged changes and untracked files."""
        with (
            patch("deepwork.core.git_utils._stage_all_changes"),
            patch(
                "deepwork.core.git_utils._get_all_changes_vs_ref",
                return_value={"staged.py"},
            ),
            patch(
                "deepwork.core.git_utils._get_untracked_files",
                return_value={"untracked.py"},
            ),
            patch.object(
                CompareToPrompt,
                "BASELINE_REF_PATH",
                temp_dir / "nonexistent",
            ),
        ):
            comparator = CompareToPrompt()
            changed = comparator.get_changed_files()
            assert "staged.py" in changed
            assert "untracked.py" in changed

    def test_get_changed_files_with_baseline_ref(self, temp_dir: Path) -> None:
        """When baseline ref exists, returns all changes vs that ref."""
        ref_file = temp_dir / ".last_head_ref"
        ref_file.write_text("abc123")

        with (
            patch("deepwork.core.git_utils._stage_all_changes"),
            patch(
                "deepwork.core.git_utils._get_all_changes_vs_ref",
                return_value={"committed.py", "staged.py"},
            ),
            patch.object(CompareToPrompt, "BASELINE_REF_PATH", ref_file),
        ):
            comparator = CompareToPrompt()
            changed = comparator.get_changed_files()
            assert "committed.py" in changed
            assert "staged.py" in changed


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

    def test_full_workflow_with_baseline_files(self, temp_dir: Path) -> None:
        """Test complete workflow with baseline files (mocked git operations)."""
        # Setup baseline files
        deepwork_dir = temp_dir / ".deepwork"
        deepwork_dir.mkdir()

        # Write baseline files
        ref_file = deepwork_dir / ".last_head_ref"
        ref_file.write_text("abc123")

        work_tree_file = deepwork_dir / ".last_work_tree"
        work_tree_file.write_text("README.md\n")

        # Mock git operations to simulate a new file being created and committed
        with (
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
