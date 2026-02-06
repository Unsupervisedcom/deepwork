"""Tests for Claude CLI subprocess wrapper."""

import json
from collections.abc import Callable, Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from deepwork.mcp.claude_cli import ClaudeCLI, ClaudeCLIError


def create_mock_subprocess(
    response: dict[str, Any] | None = None,
    returncode: int = 0,
) -> tuple[list[str], Callable[..., MagicMock]]:
    """Create a mock subprocess executor that captures commands.

    Args:
        response: The structured_output to return in the CLI wrapper.
                  Defaults to an empty passing response.
        returncode: The return code for the process.

    Returns:
        A tuple of (captured_cmd list, mock_create_subprocess_exec function).
    """
    if response is None:
        response = {"result": "ok"}

    captured_cmd: list[str] = []

    async def mock_create_subprocess_exec(*cmd: str, **kwargs: Any) -> MagicMock:  # noqa: ARG001
        captured_cmd.extend(cmd)
        mock_process = MagicMock()
        mock_process.returncode = returncode

        async def mock_communicate(input: bytes = b"") -> tuple[bytes, bytes]:  # noqa: ARG001
            wrapper = {
                "type": "result",
                "subtype": "success",
                "is_error": False,
                "structured_output": response,
            }
            return json.dumps(wrapper).encode(), b""

        mock_process.communicate = mock_communicate
        return mock_process

    return captured_cmd, mock_create_subprocess_exec


@contextmanager
def patched_subprocess(
    response: dict[str, Any] | None = None,
    returncode: int = 0,
) -> Generator[list[str], None, None]:
    """Context manager that patches subprocess and yields captured command.

    Args:
        response: The structured_output to return. Defaults to a simple response.
        returncode: The return code for the process.

    Yields:
        The list of captured command arguments.
    """
    captured_cmd, mock_subprocess = create_mock_subprocess(response, returncode)
    with patch("asyncio.create_subprocess_exec", mock_subprocess):
        yield captured_cmd


TEST_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["value"],
    "properties": {"value": {"type": "string"}},
}


class TestClaudeCLI:
    """Tests for ClaudeCLI class."""

    def test_init(self) -> None:
        """Test ClaudeCLI initialization."""
        cli = ClaudeCLI(timeout=60)
        assert cli.timeout == 60

    def test_init_defaults(self) -> None:
        """Test ClaudeCLI default values."""
        cli = ClaudeCLI()
        assert cli.timeout == 120

    async def test_run_returns_structured_output(self, tmp_path: Path) -> None:
        """Test that run() returns the structured_output dict."""
        cli = ClaudeCLI(timeout=10)
        expected = {"value": "hello"}

        with patched_subprocess(response=expected):
            result = await cli.run(
                prompt="test prompt",
                system_prompt="test system",
                json_schema=TEST_SCHEMA,
                cwd=tmp_path,
            )

        assert result == expected

    async def test_run_pipes_prompt_via_stdin(self, tmp_path: Path) -> None:
        """Test that the prompt is piped via stdin."""
        cli = ClaudeCLI(timeout=10)
        captured_input: list[bytes] = []

        async def mock_exec(*cmd: str, **kwargs: Any) -> MagicMock:  # noqa: ARG001
            mock = MagicMock()
            mock.returncode = 0

            async def mock_communicate(input: bytes = b"") -> tuple[bytes, bytes]:
                captured_input.append(input)
                wrapper = {
                    "type": "result",
                    "subtype": "success",
                    "is_error": False,
                    "structured_output": {"value": "ok"},
                }
                return json.dumps(wrapper).encode(), b""

            mock.communicate = mock_communicate
            return mock

        with patch("asyncio.create_subprocess_exec", mock_exec):
            await cli.run(
                prompt="my prompt text",
                system_prompt="sys",
                json_schema=TEST_SCHEMA,
                cwd=tmp_path,
            )

        assert len(captured_input) == 1
        assert captured_input[0] == b"my prompt text"


class TestClaudeCLICommandConstruction:
    """Tests for command construction."""

    @staticmethod
    def get_command_arg(captured_cmd: list[str], flag: str) -> str:
        """Extract the argument value following a command flag."""
        assert flag in captured_cmd, f"Expected {flag} in command, got: {captured_cmd}"
        flag_index = captured_cmd.index(flag)
        return captured_cmd[flag_index + 1]

    async def test_command_includes_json_schema(self, tmp_path: Path) -> None:
        """Test that the command includes --json-schema with the correct schema."""
        cli = ClaudeCLI(timeout=10)

        with patched_subprocess() as captured_cmd:
            await cli.run(
                prompt="test",
                system_prompt="test",
                json_schema=TEST_SCHEMA,
                cwd=tmp_path,
            )

        schema_json = self.get_command_arg(captured_cmd, "--json-schema")
        parsed_schema = json.loads(schema_json)
        assert parsed_schema == TEST_SCHEMA

    async def test_command_includes_system_prompt(self, tmp_path: Path) -> None:
        """Test that the command includes --system-prompt."""
        cli = ClaudeCLI(timeout=10)

        with patched_subprocess() as captured_cmd:
            await cli.run(
                prompt="test",
                system_prompt="You are a reviewer",
                json_schema=TEST_SCHEMA,
                cwd=tmp_path,
            )

        system_prompt = self.get_command_arg(captured_cmd, "--system-prompt")
        assert system_prompt == "You are a reviewer"

    async def test_command_has_correct_flag_ordering(self, tmp_path: Path) -> None:
        """Test that flags come before -p -- for proper CLI invocation.

        See doc/reference/calling_claude_in_print_mode.md for details on
        why flag ordering matters.
        """
        cli = ClaudeCLI(timeout=10)

        with patched_subprocess() as captured_cmd:
            await cli.run(
                prompt="test",
                system_prompt="test",
                json_schema=TEST_SCHEMA,
                cwd=tmp_path,
            )

        assert captured_cmd[0] == "claude"
        assert "--print" in captured_cmd
        assert "--output-format" in captured_cmd
        assert "-p" in captured_cmd
        assert "--" in captured_cmd

        # Verify -p -- comes last (after all other flags)
        p_index = captured_cmd.index("-p")
        dash_dash_index = captured_cmd.index("--")
        json_schema_index = captured_cmd.index("--json-schema")
        system_prompt_index = captured_cmd.index("--system-prompt")

        assert json_schema_index < p_index, "Flags must come before -p"
        assert system_prompt_index < p_index, "Flags must come before -p"
        assert dash_dash_index == p_index + 1, "-- must immediately follow -p"

    async def test_test_command_override(self, tmp_path: Path) -> None:
        """Test that _test_command overrides the default command."""
        cli = ClaudeCLI(timeout=10, _test_command=["echo", "test"])

        with patched_subprocess() as captured_cmd:
            await cli.run(
                prompt="test",
                system_prompt="sys prompt",
                json_schema=TEST_SCHEMA,
                cwd=tmp_path,
            )

        assert captured_cmd[0] == "echo"
        assert captured_cmd[1] == "test"
        assert "--system-prompt" in captured_cmd
        assert "sys prompt" in captured_cmd
        # _test_command should NOT include --json-schema
        assert "--json-schema" not in captured_cmd


