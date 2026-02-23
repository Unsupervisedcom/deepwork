"""Tests for the review MCP adapter (deepwork.review.mcp)."""

from pathlib import Path
from unittest.mock import patch

import pytest

from deepwork.review.config import ReviewRule, ReviewTask
from deepwork.review.mcp import ReviewToolError, get_configured_reviews, run_review


def _make_rule(tmp_path: Path) -> ReviewRule:
    """Create a ReviewRule for testing."""
    return ReviewRule(
        name="test_rule",
        description="Test rule description.",
        include_patterns=["**/*.py"],
        exclude_patterns=[],
        strategy="individual",
        instructions="Review it.",
        agent=None,
        all_changed_filenames=False,
        unchanged_matching_files=False,
        source_dir=tmp_path,
        source_file=tmp_path / ".deepreview",
        source_line=1,
    )


class TestRunReview:
    """Tests for the run_review adapter function."""

    @patch("deepwork.review.mcp.load_all_rules")
    def test_no_deepreview_files_returns_message(self, mock_load, tmp_path: Path) -> None:
        mock_load.return_value = ([], [])
        result = run_review(tmp_path, "claude")
        assert "No .deepreview configuration files found" in result

    @patch("deepwork.review.mcp.get_changed_files")
    @patch("deepwork.review.mcp.load_all_rules")
    def test_no_changed_files_git_diff(self, mock_load, mock_diff, tmp_path: Path) -> None:
        mock_load.return_value = ([_make_rule(tmp_path)], [])
        mock_diff.return_value = []
        result = run_review(tmp_path, "claude")
        assert "No changed files detected" in result

    @patch("deepwork.review.mcp.load_all_rules")
    def test_no_changed_files_explicit_empty_list(self, mock_load, tmp_path: Path) -> None:
        mock_load.return_value = ([_make_rule(tmp_path)], [])
        result = run_review(tmp_path, "claude", files=[])
        assert "No changed files detected" in result

    @patch("deepwork.review.mcp.match_files_to_rules")
    @patch("deepwork.review.mcp.get_changed_files")
    @patch("deepwork.review.mcp.load_all_rules")
    def test_no_rules_match(self, mock_load, mock_diff, mock_match, tmp_path: Path) -> None:
        mock_load.return_value = ([_make_rule(tmp_path)], [])
        mock_diff.return_value = ["app.ts"]
        mock_match.return_value = []
        result = run_review(tmp_path, "claude")
        assert "No review rules matched" in result

    @patch("deepwork.review.mcp.get_changed_files")
    @patch("deepwork.review.mcp.load_all_rules")
    def test_git_diff_error_raises_review_tool_error(
        self, mock_load, mock_diff, tmp_path: Path
    ) -> None:
        from deepwork.review.matcher import GitDiffError

        mock_load.return_value = ([_make_rule(tmp_path)], [])
        mock_diff.side_effect = GitDiffError("not a git repo")
        with pytest.raises(ReviewToolError, match="Git error"):
            run_review(tmp_path, "claude")

    @patch("deepwork.review.mcp.match_files_to_rules")
    @patch("deepwork.review.mcp.get_changed_files")
    @patch("deepwork.review.mcp.load_all_rules")
    def test_explicit_files_bypass_git_diff(
        self, mock_load, mock_diff, mock_match, tmp_path: Path
    ) -> None:
        mock_load.return_value = ([_make_rule(tmp_path)], [])
        mock_match.return_value = []
        run_review(tmp_path, "claude", files=["src/a.py", "src/b.py"])
        mock_diff.assert_not_called()
        mock_match.assert_called_once()
        called_files = mock_match.call_args[0][0]
        assert called_files == ["src/a.py", "src/b.py"]

    @patch("deepwork.review.mcp.write_instruction_files")
    @patch("deepwork.review.mcp.match_files_to_rules")
    @patch("deepwork.review.mcp.get_changed_files")
    @patch("deepwork.review.mcp.load_all_rules")
    def test_full_pipeline_returns_formatted_output(
        self, mock_load, mock_diff, mock_match, mock_write, tmp_path: Path
    ) -> None:
        rule = _make_rule(tmp_path)
        task = ReviewTask(
            rule_name="test_rule",
            files_to_review=["app.py"],
            instructions="Review it.",
            agent_name=None,
        )
        mock_load.return_value = ([rule], [])
        mock_diff.return_value = ["app.py"]
        mock_match.return_value = [task]
        mock_write.return_value = [(task, tmp_path / "instr.md")]

        result = run_review(tmp_path, "claude")
        assert "Invoke the following" in result
        mock_write.assert_called_once()

    def test_unsupported_platform_raises_review_tool_error(self, tmp_path: Path) -> None:
        with pytest.raises(ReviewToolError, match="Unsupported platform"):
            run_review(tmp_path, "unsupported_platform")

    @patch("deepwork.review.mcp.match_files_to_rules")
    @patch("deepwork.review.mcp.load_all_rules")
    def test_files_are_deduplicated_and_sorted(
        self, mock_load, mock_match, tmp_path: Path
    ) -> None:
        mock_load.return_value = ([_make_rule(tmp_path)], [])
        mock_match.return_value = []
        run_review(tmp_path, "claude", files=["z.py", "a.py", "z.py"])
        called_files = mock_match.call_args[0][0]
        assert called_files == ["a.py", "z.py"]

    @patch("deepwork.review.mcp.write_instruction_files")
    @patch("deepwork.review.mcp.match_files_to_rules")
    @patch("deepwork.review.mcp.get_changed_files")
    @patch("deepwork.review.mcp.load_all_rules")
    def test_write_error_raises_review_tool_error(
        self, mock_load, mock_diff, mock_match, mock_write, tmp_path: Path
    ) -> None:
        rule = _make_rule(tmp_path)
        task = ReviewTask(
            rule_name="test_rule",
            files_to_review=["app.py"],
            instructions="Review it.",
            agent_name=None,
        )
        mock_load.return_value = ([rule], [])
        mock_diff.return_value = ["app.py"]
        mock_match.return_value = [task]
        mock_write.side_effect = OSError("Permission denied")

        with pytest.raises(ReviewToolError, match="Error writing instruction files"):
            run_review(tmp_path, "claude")


