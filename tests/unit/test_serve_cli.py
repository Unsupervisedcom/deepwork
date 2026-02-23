"""Tests for serve CLI command --external-runner option."""

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from deepwork.cli.serve import serve


class TestServeExternalRunnerOption:
    """Tests for --external-runner CLI option on the serve command."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-005.2.6).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    @patch("deepwork.cli.serve._serve_mcp")
    def test_default_external_runner_is_none(self, mock_serve: MagicMock, tmp_path: str) -> None:
        """Test that --external-runner defaults to None when not specified."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            result = runner.invoke(serve, ["--path", td])
            if result.exit_code != 0 and result.exception:
                raise result.exception

        # _serve_mcp should be called with external_runner=None
        mock_serve.assert_called_once()
        call_args = mock_serve.call_args
        assert call_args[0][4] is None or call_args.kwargs.get("external_runner") is None

    # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-005.2.6).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    @patch("deepwork.cli.serve._serve_mcp")
    def test_external_runner_claude(self, mock_serve: MagicMock, tmp_path: str) -> None:
        """Test that --external-runner claude passes 'claude' through."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            result = runner.invoke(serve, ["--path", td, "--external-runner", "claude"])
            if result.exit_code != 0 and result.exception:
                raise result.exception

        mock_serve.assert_called_once()
        # external_runner is the 5th positional arg (index 4)
        call_args = mock_serve.call_args[0]
        assert call_args[4] == "claude"

    # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-005.2.6).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_external_runner_invalid_choice(self, tmp_path: str) -> None:
        """Test that invalid --external-runner values are rejected."""
        runner = CliRunner()
        result = runner.invoke(serve, ["--path", ".", "--external-runner", "invalid"])

        assert result.exit_code != 0
        assert "Invalid value" in result.output or "invalid" in result.output.lower()

    # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-005.2.6).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_help_shows_external_runner(self) -> None:
        """Test that --help shows the --external-runner option."""
        runner = CliRunner()
        result = runner.invoke(serve, ["--help"])

        assert result.exit_code == 0
        assert "--external-runner" in result.output
        assert "claude" in result.output
