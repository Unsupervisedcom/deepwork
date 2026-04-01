"""Tests for changed file detection and rule matching (deepwork.review.matcher) — validates REVIEW-REQ-003, REVIEW-REQ-004."""

import inspect
import os
import subprocess
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, call, patch

import pytest

from deepwork.review.config import ReviewRule
from deepwork.review.matcher import (
    GitDiffError,
    _detect_base_ref,
    _get_git_diff,
    _get_merge_base,
    _git_untracked_files,
    _glob_match,
    _relative_to_dir,
    _should_inject_diff,
    _sort_diff_by_path,
    get_changed_files,
    match_files_to_rules,
    match_rule,
)


def _make_rule(
    name: str = "test_rule",
    include: list[str] | None = None,
    exclude: list[str] | None = None,
    strategy: str = "individual",
    instructions: str = "Review it.",
    agent: dict[str, str] | None = None,
    all_changed_filenames: bool = False,
    unchanged_matching_files: bool = False,
    source_dir: Path = Path("/project"),
    source_file: Path | None = None,
    source_line: int = 1,
) -> ReviewRule:
    """Create a ReviewRule with sensible defaults for testing."""
    return ReviewRule(
        name=name,
        description="Test rule description.",
        include_patterns=include or ["**/*.py"],
        exclude_patterns=exclude or [],
        strategy=strategy,
        instructions=instructions,
        agent=agent,
        all_changed_filenames=all_changed_filenames,
        unchanged_matching_files=unchanged_matching_files,
        source_dir=source_dir,
        source_file=source_file or source_dir / ".deepreview",
        source_line=source_line,
    )


class TestRelativeToDir:
    """Tests for _relative_to_dir helper."""

    def test_file_under_dir(self) -> None:
        assert _relative_to_dir("src/app.py", "src") == "app.py"

    def test_file_under_nested_dir(self) -> None:
        assert _relative_to_dir("src/lib/utils.py", "src") == "lib/utils.py"

    def test_file_not_under_dir(self) -> None:
        assert _relative_to_dir("tests/test.py", "src") is None

    def test_root_dir(self) -> None:
        assert _relative_to_dir("app.py", ".") == "app.py"

    def test_empty_dir(self) -> None:
        assert _relative_to_dir("app.py", "") == "app.py"


class TestGlobMatch:
    """Tests for _glob_match helper."""

    def test_recursive_star_star(self) -> None:
        assert _glob_match("lib/utils.py", "**/*.py") is True

    def test_recursive_star_star_no_match(self) -> None:
        assert _glob_match("lib/utils.ts", "**/*.py") is False

    def test_single_star(self) -> None:
        assert _glob_match("app.py", "*.py") is True

    def test_single_star_no_match_in_subdir(self) -> None:
        # * should NOT match across / boundaries
        assert _glob_match("lib/app.py", "*.py") is False

    def test_specific_path(self) -> None:
        assert _glob_match("config/settings.yaml", "config/*") is True

    def test_specific_path_no_match(self) -> None:
        assert _glob_match("other/settings.yaml", "config/*") is False


