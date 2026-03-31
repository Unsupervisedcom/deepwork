"""Tests for serve CLI command options."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from deepwork.cli.serve import ServeError, _serve_mcp, serve


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

    @patch("deepwork.cli.serve._serve_mcp", side_effect=ServeError("Server failed"))
    def test_serve_error_prints_message_and_aborts(self, mock_serve: MagicMock, tmp_path: str) -> None:
        """Test that ServeError is caught, prints error, and aborts."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            result = runner.invoke(serve, ["--path", td])

        assert result.exit_code != 0
        assert "Server failed" in result.output

    @patch("deepwork.cli.serve._serve_mcp", side_effect=RuntimeError("Unexpected"))
    def test_unexpected_error_prints_message(self, mock_serve: MagicMock, tmp_path: str) -> None:
        """Test that unexpected exceptions are caught and printed."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            result = runner.invoke(serve, ["--path", td])

        assert result.exit_code != 0
        assert "Unexpected error" in result.output


class TestServeMCP:
    """Tests for the _serve_mcp internal function."""

    PATCH_TARGET = "deepwork.jobs.mcp.server.create_server"

    @patch(PATCH_TARGET)
    def test_creates_tmp_dir(self, mock_create: MagicMock, tmp_path: Path) -> None:
        """Test that _serve_mcp creates .deepwork/tmp/ directory."""
        mock_server = MagicMock()
        mock_create.return_value = mock_server

        _serve_mcp(tmp_path, "stdio", 8000)

        assert (tmp_path / ".deepwork" / "tmp").is_dir()

    @patch(PATCH_TARGET)
    def test_creates_tmp_gitignore(self, mock_create: MagicMock, tmp_path: Path) -> None:
        """Test that _serve_mcp creates .gitignore in tmp dir."""
        mock_server = MagicMock()
        mock_create.return_value = mock_server

        _serve_mcp(tmp_path, "stdio", 8000)

        gitignore = tmp_path / ".deepwork" / "tmp" / ".gitignore"
        assert gitignore.exists()
        content = gitignore.read_text()
        assert "*" in content
        assert "!.gitignore" in content

    @patch(PATCH_TARGET)
    def test_does_not_overwrite_existing_gitignore(self, mock_create: MagicMock, tmp_path: Path) -> None:
        """Test that _serve_mcp does not overwrite an existing .gitignore."""
        tmp_dir = tmp_path / ".deepwork" / "tmp"
        tmp_dir.mkdir(parents=True)
        gitignore = tmp_dir / ".gitignore"
        gitignore.write_text("custom content")

        mock_server = MagicMock()
        mock_create.return_value = mock_server

        _serve_mcp(tmp_path, "stdio", 8000)

        assert gitignore.read_text() == "custom content"

    @patch(PATCH_TARGET)
    def test_stdio_transport(self, mock_create: MagicMock, tmp_path: Path) -> None:
        """Test that stdio transport calls server.run with transport='stdio'."""
        mock_server = MagicMock()
        mock_create.return_value = mock_server

        _serve_mcp(tmp_path, "stdio", 8000)

        mock_server.run.assert_called_once_with(transport="stdio")

    @patch(PATCH_TARGET)
    def test_sse_transport(self, mock_create: MagicMock, tmp_path: Path) -> None:
        """Test that sse transport calls server.run with transport='sse' and port."""
        mock_server = MagicMock()
        mock_create.return_value = mock_server

        _serve_mcp(tmp_path, "sse", 9000)

        mock_server.run.assert_called_once_with(transport="sse", port=9000)

    @patch(PATCH_TARGET)
    def test_passes_platform_to_create_server(self, mock_create: MagicMock, tmp_path: Path) -> None:
        """Test that platform is forwarded to create_server."""
        mock_server = MagicMock()
        mock_create.return_value = mock_server

        _serve_mcp(tmp_path, "stdio", 8000, platform="claude")

        mock_create.assert_called_once_with(
            project_root=tmp_path,
            platform="claude",
        )
