"""Tests for the deepwork review CLI command (deepwork.cli.review)."""

from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from deepwork.cli.review import review
from deepwork.review.config import ReviewRule, ReviewTask


def _make_rule(tmp_path: Path) -> ReviewRule:
    """Create a ReviewRule for testing."""
    return ReviewRule(
        name="test_rule",
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


class TestReviewCommand:
    """Tests for the review CLI command."""

    # REQ-006.4.1
    @patch("deepwork.cli.review.load_all_rules")
    def test_no_config_files_found(self, mock_load, tmp_path: Path) -> None:
        mock_load.return_value = ([], [])
        runner = CliRunner()
        result = runner.invoke(
            review,
            ["--instructions-for", "claude", "--path", str(tmp_path)],
        )
        assert result.exit_code == 0
        assert "No .deepreview configuration files found" in result.output

    # REQ-006.4.2
    @patch("deepwork.cli.review.get_changed_files")
    @patch("deepwork.cli.review.load_all_rules")
    def test_no_changed_files(self, mock_load, mock_diff, tmp_path: Path) -> None:
        mock_load.return_value = ([_make_rule(tmp_path)], [])
        mock_diff.return_value = []
        runner = CliRunner()
        result = runner.invoke(
            review,
            ["--instructions-for", "claude", "--path", str(tmp_path)],
        )
        assert result.exit_code == 0
        assert "No changed files detected" in result.output

    # REQ-006.4.3
    @patch("deepwork.cli.review.match_files_to_rules")
    @patch("deepwork.cli.review.get_changed_files")
    @patch("deepwork.cli.review.load_all_rules")
    def test_no_rules_match(self, mock_load, mock_diff, mock_match, tmp_path: Path) -> None:
        mock_load.return_value = ([_make_rule(tmp_path)], [])
        mock_diff.return_value = ["app.ts"]
        mock_match.return_value = []
        runner = CliRunner()
        result = runner.invoke(
            review,
            ["--instructions-for", "claude", "--path", str(tmp_path)],
        )
        assert result.exit_code == 0
        assert "No review rules matched" in result.output

    # REQ-006.5.2
    @patch("deepwork.cli.review.get_changed_files")
    @patch("deepwork.cli.review.load_all_rules")
    def test_git_error_exits_with_code_1(self, mock_load, mock_diff, tmp_path: Path) -> None:
        from deepwork.review.matcher import GitDiffError

        mock_load.return_value = ([_make_rule(tmp_path)], [])
        mock_diff.side_effect = GitDiffError("not a git repo")
        runner = CliRunner()
        result = runner.invoke(
            review,
            ["--instructions-for", "claude", "--path", str(tmp_path)],
        )
        assert result.exit_code == 1

    # REQ-006.5.1
    @patch("deepwork.cli.review.load_all_rules")
    def test_discovery_errors_reported_but_continues(self, mock_load, tmp_path: Path) -> None:
        from deepwork.review.discovery import DiscoveryError

        mock_load.return_value = (
            [],
            [DiscoveryError(file_path=Path("/bad/.deepreview"), error="parse error")],
        )
        runner = CliRunner()
        result = runner.invoke(
            review,
            ["--instructions-for", "claude", "--path", str(tmp_path)],
        )
        # With no valid rules loaded, should report no config found
        assert result.exit_code == 0
        assert "No .deepreview configuration files found" in result.output

    # REQ-006.2.1, REQ-006.3.2
    @patch("deepwork.cli.review.format_for_claude")
    @patch("deepwork.cli.review.write_instruction_files")
    @patch("deepwork.cli.review.match_files_to_rules")
    @patch("deepwork.cli.review.get_changed_files")
    @patch("deepwork.cli.review.load_all_rules")
    def test_full_pipeline_produces_output(
        self, mock_load, mock_diff, mock_match, mock_write, mock_format, tmp_path: Path
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
        mock_format.return_value = "Invoke the following..."

        runner = CliRunner()
        result = runner.invoke(
            review,
            ["--instructions-for", "claude", "--path", str(tmp_path)],
        )
        assert result.exit_code == 0
        assert "Invoke the following" in result.output
        mock_format.assert_called_once()

    # REQ-006.1.3
    def test_instructions_for_is_required(self) -> None:
        runner = CliRunner()
        result = runner.invoke(review, [])
        assert result.exit_code != 0
        assert "Missing option" in result.output or "required" in result.output.lower()

    # REQ-006.6.1: --files bypasses git diff
    @patch("deepwork.cli.review.match_files_to_rules")
    @patch("deepwork.cli.review.get_changed_files")
    @patch("deepwork.cli.review.load_all_rules")
    def test_files_option_bypasses_git_diff(
        self, mock_load, mock_diff, mock_match, tmp_path: Path
    ) -> None:
        mock_load.return_value = ([_make_rule(tmp_path)], [])
        mock_match.return_value = []
        runner = CliRunner()
        result = runner.invoke(
            review,
            [
                "--instructions-for", "claude",
                "--path", str(tmp_path),
                "--files", "src/a.py",
                "--files", "src/b.py",
            ],
        )
        assert result.exit_code == 0
        # git diff should NOT have been called
        mock_diff.assert_not_called()
        # match should have been called with the provided files
        mock_match.assert_called_once()
        called_files = mock_match.call_args[0][0]
        assert called_files == ["src/a.py", "src/b.py"]

    # REQ-006.6.2: stdin provides file list
    @patch("deepwork.cli.review.match_files_to_rules")
    @patch("deepwork.cli.review.get_changed_files")
    @patch("deepwork.cli.review.load_all_rules")
    def test_stdin_provides_file_list(
        self, mock_load, mock_diff, mock_match, tmp_path: Path
    ) -> None:
        mock_load.return_value = ([_make_rule(tmp_path)], [])
        mock_match.return_value = []
        runner = CliRunner()
        result = runner.invoke(
            review,
            ["--instructions-for", "claude", "--path", str(tmp_path)],
            input="src/x.py\nsrc/y.py\n",
        )
        assert result.exit_code == 0
        mock_diff.assert_not_called()
        mock_match.assert_called_once()
        called_files = mock_match.call_args[0][0]
        assert called_files == ["src/x.py", "src/y.py"]

    # REQ-006.6.4: file list is sorted and deduplicated
    @patch("deepwork.cli.review.match_files_to_rules")
    @patch("deepwork.cli.review.get_changed_files")
    @patch("deepwork.cli.review.load_all_rules")
    def test_files_option_deduplicates_and_sorts(
        self, mock_load, mock_diff, mock_match, tmp_path: Path
    ) -> None:
        mock_load.return_value = ([_make_rule(tmp_path)], [])
        mock_match.return_value = []
        runner = CliRunner()
        result = runner.invoke(
            review,
            [
                "--instructions-for", "claude",
                "--path", str(tmp_path),
                "--files", "z.py",
                "--files", "a.py",
                "--files", "z.py",
            ],
        )
        assert result.exit_code == 0
        called_files = mock_match.call_args[0][0]
        assert called_files == ["a.py", "z.py"]

    # REQ-006.6.1: --files takes priority over stdin
    @patch("deepwork.cli.review.match_files_to_rules")
    @patch("deepwork.cli.review.get_changed_files")
    @patch("deepwork.cli.review.load_all_rules")
    def test_files_option_takes_priority_over_stdin(
        self, mock_load, mock_diff, mock_match, tmp_path: Path
    ) -> None:
        mock_load.return_value = ([_make_rule(tmp_path)], [])
        mock_match.return_value = []
        runner = CliRunner()
        result = runner.invoke(
            review,
            [
                "--instructions-for", "claude",
                "--path", str(tmp_path),
                "--files", "explicit.py",
            ],
            input="from_stdin.py\n",
        )
        assert result.exit_code == 0
        called_files = mock_match.call_args[0][0]
        assert called_files == ["explicit.py"]