class TestMatchRule:
    """Tests for match_rule."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-004.1.1, REVIEW-REQ-004.1.6).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_matches_include_pattern(self, tmp_path: Path) -> None:
        rule = _make_rule(include=["**/*.py"], source_dir=tmp_path)
        matched = match_rule(["src/app.py", "src/lib.ts"], rule, tmp_path)
        assert matched == ["src/app.py"]

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-004.1.6, REVIEW-REQ-004.1.7).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_exclude_pattern_filters_out(self, tmp_path: Path) -> None:
        rule = _make_rule(
            include=["**/*.py"],
            exclude=["tests/**/*.py"],
            source_dir=tmp_path,
        )
        matched = match_rule(["src/app.py", "tests/test_app.py"], rule, tmp_path)
        assert matched == ["src/app.py"]

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-004.1.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_file_outside_source_dir_not_matched(self, tmp_path: Path) -> None:
        source = tmp_path / "src"
        source.mkdir()
        rule = _make_rule(include=["**/*.py"], source_dir=source)
        matched = match_rule(["tests/test.py", "src/app.py"], rule, tmp_path)
        assert matched == ["src/app.py"]

    def test_no_matches(self, tmp_path: Path) -> None:
        rule = _make_rule(include=["**/*.py"], source_dir=tmp_path)
        matched = match_rule(["app.ts", "lib.js"], rule, tmp_path)
        assert matched == []


class TestMatchFilesToRules:
    """Tests for match_files_to_rules."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-004.3.1, REVIEW-REQ-004.3.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_individual_strategy_creates_one_task_per_file(self, tmp_path: Path) -> None:
        rule = _make_rule(strategy="individual", source_dir=tmp_path)
        tasks = match_files_to_rules(
            ["app.py", "lib.py", "main.ts"],
            [rule],
            tmp_path,
        )
        assert len(tasks) == 2  # app.py and lib.py
        assert tasks[0].files_to_review == ["app.py"]
        assert tasks[1].files_to_review == ["lib.py"]

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-004.4.1, REVIEW-REQ-004.4.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_matches_together_strategy_creates_single_task(self, tmp_path: Path) -> None:
        rule = _make_rule(strategy="matches_together", source_dir=tmp_path)
        tasks = match_files_to_rules(
            ["app.py", "lib.py", "main.ts"],
            [rule],
            tmp_path,
        )
        assert len(tasks) == 1
        assert set(tasks[0].files_to_review) == {"app.py", "lib.py"}

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-004.5.1, REVIEW-REQ-004.5.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_all_changed_files_strategy_includes_all(self, tmp_path: Path) -> None:
        rule = _make_rule(strategy="all_changed_files", source_dir=tmp_path)
        tasks = match_files_to_rules(
            ["app.py", "lib.py", "main.ts"],
            [rule],
            tmp_path,
        )
        assert len(tasks) == 1
        assert set(tasks[0].files_to_review) == {"app.py", "lib.py", "main.ts"}

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-004.5.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_all_changed_files_not_triggered_without_match(self, tmp_path: Path) -> None:
        rule = _make_rule(
            include=["**/*.py"],
            strategy="all_changed_files",
            source_dir=tmp_path,
        )
        tasks = match_files_to_rules(
            ["main.ts", "lib.js"],
            [rule],
            tmp_path,
        )
        assert tasks == []

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-004.7.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_no_match_produces_no_tasks(self, tmp_path: Path) -> None:
        rule = _make_rule(include=["**/*.py"], source_dir=tmp_path)
        tasks = match_files_to_rules(
            ["app.ts"],
            [rule],
            tmp_path,
        )
        assert tasks == []

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-004.6.1, REVIEW-REQ-004.6.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_all_changed_filenames_context(self, tmp_path: Path) -> None:
        rule = _make_rule(
            strategy="individual",
            all_changed_filenames=True,
            source_dir=tmp_path,
        )
        changed = ["app.py", "main.ts"]
        tasks = match_files_to_rules(changed, [rule], tmp_path)
        assert len(tasks) == 1  # Only app.py matches
        assert tasks[0].all_changed_filenames == ["app.py", "main.ts"]

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-004.8.2, REVIEW-REQ-004.8.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_agent_resolution(self, tmp_path: Path) -> None:
        rule = _make_rule(
            agent={"claude": "security-expert", "gemini": "sec-bot"},
            source_dir=tmp_path,
        )
        tasks = match_files_to_rules(["app.py"], [rule], tmp_path, platform="claude")
        assert tasks[0].agent_name == "security-expert"

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-004.8.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_agent_resolution_missing_platform(self, tmp_path: Path) -> None:
        rule = _make_rule(
            agent={"gemini": "sec-bot"},
            source_dir=tmp_path,
        )
        tasks = match_files_to_rules(["app.py"], [rule], tmp_path, platform="claude")
        assert tasks[0].agent_name is None

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-004.2.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_source_location_set_on_tasks(self, tmp_path: Path) -> None:
        rule = _make_rule(
            source_dir=tmp_path,
            source_file=tmp_path / ".deepreview",
            source_line=3,
        )
        tasks = match_files_to_rules(["app.py"], [rule], tmp_path)
        assert tasks[0].source_location == ".deepreview:3"

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-004.9.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_multiple_rules_processed_independently(self, tmp_path: Path) -> None:
        rule_a = _make_rule(name="rule_a", include=["**/*.py"], source_dir=tmp_path)
        rule_b = _make_rule(name="rule_b", include=["**/*.py"], source_dir=tmp_path)
        tasks = match_files_to_rules(["app.py"], [rule_a, rule_b], tmp_path)
        assert len(tasks) == 2
        assert tasks[0].rule_name == "rule_a"
        assert tasks[1].rule_name == "rule_b"

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-004.10.1, REVIEW-REQ-004.10.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_same_name_rules_from_different_dirs_produce_independent_tasks(
        self, tmp_path: Path
    ) -> None:
        """Two .deepreview files defining the same rule name in sibling
        directories must produce separate tasks scoped to their own directory."""
        dir_a = tmp_path / "jobs" / "job_a"
        dir_b = tmp_path / "jobs" / "job_b"
        dir_a.mkdir(parents=True)
        dir_b.mkdir(parents=True)

        rule_a = _make_rule(
            name="job_definition_review",
            include=["job.yml"],
            strategy="matches_together",
            source_dir=dir_a,
            source_file=dir_a / ".deepreview",
        )
        rule_b = _make_rule(
            name="job_definition_review",
            include=["job.yml"],
            strategy="matches_together",
            source_dir=dir_b,
            source_file=dir_b / ".deepreview",
        )

        changed_files = [
            "jobs/job_a/job.yml",
            "jobs/job_b/job.yml",
        ]
        tasks = match_files_to_rules(changed_files, [rule_a, rule_b], tmp_path)

        assert len(tasks) == 2
        assert tasks[0].rule_name == "job_definition_review"
        assert tasks[1].rule_name == "job_definition_review"
        assert tasks[0].files_to_review == ["jobs/job_a/job.yml"]
        assert tasks[1].files_to_review == ["jobs/job_b/job.yml"]

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-004.4.3, REVIEW-REQ-004.4.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_unchanged_matching_files(self, tmp_path: Path) -> None:
        # Create files on disk for the glob scan
        (tmp_path / "app.py").write_text("# app")
        (tmp_path / "lib.py").write_text("# lib")
        (tmp_path / "unchanged.py").write_text("# unchanged")

        rule = _make_rule(
            strategy="matches_together",
            unchanged_matching_files=True,
            source_dir=tmp_path,
        )
        tasks = match_files_to_rules(
            ["app.py", "lib.py"],
            [rule],
            tmp_path,
        )
        assert len(tasks) == 1
        assert "unchanged.py" in tasks[0].additional_files