class TestClaudeCLIWrapperParsing:
    """Tests for Claude CLI response wrapper parsing."""

    def test_parse_wrapper_valid(self) -> None:
        """Test parsing a valid wrapper response."""
        cli = ClaudeCLI()
        response = json.dumps(
            {
                "type": "result",
                "subtype": "success",
                "is_error": False,
                "structured_output": {"value": "hello"},
            }
        )

        result = cli._parse_wrapper(response)
        assert result == {"value": "hello"}

    def test_parse_wrapper_error(self) -> None:
        """Test parsing a wrapper with is_error=True."""
        cli = ClaudeCLI()
        response = json.dumps(
            {
                "type": "result",
                "subtype": "error",
                "is_error": True,
                "result": "Something went wrong",
            }
        )

        with pytest.raises(ClaudeCLIError, match="returned error"):
            cli._parse_wrapper(response)

    def test_parse_wrapper_missing_structured_output(self) -> None:
        """Test parsing a wrapper missing structured_output field."""
        cli = ClaudeCLI()
        response = json.dumps(
            {
                "type": "result",
                "subtype": "success",
                "is_error": False,
                "result": "Some text response",
            }
        )

        with pytest.raises(ClaudeCLIError, match="missing 'structured_output'"):
            cli._parse_wrapper(response)

    def test_parse_wrapper_invalid_json(self) -> None:
        """Test parsing invalid JSON."""
        cli = ClaudeCLI()

        with pytest.raises(ClaudeCLIError, match="Failed to parse"):
            cli._parse_wrapper("This is not JSON")


class TestClaudeCLIErrors:
    """Tests for error handling."""

    async def test_timeout_error(self, tmp_path: Path) -> None:
        """Test that timeout raises ClaudeCLIError."""
        import asyncio

        cli = ClaudeCLI(timeout=0)

        async def mock_exec(*cmd: str, **kwargs: Any) -> MagicMock:  # noqa: ARG001
            mock = MagicMock()

            async def mock_communicate(input: bytes = b"") -> tuple[bytes, bytes]:  # noqa: ARG001
                await asyncio.sleep(10)
                return b"", b""

            mock.communicate = mock_communicate
            mock.kill = MagicMock()

            async def mock_wait() -> None:
                pass

            mock.wait = mock_wait
            return mock

        with patch("asyncio.create_subprocess_exec", mock_exec):
            with pytest.raises(ClaudeCLIError, match="timed out"):
                await cli.run(
                    prompt="test",
                    system_prompt="test",
                    json_schema=TEST_SCHEMA,
                    cwd=tmp_path,
                )

    async def test_nonzero_exit_code(self, tmp_path: Path) -> None:
        """Test that non-zero exit code raises ClaudeCLIError."""
        cli = ClaudeCLI(timeout=10)

        async def mock_exec(*cmd: str, **kwargs: Any) -> MagicMock:  # noqa: ARG001
            mock = MagicMock()
            mock.returncode = 1

            async def mock_communicate(input: bytes = b"") -> tuple[bytes, bytes]:  # noqa: ARG001
                return b"", b"error output"

            mock.communicate = mock_communicate
            return mock

        with patch("asyncio.create_subprocess_exec", mock_exec):
            with pytest.raises(ClaudeCLIError, match="exit code 1"):
                await cli.run(
                    prompt="test",
                    system_prompt="test",
                    json_schema=TEST_SCHEMA,
                    cwd=tmp_path,
                )

    async def test_command_not_found(self, tmp_path: Path) -> None:
        """Test that missing command raises ClaudeCLIError."""
        cli = ClaudeCLI(timeout=10)

        async def mock_exec(*cmd: str, **kwargs: Any) -> MagicMock:  # noqa: ARG001
            raise FileNotFoundError("No such file")

        with patch("asyncio.create_subprocess_exec", mock_exec):
            with pytest.raises(ClaudeCLIError, match="command not found"):
                await cli.run(
                    prompt="test",
                    system_prompt="test",
                    json_schema=TEST_SCHEMA,
                    cwd=tmp_path,
                )