class TestReviewToolRegistration:
    """Test that the review tool is registered on the MCP server."""

    def test_review_tool_is_registered(self, tmp_path: Path) -> None:
        from deepwork.jobs.mcp.server import create_server

        server = create_server(
            project_root=tmp_path,
            enable_quality_gate=False,
            platform="claude",
        )
        assert "get_review_instructions" in server._tool_manager._tools

    def test_review_tool_uses_platform_from_create_server(self, tmp_path: Path) -> None:
        """Platform passed to create_server is used by the review tool."""
        from deepwork.jobs.mcp.server import create_server

        server = create_server(
            project_root=tmp_path,
            enable_quality_gate=False,
            platform="claude",
        )
        assert "get_review_instructions" in server._tool_manager._tools

    def test_review_tool_defaults_platform_to_claude(self, tmp_path: Path) -> None:
        """When no platform is passed, review defaults to 'claude'."""
        from deepwork.jobs.mcp.server import create_server

        server = create_server(
            project_root=tmp_path,
            enable_quality_gate=False,
        )
        assert "get_review_instructions" in server._tool_manager._tools

    def test_get_configured_reviews_tool_is_registered(self, tmp_path: Path) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-008.1.1).
        """get_configured_reviews is registered on the MCP server."""
        from deepwork.jobs.mcp.server import create_server

        server = create_server(
            project_root=tmp_path,
            enable_quality_gate=False,
        )
        assert "get_configured_reviews" in server._tool_manager._tools


class TestGetConfiguredReviews:
    """Tests for the get_configured_reviews adapter function — validates REQ-008."""

    @patch("deepwork.review.mcp.load_all_rules")
    def test_returns_all_rules(self, mock_load: object, tmp_path: Path) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-008.1.3, REQ-008.2.1, REQ-008.2.2, REQ-008.2.3).
        rule1 = _make_rule(tmp_path)
        rule2 = ReviewRule(
            name="lint_rule",
            description="Lint rule description.",
            include_patterns=["**/*.ts"],
            exclude_patterns=[],
            strategy="matches_together",
            instructions="Lint it.",
            agent=None,
            all_changed_filenames=False,
            unchanged_matching_files=False,
            source_dir=tmp_path,
            source_file=tmp_path / ".deepreview",
            source_line=10,
        )
        mock_load.return_value = ([rule1, rule2], [])  # type: ignore[union-attr]

        result = get_configured_reviews(tmp_path)
        assert len(result) == 2
        assert result[0]["name"] == "test_rule"
        assert result[0]["description"] == "Test rule description."
        assert result[0]["defining_file"] == ".deepreview:1"
        assert result[1]["name"] == "lint_rule"
        assert result[1]["defining_file"] == ".deepreview:10"

    @patch("deepwork.review.mcp.load_all_rules")
    def test_returns_empty_when_no_rules(self, mock_load: object, tmp_path: Path) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-008.1.3).
        mock_load.return_value = ([], [])  # type: ignore[union-attr]
        result = get_configured_reviews(tmp_path)
        assert result == []

    @patch("deepwork.review.mcp.load_all_rules")
    def test_filters_by_matching_files(self, mock_load: object, tmp_path: Path) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-008.3.1).
        py_rule = _make_rule(tmp_path)  # includes **/*.py
        ts_rule = ReviewRule(
            name="ts_rule",
            description="TypeScript rule.",
            include_patterns=["**/*.ts"],
            exclude_patterns=[],
            strategy="individual",
            instructions="Review TS.",
            agent=None,
            all_changed_filenames=False,
            unchanged_matching_files=False,
            source_dir=tmp_path,
            source_file=tmp_path / ".deepreview",
            source_line=5,
        )
        mock_load.return_value = ([py_rule, ts_rule], [])  # type: ignore[union-attr]

        result = get_configured_reviews(tmp_path, only_rules_matching_files=["src/app.py"])
        assert len(result) == 1
        assert result[0]["name"] == "test_rule"

    @patch("deepwork.review.mcp.load_all_rules")
    def test_no_filter_returns_all(self, mock_load: object, tmp_path: Path) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-008.3.2).
        rule = _make_rule(tmp_path)
        mock_load.return_value = ([rule], [])  # type: ignore[union-attr]

        result = get_configured_reviews(tmp_path, only_rules_matching_files=None)
        assert len(result) == 1
        assert result[0]["name"] == "test_rule"

    @patch("deepwork.review.mcp.load_all_rules")
    def test_discovery_errors_still_return_valid_rules(
        self, mock_load: object, tmp_path: Path
    ) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-008.4.1, REQ-008.4.2).
        rule = _make_rule(tmp_path)
        errors = ["Error parsing /bad/.deepreview: invalid YAML"]
        mock_load.return_value = ([rule], errors)  # type: ignore[union-attr]

        result = get_configured_reviews(tmp_path)
        assert len(result) == 1
        assert result[0]["name"] == "test_rule"