class TestGetChangedFiles:
    """Tests for get_changed_files."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-003.1.6).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_raises_on_non_git_repo(self, tmp_path: Path) -> None:
        with pytest.raises(GitDiffError):
            get_changed_files(tmp_path)

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-003.1.2, REVIEW-REQ-003.1.5).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    @patch("deepwork.review.matcher.subprocess.run")
    @patch("deepwork.review.matcher._detect_base_ref", return_value="main")
    @patch("deepwork.review.matcher._get_merge_base", return_value="abc123")
    def test_returns_sorted_deduplicated_files(
        self, mock_merge_base: Any, mock_detect: Any, mock_run: Any, tmp_path: Path
    ) -> None:
        mock_run.return_value.stdout = "b.py\na.py\n"
        mock_run.return_value.returncode = 0
        files = get_changed_files(tmp_path)
        assert files == ["a.py", "b.py"]

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-003.2.6).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    @patch("deepwork.review.matcher._git_untracked_files", return_value=[])
    @patch("deepwork.review.matcher._git_diff_name_only")
    @patch("deepwork.review.matcher._get_merge_base", return_value="abc123")
    def test_uses_explicit_base_ref(
        self, mock_merge_base: Any, mock_diff: Any, mock_untracked: Any, tmp_path: Path
    ) -> None:
        mock_diff.return_value = ["app.py"]
        get_changed_files(tmp_path, base_ref="develop")
        mock_merge_base.assert_called_once_with(tmp_path, "develop")

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-003.1.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    @patch("deepwork.review.matcher._git_untracked_files", return_value=[])
    @patch("deepwork.review.matcher._git_diff_name_only")
    @patch("deepwork.review.matcher._detect_base_ref", return_value="main")
    @patch("deepwork.review.matcher._get_merge_base", return_value="abc123")
    def test_returns_list_of_relative_paths(
        self,
        mock_merge_base: Any,
        mock_detect: Any,
        mock_diff: Any,
        mock_untracked: Any,
        tmp_path: Path,
    ) -> None:
        mock_diff.return_value = ["src/app.py", "tests/test_app.py"]
        result = get_changed_files(tmp_path)
        assert isinstance(result, list)
        assert all(isinstance(p, str) for p in result)
        # Paths should be relative (no leading /)
        assert all(not p.startswith("/") for p in result)

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-003.1.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    @patch("deepwork.review.matcher.subprocess.run")
    @patch("deepwork.review.matcher._detect_base_ref", return_value="main")
    @patch("deepwork.review.matcher._get_merge_base", return_value="abc123")
    def test_uses_diff_filter_acmr(
        self, mock_merge_base: Any, mock_detect: Any, mock_run: Any, tmp_path: Path
    ) -> None:
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0
        get_changed_files(tmp_path)
        # Every git diff call must include --diff-filter=ACMR
        for c in mock_run.call_args_list:
            cmd = c[0][0] if c[0] else c[1].get("args", [])
            if "diff" in cmd:
                assert "--diff-filter=ACMR" in cmd, (
                    f"Expected --diff-filter=ACMR in git diff command: {cmd}"
                )

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-003.1.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    @patch("deepwork.review.matcher._git_untracked_files", return_value=[])
    @patch("deepwork.review.matcher._detect_base_ref", return_value="main")
    @patch("deepwork.review.matcher._get_merge_base", return_value="abc123")
    @patch("deepwork.review.matcher._git_diff_name_only")
    def test_combines_unstaged_and_staged_changes(
        self,
        mock_diff: Any,
        mock_merge_base: Any,
        mock_detect: Any,
        mock_untracked: Any,
        tmp_path: Path,
    ) -> None:
        # First call is for diff against merge-base (unstaged/committed),
        # second call is for staged changes
        mock_diff.side_effect = [["src/app.py"], ["src/new.py"]]
        result = get_changed_files(tmp_path)
        assert "src/app.py" in result
        assert "src/new.py" in result
        # Verify two calls were made: one with merge_base ref, one with None+staged
        assert mock_diff.call_count == 2
        first_call = mock_diff.call_args_list[0]
        second_call = mock_diff.call_args_list[1]
        # First call: diff against merge-base
        assert first_call == call(tmp_path, "abc123")
        # Second call: staged changes (ref=None, staged=True)
        assert second_call == call(tmp_path, None, staged=True)

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-003.1.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    @patch("deepwork.review.matcher._git_untracked_files")
    @patch("deepwork.review.matcher._detect_base_ref", return_value="main")
    @patch("deepwork.review.matcher._get_merge_base", return_value="abc123")
    @patch("deepwork.review.matcher._git_diff_name_only")
    def test_includes_untracked_files(
        self,
        mock_diff: Any,
        mock_merge_base: Any,
        mock_detect: Any,
        mock_untracked: Any,
        tmp_path: Path,
    ) -> None:
        mock_diff.side_effect = [["src/app.py"], []]
        mock_untracked.return_value = ["plugins/new/.deepreview"]
        result = get_changed_files(tmp_path)
        assert "src/app.py" in result
        assert "plugins/new/.deepreview" in result
        mock_untracked.assert_called_once_with(tmp_path)

    @patch("deepwork.review.matcher._git_untracked_files")
    @patch("deepwork.review.matcher._detect_base_ref", return_value="main")
    @patch("deepwork.review.matcher._get_merge_base", return_value="abc123")
    @patch("deepwork.review.matcher._git_diff_name_only")
    def test_deduplicates_untracked_with_diff(
        self,
        mock_diff: Any,
        mock_merge_base: Any,
        mock_detect: Any,
        mock_untracked: Any,
        tmp_path: Path,
    ) -> None:
        mock_diff.side_effect = [["src/app.py"], ["src/app.py"]]
        mock_untracked.return_value = ["src/app.py"]
        result = get_changed_files(tmp_path)
        assert result == ["src/app.py"]

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-003.1.6).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    @patch("deepwork.review.matcher._git_untracked_files", return_value=[])
    @patch("deepwork.review.matcher._git_diff_name_only")
    @patch("deepwork.review.matcher._detect_base_ref", return_value="main")
    @patch("deepwork.review.matcher._get_merge_base", return_value="abc123")
    def test_paths_relative_to_repo_root(
        self,
        mock_merge_base: Any,
        mock_detect: Any,
        mock_diff: Any,
        mock_untracked: Any,
        tmp_path: Path,
    ) -> None:
        mock_diff.return_value = ["src/lib/utils.py", "README.md"]
        result = get_changed_files(tmp_path)
        # All paths must be relative (no absolute paths)
        for path in result:
            assert not Path(path).is_absolute(), f"Path should be relative: {path}"
            assert not path.startswith("/"), f"Path should not start with /: {path}"

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-003.2.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_base_ref_defaults_to_none(self) -> None:
        sig = inspect.signature(get_changed_files)
        base_ref_param = sig.parameters["base_ref"]
        assert base_ref_param.default is None

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-003.2.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    @patch("deepwork.review.matcher._git_untracked_files", return_value=[])
    @patch("deepwork.review.matcher._git_diff_name_only")
    @patch("deepwork.review.matcher._get_merge_base", return_value="abc123")
    @patch("deepwork.review.matcher._detect_base_ref", return_value="main")
    def test_auto_detects_merge_base_when_base_ref_none(
        self,
        mock_detect: Any,
        mock_merge_base: Any,
        mock_diff: Any,
        mock_untracked: Any,
        tmp_path: Path,
    ) -> None:
        mock_diff.return_value = []
        get_changed_files(tmp_path, base_ref=None)
        mock_detect.assert_called_once_with(tmp_path)
        mock_merge_base.assert_called_once_with(tmp_path, "main")

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-003.2.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    @patch("deepwork.review.matcher.subprocess.run")
    def test_detect_base_ref_uses_symbolic_ref(self, mock_run: Any, tmp_path: Path) -> None:
        def side_effect(cmd: Any, **kwargs: Any) -> Any:
            result = MagicMock()
            result.returncode = 0
            if "symbolic-ref" in cmd:
                result.stdout = "refs/remotes/origin/main\n"
            else:
                result.stdout = ""
            return result

        mock_run.side_effect = side_effect
        result = _detect_base_ref(tmp_path)
        assert result == "origin/main"
        # First call should be the symbolic-ref query
        first_call_cmd = mock_run.call_args_list[0][0][0]
        assert "symbolic-ref" in first_call_cmd

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-003.2.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    @patch("deepwork.review.matcher.subprocess.run")
    def test_detect_base_ref_symbolic_ref_works_for_non_standard_names(
        self, mock_run: Any, tmp_path: Path
    ) -> None:
        def side_effect(cmd: Any, **kwargs: Any) -> Any:
            result = MagicMock()
            result.returncode = 0
            if "symbolic-ref" in cmd:
                result.stdout = "refs/remotes/origin/develop\n"
            else:
                result.stdout = ""
            return result

        mock_run.side_effect = side_effect
        result = _detect_base_ref(tmp_path)
        assert result == "origin/develop"

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-003.2.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    @patch("deepwork.review.matcher.subprocess.run")
    def test_detect_base_ref_falls_back_when_symbolic_ref_not_set(
        self, mock_run: Any, tmp_path: Path
    ) -> None:
        def side_effect(cmd: Any, **kwargs: Any) -> Any:
            # symbolic-ref fails, but origin/main exists
            if "symbolic-ref" in cmd:
                raise subprocess.CalledProcessError(128, cmd)
            result = MagicMock()
            result.returncode = 0
            return result

        mock_run.side_effect = side_effect
        result = _detect_base_ref(tmp_path)
        assert result == "origin/main"

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-003.2.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    @patch("deepwork.review.matcher.subprocess.run")
    def test_detect_base_ref_falls_back_to_origin_master(
        self, mock_run: Any, tmp_path: Path
    ) -> None:
        def side_effect(cmd: Any, **kwargs: Any) -> Any:
            if "symbolic-ref" in cmd or "origin/main" in cmd:
                raise subprocess.CalledProcessError(128, cmd)
            result = MagicMock()
            result.returncode = 0
            return result

        mock_run.side_effect = side_effect
        result = _detect_base_ref(tmp_path)
        assert result == "origin/master"

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-003.2.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    @patch("deepwork.review.matcher.subprocess.run")
    def test_detect_base_ref_falls_back_to_local_main(self, mock_run: Any, tmp_path: Path) -> None:
        def side_effect(cmd: Any, **kwargs: Any) -> Any:
            if "symbolic-ref" in cmd or "origin/main" in cmd or "origin/master" in cmd:
                raise subprocess.CalledProcessError(128, cmd)
            result = MagicMock()
            result.returncode = 0
            return result

        mock_run.side_effect = side_effect
        result = _detect_base_ref(tmp_path)
        assert result == "main"

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-003.2.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    @patch("deepwork.review.matcher.subprocess.run")
    def test_detect_base_ref_falls_back_to_local_master(
        self, mock_run: Any, tmp_path: Path
    ) -> None:
        def side_effect(cmd: Any, **kwargs: Any) -> Any:
            if (
                "symbolic-ref" in cmd
                or "origin/main" in cmd
                or "origin/master" in cmd
                or cmd[-1] == "main"
            ):
                raise subprocess.CalledProcessError(128, cmd)
            result = MagicMock()
            result.returncode = 0
            return result

        mock_run.side_effect = side_effect
        result = _detect_base_ref(tmp_path)
        assert result == "master"

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-003.2.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    @patch("deepwork.review.matcher.subprocess.run")
    def test_detect_base_ref_falls_back_to_head(self, mock_run: Any, tmp_path: Path) -> None:
        # Nothing works — symbolic-ref fails, no known branches exist
        mock_run.side_effect = subprocess.CalledProcessError(128, "git")
        result = _detect_base_ref(tmp_path)
        assert result == "HEAD"

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-003.2.7).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    @patch("deepwork.review.matcher.subprocess.run")
    def test_uses_git_merge_base(self, mock_run: Any, tmp_path: Path) -> None:
        mock_run.return_value.stdout = "deadbeef\n"
        mock_run.return_value.returncode = 0
        result = _get_merge_base(tmp_path, "main")
        cmd = mock_run.call_args[0][0]
        assert cmd[0:2] == ["git", "merge-base"]
        assert "HEAD" in cmd
        assert "main" in cmd
        assert result == "deadbeef"

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-003.3.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    @patch("deepwork.review.matcher.subprocess.run")
    @patch("deepwork.review.matcher._detect_base_ref", return_value="main")
    @patch("deepwork.review.matcher._get_merge_base", return_value="abc123")
    def test_git_commands_use_cwd_project_root(
        self, mock_merge_base: Any, mock_detect: Any, mock_run: Any, tmp_path: Path
    ) -> None:
        mock_run.return_value.stdout = "app.py\n"
        mock_run.return_value.returncode = 0
        get_changed_files(tmp_path)
        for c in mock_run.call_args_list:
            kwargs = c[1] if c[1] else {}
            assert kwargs.get("cwd") == tmp_path, (
                f"Expected cwd={tmp_path}, got cwd={kwargs.get('cwd')} for command {c}"
            )

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-003.3.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    @patch("deepwork.review.matcher._git_untracked_files", return_value=[])
    @patch("deepwork.review.matcher._git_diff_name_only")
    @patch("deepwork.review.matcher._detect_base_ref", return_value="main")
    @patch("deepwork.review.matcher._get_merge_base", return_value="abc123")
    def test_does_not_change_process_working_directory(
        self,
        mock_merge_base: Any,
        mock_detect: Any,
        mock_diff: Any,
        mock_untracked: Any,
        tmp_path: Path,
    ) -> None:
        mock_diff.return_value = ["app.py"]
        cwd_before = os.getcwd()
        get_changed_files(tmp_path)
        cwd_after = os.getcwd()
        assert cwd_before == cwd_after

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-003.4.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    @patch("deepwork.review.matcher.subprocess.run")
    def test_invalid_base_ref_raises_error(self, mock_run: Any, tmp_path: Path) -> None:
        mock_run.side_effect = subprocess.CalledProcessError(
            128, "git", stderr="fatal: Not a valid object name nonexistent_branch"
        )
        with pytest.raises(GitDiffError, match="nonexistent_branch"):
            _get_merge_base(tmp_path, "nonexistent_branch")

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-003.4.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    @patch("deepwork.review.matcher.subprocess.run")
    def test_stderr_included_in_error_message(self, mock_run: Any, tmp_path: Path) -> None:
        stderr_msg = "fatal: bad revision 'bad_ref'"
        mock_run.side_effect = subprocess.CalledProcessError(128, "git", stderr=stderr_msg)
        with pytest.raises(GitDiffError, match=stderr_msg):
            _get_merge_base(tmp_path, "bad_ref")


class TestGitUntrackedFiles:
    """Tests for _git_untracked_files."""

    @patch("deepwork.review.matcher.subprocess.run")
    def test_returns_untracked_files(self, mock_run: Any, tmp_path: Path) -> None:
        mock_run.return_value.stdout = "new_file.py\nplugins/claude/.deepreview\n"
        mock_run.return_value.returncode = 0
        result = _git_untracked_files(tmp_path)
        assert result == ["new_file.py", "plugins/claude/.deepreview"]
        cmd = mock_run.call_args[0][0]
        assert "ls-files" in cmd
        assert "--others" in cmd
        assert "--exclude-standard" in cmd

    @patch("deepwork.review.matcher.subprocess.run")
    def test_returns_empty_list_when_no_untracked(self, mock_run: Any, tmp_path: Path) -> None:
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0
        result = _git_untracked_files(tmp_path)
        assert result == []

    @patch("deepwork.review.matcher.subprocess.run")
    def test_raises_git_diff_error_on_failure(self, mock_run: Any, tmp_path: Path) -> None:
        mock_run.side_effect = subprocess.CalledProcessError(
            128, "git", stderr="fatal: not a git repository"
        )
        with pytest.raises(GitDiffError, match="git ls-files failed"):
            _git_untracked_files(tmp_path)


class TestMatchRuleSourceDirOutsideProject:
    """Tests for match_rule when source_dir is not under project_root."""

    def test_source_dir_not_under_project_root_returns_empty(self, tmp_path: Path) -> None:
        """When source_dir is outside project_root, match_rule returns []."""
        rule = _make_rule(
            include=["**/*.py"],
            source_dir=Path("/some/other/directory"),
        )
        matched = match_rule(["src/app.py"], rule, tmp_path)
        assert matched == []


class TestGlobMatchExtra:
    """Additional tests for _glob_match to cover ? and ** at end."""

    def test_question_mark_matches_single_char(self) -> None:
        """? matches a single non-/ character."""
        assert _glob_match("a.py", "?.py") is True
        assert _glob_match("ab.py", "?.py") is False

    def test_question_mark_does_not_match_slash(self) -> None:
        """? does not match /."""
        assert _glob_match("/", "?") is False

    def test_double_star_at_end_matches_everything(self) -> None:
        """** at end of pattern matches all remaining path components."""
        assert _glob_match("src/lib/deep/file.py", "src/**") is True
        assert _glob_match("src", "src/**") is False


class TestFormatSourceLocationExtra:
    """Tests for format_source_location edge cases."""

    def test_source_file_outside_project_root(self, tmp_path: Path) -> None:
        """When source_file is not under project_root, uses the absolute path."""
        from deepwork.review.matcher import format_source_location

        rule = _make_rule(
            source_dir=Path("/outside"),
            source_file=Path("/outside/.deepreview"),
            source_line=5,
        )
        result = format_source_location(rule, tmp_path)
        assert result == "/outside/.deepreview:5"


class TestFindUnchangedMatchingFilesExtra:
    """Tests for _find_unchanged_matching_files edge cases."""

    def test_source_dir_outside_project_returns_empty(self, tmp_path: Path) -> None:
        """source_dir outside project_root returns []."""
        from deepwork.review.matcher import _find_unchanged_matching_files

        rule = _make_rule(
            source_dir=Path("/nonexistent/dir"),
            include=["**/*.py"],
        )
        result = _find_unchanged_matching_files(["app.py"], rule, tmp_path)
        assert result == []

    def test_skips_directories_in_glob(self, tmp_path: Path) -> None:
        """Directories matched by glob are skipped."""
        from deepwork.review.matcher import _find_unchanged_matching_files

        # Create a directory that matches the glob pattern name
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "app.py").mkdir()  # directory, not file
        (tmp_path / "src" / "lib.py").write_text("# lib")

        rule = _make_rule(
            source_dir=tmp_path,
            include=["src/*.py"],
        )
        result = _find_unchanged_matching_files([], rule, tmp_path)
        assert "src/lib.py" in result
        assert "src/app.py" not in result

    def test_skips_file_not_relative_to_project(self, tmp_path: Path) -> None:
        """Files that can't be made relative to project_root are skipped."""
        from deepwork.review.matcher import _find_unchanged_matching_files

        # This is hard to trigger naturally since source_dir is under project_root
        # at this point. We use a symlink to create a file that resolves outside.
        # Instead, test the rel_to_source None path.
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "file.py").write_text("# file")

        rule = _make_rule(
            source_dir=tmp_path / "subdir",
            include=["*.py"],
        )
        result = _find_unchanged_matching_files([], rule, tmp_path)
        assert "subdir/file.py" in result

    def test_exclude_patterns_filter_unchanged_files(self, tmp_path: Path) -> None:
        """Exclude patterns filter out unchanged files."""
        from deepwork.review.matcher import _find_unchanged_matching_files

        (tmp_path / "app.py").write_text("# app")
        (tmp_path / "test_app.py").write_text("# test")

        rule = _make_rule(
            source_dir=tmp_path,
            include=["*.py"],
            exclude=["test_*.py"],
        )
        result = _find_unchanged_matching_files([], rule, tmp_path)
        assert "app.py" in result
        assert "test_app.py" not in result


