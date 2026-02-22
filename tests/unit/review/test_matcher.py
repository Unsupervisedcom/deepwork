"""Tests for changed file detection and rule matching (deepwork.review.matcher)."""

from pathlib import Path
from unittest.mock import patch

import pytest

from deepwork.review.config import ReviewRule
from deepwork.review.matcher import (
    GitDiffError,
    _glob_match,
    _glob_to_regex,
    _match_rule,
    _relative_to_dir,
    get_changed_files,
    match_files_to_rules,
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
    """Tests for _match_rule."""

    # REQ-004.1.1, REQ-004.1.6
    def test_matches_include_pattern(self, tmp_path: Path) -> None:
        rule = _make_rule(include=["**/*.py"], source_dir=tmp_path)
        matched = _match_rule(["src/app.py", "src/lib.ts"], rule, tmp_path)
        assert matched == ["src/app.py"]

    # REQ-004.1.6, REQ-004.1.7
    def test_exclude_pattern_filters_out(self, tmp_path: Path) -> None:
        rule = _make_rule(
            include=["**/*.py"],
            exclude=["tests/**/*.py"],
            source_dir=tmp_path,
        )
        matched = _match_rule(
            ["src/app.py", "tests/test_app.py"], rule, tmp_path
        )
        assert matched == ["src/app.py"]

    # REQ-004.1.2
    def test_file_outside_source_dir_not_matched(self, tmp_path: Path) -> None:
        source = tmp_path / "src"
        source.mkdir()
        rule = _make_rule(include=["**/*.py"], source_dir=source)
        matched = _match_rule(["tests/test.py", "src/app.py"], rule, tmp_path)
        assert matched == ["src/app.py"]

    def test_no_matches(self, tmp_path: Path) -> None:
        rule = _make_rule(include=["**/*.py"], source_dir=tmp_path)
        matched = _match_rule(["app.ts", "lib.js"], rule, tmp_path)
        assert matched == []


class TestMatchFilesToRules:
    """Tests for match_files_to_rules."""

    # REQ-004.3.1, REQ-004.3.2
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

    # REQ-004.4.1, REQ-004.4.2
    def test_matches_together_strategy_creates_single_task(self, tmp_path: Path) -> None:
        rule = _make_rule(strategy="matches_together", source_dir=tmp_path)
        tasks = match_files_to_rules(
            ["app.py", "lib.py", "main.ts"],
            [rule],
            tmp_path,
        )
        assert len(tasks) == 1
        assert set(tasks[0].files_to_review) == {"app.py", "lib.py"}

    # REQ-004.5.1, REQ-004.5.2
    def test_all_changed_files_strategy_includes_all(self, tmp_path: Path) -> None:
        rule = _make_rule(strategy="all_changed_files", source_dir=tmp_path)
        tasks = match_files_to_rules(
            ["app.py", "lib.py", "main.ts"],
            [rule],
            tmp_path,
        )
        assert len(tasks) == 1
        assert set(tasks[0].files_to_review) == {"app.py", "lib.py", "main.ts"}

    # REQ-004.5.1
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

    # REQ-004.7.1
    def test_no_match_produces_no_tasks(self, tmp_path: Path) -> None:
        rule = _make_rule(include=["**/*.py"], source_dir=tmp_path)
        tasks = match_files_to_rules(
            ["app.ts"],
            [rule],
            tmp_path,
        )
        assert tasks == []

    # REQ-004.6.1, REQ-004.6.2
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

    # REQ-004.8.2, REQ-004.8.3
    def test_agent_resolution(self, tmp_path: Path) -> None:
        rule = _make_rule(
            agent={"claude": "security-expert", "gemini": "sec-bot"},
            source_dir=tmp_path,
        )
        tasks = match_files_to_rules(["app.py"], [rule], tmp_path, platform="claude")
        assert tasks[0].agent_name == "security-expert"

    # REQ-004.8.3
    def test_agent_resolution_missing_platform(self, tmp_path: Path) -> None:
        rule = _make_rule(
            agent={"gemini": "sec-bot"},
            source_dir=tmp_path,
        )
        tasks = match_files_to_rules(["app.py"], [rule], tmp_path, platform="claude")
        assert tasks[0].agent_name is None

    # REQ-004.2.4
    def test_source_location_set_on_tasks(self, tmp_path: Path) -> None:
        rule = _make_rule(
            source_dir=tmp_path,
            source_file=tmp_path / ".deepreview",
            source_line=3,
        )
        tasks = match_files_to_rules(["app.py"], [rule], tmp_path)
        assert tasks[0].source_location == ".deepreview:3"

    # REQ-004.9.2
    def test_multiple_rules_processed_independently(self, tmp_path: Path) -> None:
        rule_a = _make_rule(name="rule_a", include=["**/*.py"], source_dir=tmp_path)
        rule_b = _make_rule(name="rule_b", include=["**/*.py"], source_dir=tmp_path)
        tasks = match_files_to_rules(["app.py"], [rule_a, rule_b], tmp_path)
        assert len(tasks) == 2
        assert tasks[0].rule_name == "rule_a"
        assert tasks[1].rule_name == "rule_b"

    # REQ-004.4.3, REQ-004.4.4
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

    # REQ-003.1.7
    def test_raises_on_non_git_repo(self, tmp_path: Path) -> None:
        with pytest.raises(GitDiffError):
            get_changed_files(tmp_path)

    # REQ-003.1.2, REQ-003.1.6
    @patch("deepwork.review.matcher.subprocess.run")
    @patch("deepwork.review.matcher._detect_base_ref", return_value="main")
    @patch("deepwork.review.matcher._get_merge_base", return_value="abc123")
    def test_returns_sorted_deduplicated_files(
        self, mock_merge_base, mock_detect, mock_run, tmp_path: Path
    ) -> None:
        mock_run.return_value.stdout = "b.py\na.py\n"
        mock_run.return_value.returncode = 0
        files = get_changed_files(tmp_path)
        assert files == ["a.py", "b.py"]

    # REQ-003.2.5
    @patch("deepwork.review.matcher._git_diff_name_only")
    @patch("deepwork.review.matcher._get_merge_base", return_value="abc123")
    def test_uses_explicit_base_ref(self, mock_merge_base, mock_diff, tmp_path: Path) -> None:
        mock_diff.return_value = ["app.py"]
        get_changed_files(tmp_path, base_ref="develop")
        mock_merge_base.assert_called_once_with(tmp_path, "develop")
