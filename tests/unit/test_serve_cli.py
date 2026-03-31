"""Tests for serve CLI command options."""

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from deepwork.cli.serve import serve


class TestServeCLI:
    """Tests for serve CLI command."""

    @patch("deepwork.cli.serve._serve_mcp")
    def test_default_invocation(self, mock_serve: MagicMock, tmp_path: str) -> None:
        """Test that serve calls _serve_mcp with correct defaults."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            result = runner.invoke(serve, ["--path", td])
            if result.exit_code != 0 and result.exception:
                raise result.exception

        mock_serve.assert_called_once()
        call_args = mock_serve.call_args[0]
        # _serve_mcp(project_path, transport, port, platform)
        assert call_args[1] == "stdio"  # transport
        assert call_args[2] == 8000  # port
        assert call_args[3] is None  # platform

    # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-005.2.6).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_external_runner_option_accepted(self, tmp_path: str) -> None:
        """Test that --external-runner is accepted (hidden, backwards compat)."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            with patch("deepwork.cli.serve._serve_mcp"):
                result = runner.invoke(serve, ["--path", td, "--external-runner", "claude"])
                # Should not fail — option is still accepted for backwards compat
                assert result.exit_code == 0

    # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-005.2.6).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_external_runner_invalid_choice(self, tmp_path: str) -> None:
        """Test that invalid --external-runner values are rejected."""
        runner = CliRunner()
        result = runner.invoke(serve, ["--path", ".", "--external-runner", "invalid"])

        assert result.exit_code != 0
        assert "Invalid value" in result.output or "invalid" in result.output.lower()

    @patch("deepwork.cli.serve._serve_mcp")
    def test_platform_option(self, mock_serve: MagicMock, tmp_path: str) -> None:
        """Test that --platform passes through to _serve_mcp."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            result = runner.invoke(serve, ["--path", td, "--platform", "claude"])
            if result.exit_code != 0 and result.exception:
                raise result.exception

        mock_serve.assert_called_once()
        call_args = mock_serve.call_args[0]
        assert call_args[3] == "claude"  # platform

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-011.4.1).
    @patch("deepwork.cli.serve._serve_mcp")
    def test_no_path_passes_explicit_false(self, mock_serve: MagicMock) -> None:
        """When --path is omitted, explicit_path=False is passed to _serve_mcp."""
        runner = CliRunner()
        result = runner.invoke(serve, [])
        if result.exit_code != 0 and result.exception:
            raise result.exception

        mock_serve.assert_called_once()
        assert mock_serve.call_args[1]["explicit_path"] is False

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-011.4.2).
    @patch("deepwork.cli.serve._serve_mcp")
    def test_explicit_path_passes_explicit_true(self, mock_serve: MagicMock, tmp_path: str) -> None:
        """When --path is provided, explicit_path=True is passed to _serve_mcp."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            result = runner.invoke(serve, ["--path", td])
            if result.exit_code != 0 and result.exception:
                raise result.exception

        mock_serve.assert_called_once()
        assert mock_serve.call_args[1]["explicit_path"] is True

    def test_help_shows_options(self) -> None:
        """Test that --help shows the available options."""
        runner = CliRunner()
        result = runner.invoke(serve, ["--help"])

        assert result.exit_code == 0
        assert "--path" in result.output
        assert "--transport" in result.output
        assert "--platform" in result.output