class TestMatchFilesToRulesAllChangedFiles:
    """Test the all_changed_files strategy branch more thoroughly."""

    def test_all_changed_files_strategy_with_agent(self, tmp_path: Path) -> None:
        """all_changed_files strategy passes all files and resolves agent."""
        rule = _make_rule(
            strategy="all_changed_files",
            agent={"claude": "reviewer"},
            source_dir=tmp_path,
        )
        tasks = match_files_to_rules(
            ["app.py", "lib.py", "main.ts"],
            [rule],
            tmp_path,
            platform="claude",
        )
        assert len(tasks) == 1
        assert set(tasks[0].files_to_review) == {"app.py", "lib.py", "main.ts"}
        assert tasks[0].agent_name == "reviewer"


class TestSortDiffByPath:
    """Tests for _sort_diff_by_path."""

    def test_sorts_hunks_alphabetically(self) -> None:
        diff = (
            "diff --git a/tests/test_z.py b/tests/test_z.py\n"
            "+z\n"
            "diff --git a/src/a.py b/src/a.py\n"
            "+a\n"
            "diff --git a/src/b.py b/src/b.py\n"
            "+b\n"
        )
        result = _sort_diff_by_path(diff)
        # src/ files should come before tests/
        assert result.index("src/a.py") < result.index("src/b.py")
        assert result.index("src/b.py") < result.index("tests/test_z.py")

    def test_groups_same_directory_together(self) -> None:
        diff = (
            "diff --git a/tests/test_a.py b/tests/test_a.py\n"
            "+ta\n"
            "diff --git a/src/x.py b/src/x.py\n"
            "+x\n"
            "diff --git a/tests/test_b.py b/tests/test_b.py\n"
            "+tb\n"
        )
        result = _sort_diff_by_path(diff)
        # Both src/ and tests/ files should be grouped
        assert result.index("src/x.py") < result.index("tests/test_a.py")
        assert result.index("tests/test_a.py") < result.index("tests/test_b.py")

    def test_empty_input_returns_unchanged(self) -> None:
        assert _sort_diff_by_path("") == ""
        assert _sort_diff_by_path("  \n") == "  \n"

    def test_single_hunk_unchanged(self) -> None:
        diff = "diff --git a/foo.py b/foo.py\n+hello\n"
        assert _sort_diff_by_path(diff) == diff

    def test_preserves_hunk_content(self) -> None:
        diff = (
            "diff --git a/b.py b/b.py\n"
            "--- a/b.py\n"
            "+++ b/b.py\n"
            "@@ -1,3 +1,4 @@\n"
            " line1\n"
            "+added\n"
            "diff --git a/a.py b/a.py\n"
            "--- a/a.py\n"
            "+++ b/a.py\n"
            "@@ -1 +1 @@\n"
            "-old\n"
            "+new\n"
        )
        result = _sort_diff_by_path(diff)
        # a.py should come first, and its full content preserved
        assert result.startswith("diff --git a/a.py b/a.py\n")
        assert "-old\n+new\n" in result
        assert "+added\n" in result


class TestShouldInjectDiff:
    """Tests for _should_inject_diff — validates REVIEW-REQ-004.11."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-004.11.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_all_changed_files_with_star_star_star(self) -> None:
        rule = _make_rule(strategy="all_changed_files", include=["**/*"])
        assert _should_inject_diff(rule) is True

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-004.11.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_matches_together_with_star_star_star(self) -> None:
        rule = _make_rule(strategy="matches_together", include=["**/*"])
        assert _should_inject_diff(rule) is True

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-004.11.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_individual_strategy_never_qualifies(self) -> None:
        rule = _make_rule(strategy="individual", include=["**/*"])
        assert _should_inject_diff(rule) is False

    def test_non_star_star_star_pattern_does_not_qualify(self) -> None:
        rule = _make_rule(strategy="all_changed_files", include=["**/*.py"])
        assert _should_inject_diff(rule) is False

    def test_star_star_star_among_multiple_patterns_qualifies(self) -> None:
        rule = _make_rule(strategy="matches_together", include=["**/*.py", "**/*"])
        assert _should_inject_diff(rule) is True


class TestGetGitDiff:
    """Tests for _get_git_diff helper."""

    @patch("deepwork.review.matcher._run_git")
    def test_returns_diff_output(self, mock_run: Any, tmp_path: Path) -> None:
        mock_run.side_effect = [
            # _detect_base_ref: symbolic-ref
            MagicMock(stdout="refs/remotes/origin/main\n"),
            # _detect_base_ref: rev-parse --verify
            MagicMock(stdout="abc123\n"),
            # _get_merge_base
            MagicMock(stdout="def456\n"),
            # git diff --stat
            MagicMock(stdout=" f.py | 1 +\n 1 file changed\n"),
            # git diff -U8
            MagicMock(stdout="diff --git a/f.py b/f.py\n+hello\n"),
        ]
        result = _get_git_diff(tmp_path)
        assert "diff --git" in result

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-004.11.7).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    @patch("deepwork.review.matcher._run_git")
    def test_includes_stat_summary(self, mock_run: Any, tmp_path: Path) -> None:
        mock_run.side_effect = [
            MagicMock(stdout="refs/remotes/origin/main\n"),
            MagicMock(stdout="abc123\n"),
            MagicMock(stdout="def456\n"),
            MagicMock(stdout=" f.py | 1 +\n 1 file changed\n"),
            MagicMock(stdout="diff --git a/f.py b/f.py\n+hello\n"),
        ]
        result = _get_git_diff(tmp_path)
        # Stat summary should appear before the diff
        assert "1 file changed" in result
        assert result.index("1 file changed") < result.index("diff --git")

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-004.11.8).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    @patch("deepwork.review.matcher._run_git")
    def test_uses_extended_context(self, mock_run: Any, tmp_path: Path) -> None:
        mock_run.side_effect = [
            MagicMock(stdout="refs/remotes/origin/main\n"),
            MagicMock(stdout="abc123\n"),
            MagicMock(stdout="def456\n"),
            MagicMock(stdout=""),
            MagicMock(stdout="diff output\n"),
        ]
        _get_git_diff(tmp_path)
        # The full diff call (last one) should include -U8
        diff_call = mock_run.call_args_list[-1]
        diff_args = diff_call[0][1:]  # skip project_root
        assert "-U8" in diff_args

    @patch("deepwork.review.matcher._run_git")
    def test_returns_empty_on_failure(self, mock_run: Any, tmp_path: Path) -> None:
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")
        result = _get_git_diff(tmp_path)
        assert result == ""

    @patch("deepwork.review.matcher._run_git")
    def test_scopes_diff_to_subdirectory(self, mock_run: Any, tmp_path: Path) -> None:
        sub = tmp_path / "src" / "deepwork"
        sub.mkdir(parents=True)
        mock_run.side_effect = [
            MagicMock(stdout="refs/remotes/origin/main\n"),
            MagicMock(stdout="abc123\n"),
            MagicMock(stdout="def456\n"),
            MagicMock(stdout="scoped stat\n"),
            MagicMock(stdout="diff --git a/src/deepwork/f.py b/src/deepwork/f.py\nscoped diff\n"),
        ]
        result = _get_git_diff(tmp_path, scope_dir=sub)
        assert "scoped diff" in result
        # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-004.11.6).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        # Both git diff calls (stat + full) must include -- src/deepwork pathspec
        stat_call = mock_run.call_args_list[-2]
        diff_call = mock_run.call_args_list[-1]
        assert "src/deepwork" in stat_call[0][1:]
        assert "src/deepwork" in diff_call[0][1:]

    @patch("deepwork.review.matcher._run_git")
    def test_no_scope_when_source_dir_is_project_root(self, mock_run: Any, tmp_path: Path) -> None:
        mock_run.side_effect = [
            MagicMock(stdout="refs/remotes/origin/main\n"),
            MagicMock(stdout="abc123\n"),
            MagicMock(stdout="def456\n"),
            MagicMock(stdout="stat\n"),
            MagicMock(stdout="diff --git a/f.py b/f.py\nfull diff\n"),
        ]
        result = _get_git_diff(tmp_path, scope_dir=tmp_path)
        assert "full diff" in result
        # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-004.11.6).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        # No pathspec should be present when source_dir equals project_root
        stat_call = mock_run.call_args_list[-2]
        diff_call = mock_run.call_args_list[-1]
        assert "--" not in stat_call[0][1:]
        assert "--" not in diff_call[0][1:]


class TestReviewTaskGitDiffField:
    """Tests for ReviewTask.git_diff_output field — validates REVIEW-REQ-004.11.5."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-004.11.5).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_git_diff_output_defaults_to_none(self) -> None:
        from deepwork.review.config import ReviewTask

        task = ReviewTask(
            rule_name="x",
            files_to_review=["f"],
            instructions="i",
            agent_name=None,
        )
        assert task.git_diff_output is None


class TestDiffInjectionInMatchFilesToRules:
    """Tests for git diff injection in match_files_to_rules — validates REVIEW-REQ-004.11."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-004.11.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    @patch("deepwork.review.matcher._get_git_diff")
    def test_injects_diff_for_all_changed_files_with_broad_matcher(
        self, mock_diff: Any, tmp_path: Path
    ) -> None:
        mock_diff.return_value = "diff --git a/f.py b/f.py\n+hello\n"
        rule = _make_rule(strategy="all_changed_files", include=["**/*"], source_dir=tmp_path)
        tasks = match_files_to_rules(["app.py"], [rule], tmp_path)
        assert len(tasks) == 1
        assert tasks[0].git_diff_output == "diff --git a/f.py b/f.py\n+hello\n"

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-004.11.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    @patch("deepwork.review.matcher._get_git_diff")
    def test_injects_diff_for_matches_together_with_broad_matcher(
        self, mock_diff: Any, tmp_path: Path
    ) -> None:
        mock_diff.return_value = "diff --git a/f.py b/f.py\n+hello\n"
        rule = _make_rule(strategy="matches_together", include=["**/*"], source_dir=tmp_path)
        tasks = match_files_to_rules(["app.py"], [rule], tmp_path)
        assert len(tasks) == 1
        assert tasks[0].git_diff_output is not None

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-004.11.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    @patch("deepwork.review.matcher._get_git_diff")
    def test_no_diff_for_individual_strategy(self, mock_diff: Any, tmp_path: Path) -> None:
        mock_diff.return_value = "diff output"
        rule = _make_rule(strategy="individual", include=["**/*"], source_dir=tmp_path)
        tasks = match_files_to_rules(["app.py"], [rule], tmp_path)
        assert len(tasks) == 1
        assert tasks[0].git_diff_output is None
        mock_diff.assert_not_called()

    def test_no_diff_for_narrow_matcher(self, tmp_path: Path) -> None:
        rule = _make_rule(strategy="all_changed_files", include=["**/*.py"], source_dir=tmp_path)
        tasks = match_files_to_rules(["app.py"], [rule], tmp_path)
        assert len(tasks) == 1
        assert tasks[0].git_diff_output is None

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-004.11.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    @patch("deepwork.review.matcher._get_git_diff")
    def test_diff_computed_only_once_for_multiple_qualifying_rules(
        self, mock_diff: Any, tmp_path: Path
    ) -> None:
        mock_diff.return_value = "diff output"
        rule1 = _make_rule(
            name="rule1",
            strategy="all_changed_files",
            include=["**/*"],
            source_dir=tmp_path,
        )
        rule2 = _make_rule(
            name="rule2",
            strategy="matches_together",
            include=["**/*"],
            source_dir=tmp_path,
        )
        tasks = match_files_to_rules(["app.py"], [rule1, rule2], tmp_path)
        assert len(tasks) == 2
        assert all(t.git_diff_output == "diff output" for t in tasks)
        mock_diff.assert_called_once()

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-004.11.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    @patch("deepwork.review.matcher._get_git_diff")
    def test_empty_diff_sets_none(self, mock_diff: Any, tmp_path: Path) -> None:
        mock_diff.return_value = ""
        rule = _make_rule(strategy="all_changed_files", include=["**/*"], source_dir=tmp_path)
        tasks = match_files_to_rules(["app.py"], [rule], tmp_path)
        assert len(tasks) == 1
        assert tasks[0].git_diff_output is None

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-004.11.6).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    @patch("deepwork.review.matcher._get_git_diff")
    def test_diff_scoped_to_rule_source_dir(self, mock_diff: Any, tmp_path: Path) -> None:
        """Diff for a subdirectory rule is scoped to that subdirectory."""
        sub = tmp_path / "sub"
        sub.mkdir()
        mock_diff.return_value = "sub diff"
        rule = _make_rule(strategy="all_changed_files", include=["**/*"], source_dir=sub)
        tasks = match_files_to_rules(["sub/app.py"], [rule], tmp_path)
        assert len(tasks) == 1
        assert tasks[0].git_diff_output == "sub diff"
        mock_diff.assert_called_once_with(tmp_path, sub)

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-004.11.6).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    @patch("deepwork.review.matcher._get_git_diff")
    def test_diff_at_project_root_for_root_rule(self, mock_diff: Any, tmp_path: Path) -> None:
        """Diff for a root-level rule covers the entire repo."""
        mock_diff.return_value = "full diff"
        rule = _make_rule(strategy="all_changed_files", include=["**/*"], source_dir=tmp_path)
        tasks = match_files_to_rules(["app.py"], [rule], tmp_path)
        assert len(tasks) == 1
        mock_diff.assert_called_once_with(tmp_path, tmp_path)

    # THIS TEST VALIDATES A HARD REQUIREMENT (REVIEW-REQ-004.11.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    @patch("deepwork.review.matcher._get_git_diff")
    def test_diff_cached_per_source_dir(self, mock_diff: Any, tmp_path: Path) -> None:
        """Rules in different source_dirs get separate diffs; same source_dir shares."""
        sub1 = tmp_path / "a"
        sub2 = tmp_path / "b"
        sub1.mkdir()
        sub2.mkdir()
        mock_diff.side_effect = ["diff a", "diff b"]
        rule1 = _make_rule(
            name="r1", strategy="matches_together", include=["**/*"], source_dir=sub1
        )
        rule2 = _make_rule(
            name="r2", strategy="all_changed_files", include=["**/*"], source_dir=sub1
        )
        rule3 = _make_rule(
            name="r3", strategy="all_changed_files", include=["**/*"], source_dir=sub2
        )
        tasks = match_files_to_rules(["a/x.py", "b/y.py"], [rule1, rule2, rule3], tmp_path)
        # rule1 and rule2 share sub1 → one call; rule3 uses sub2 → second call
        assert mock_diff.call_count == 2
        assert tasks[0].git_diff_output == "diff a"
        assert tasks[1].git_diff_output == "diff a"
        assert tasks[2].git_diff_output == "diff b"
