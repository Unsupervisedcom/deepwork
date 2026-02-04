"""Tests for MCP quality gate."""

import json
from collections.abc import Callable, Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from deepwork.mcp.quality_gate import (
    QUALITY_GATE_RESPONSE_SCHEMA,
    MockQualityGate,
    QualityGate,
    QualityGateError,
)


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    """Create a temporary project root."""
    return tmp_path


@pytest.fixture
def quality_gate() -> QualityGate:
    """Create a QualityGate instance."""
    return QualityGate(command="echo test", timeout=10)


@pytest.fixture
def output_file(project_root: Path) -> Path:
    """Create a test output file with default content."""
    output = project_root / "output.md"
    output.write_text("Test content")
    return output


def create_mock_subprocess(
    response: dict[str, Any] | None = None,
    returncode: int = 0,
) -> tuple[list[str], Callable[..., MagicMock]]:
    """Create a mock subprocess executor that captures commands.

    ############################################################################
    # CRITICAL: DO NOT MODIFY THE RESPONSE FORMAT WITHOUT UNDERSTANDING THIS!
    #
    # This mock returns the quality gate response JSON DIRECTLY, without the
    # Claude CLI wrapper object. This is INTENTIONAL and tests that the
    # _parse_response method can handle BOTH:
    #
    # 1. Direct JSON (what this mock returns) - for backwards compatibility
    # 2. Wrapper objects from `claude -p --output-format json` which look like:
    #    {"type": "result", "result": "<actual JSON>", ...}
    #
    # The REAL Claude CLI with `--output-format json` returns a wrapper object.
    # The quality_gate.py code handles this by checking for the wrapper format
    # and extracting the "result" field before parsing.
    #
    # If you're seeing schema validation errors in production, it's because
    # the code expects to unwrap the response first. See test_parse_response_wrapper_object
    # for the wrapper format test.
    #
    # DO NOT "fix" this mock by adding a wrapper - that would break the test's
    # purpose of verifying direct JSON handling still works.
    ############################################################################

    Args:
        response: The JSON response to return. Defaults to a passing quality gate response.
        returncode: The return code for the process.

    Returns:
        A tuple of (captured_cmd list, mock_create_subprocess_exec function).
        The captured_cmd list will be populated with the command arguments when
        the mock is called.
    """
    if response is None:
        response = {"passed": True, "feedback": "OK", "criteria_results": []}

    captured_cmd: list[str] = []

    async def mock_create_subprocess_exec(*cmd: str, **kwargs: Any) -> MagicMock:  # noqa: ARG001
        captured_cmd.extend(cmd)
        mock_process = MagicMock()
        mock_process.returncode = returncode

        async def mock_communicate(input: bytes = b"") -> tuple[bytes, bytes]:  # noqa: ARG001
            # Returns direct JSON without CLI wrapper - see docstring above
            return json.dumps(response).encode(), b""

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
        response: The JSON response to return. Defaults to a passing quality gate response.
        returncode: The return code for the process.

    Yields:
        The list of captured command arguments.
    """
    captured_cmd, mock_subprocess = create_mock_subprocess(response, returncode)
    with patch("asyncio.create_subprocess_exec", mock_subprocess):
        yield captured_cmd


class TestQualityGate:
    """Tests for QualityGate class."""

    def test_init(self) -> None:
        """Test QualityGate initialization."""
        gate = QualityGate(command="claude -p", timeout=60)

        assert gate.command == "claude -p"
        assert gate.timeout == 60

    def test_init_defaults(self) -> None:
        """Test QualityGate default values."""
        gate = QualityGate()

        assert gate.command == "claude -p --output-format json"
        assert gate.timeout == 120

    def test_build_instructions(self, quality_gate: QualityGate) -> None:
        """Test building system instructions."""
        instructions = quality_gate._build_instructions(
            quality_criteria=["Output must exist", "Output must be valid"],
        )

        assert "Output must exist" in instructions
        assert "Output must be valid" in instructions
        assert "quality gate reviewer" in instructions.lower()
        assert "passed" in instructions  # JSON format mentioned
        assert "feedback" in instructions  # JSON format mentioned

    async def test_build_payload(self, quality_gate: QualityGate, project_root: Path) -> None:
        """Test building payload with file contents."""
        # Create test output file
        output_file = project_root / "output.md"
        output_file.write_text("Test content")

        payload = await quality_gate._build_payload(
            outputs=["output.md"],
            project_root=project_root,
        )

        assert "Test content" in payload
        assert "output.md" in payload
        # Check for the new separator format (20 dashes)
        assert "--------------------" in payload

    async def test_build_payload_missing_file(
        self, quality_gate: QualityGate, project_root: Path
    ) -> None:
        """Test building payload with missing file."""
        payload = await quality_gate._build_payload(
            outputs=["nonexistent.md"],
            project_root=project_root,
        )

        assert "File not found" in payload
        assert "nonexistent.md" in payload

    def test_parse_response_valid_json(self, quality_gate: QualityGate) -> None:
        """Test parsing valid JSON response."""
        response = """
        Here's my evaluation:

        ```json
        {
            "passed": true,
            "feedback": "All good",
            "criteria_results": [
                {"criterion": "Test 1", "passed": true, "feedback": null}
            ]
        }
        ```
        """

        result = quality_gate._parse_response(response)

        assert result.passed is True
        assert result.feedback == "All good"
        assert len(result.criteria_results) == 1

    def test_parse_response_failed(self, quality_gate: QualityGate) -> None:
        """Test parsing failed evaluation response."""
        response = """
        ```json
        {
            "passed": false,
            "feedback": "Issues found",
            "criteria_results": [
                {"criterion": "Test 1", "passed": false, "feedback": "Failed"}
            ]
        }
        ```
        """

        result = quality_gate._parse_response(response)

        assert result.passed is False
        assert result.feedback == "Issues found"
        assert result.criteria_results[0].passed is False

    def test_parse_response_invalid_json(self, quality_gate: QualityGate) -> None:
        """Test parsing invalid JSON response."""
        response = "This is not JSON"

        with pytest.raises(QualityGateError, match="Failed to parse"):
            quality_gate._parse_response(response)

    def test_parse_response_wrapper_object(self, quality_gate: QualityGate) -> None:
        """Test parsing response wrapped in Claude CLI --output-format json wrapper."""
        # This is what claude -p --output-format json returns
        wrapper_response = json.dumps({
            "type": "result",
            "subtype": "success",
            "is_error": False,
            "duration_ms": 1234,
            "result": json.dumps({
                "passed": True,
                "feedback": "All criteria met",
                "criteria_results": [
                    {"criterion": "Test 1", "passed": True, "feedback": None}
                ]
            }),
            "session_id": "test-session",
        })

        result = quality_gate._parse_response(wrapper_response)

        assert result.passed is True
        assert result.feedback == "All criteria met"
        assert len(result.criteria_results) == 1

    def test_parse_response_wrapper_empty_result(self, quality_gate: QualityGate) -> None:
        """Test parsing wrapper object with empty result raises error."""
        wrapper_response = json.dumps({
            "type": "result",
            "subtype": "success",
            "result": "",
        })

        with pytest.raises(QualityGateError, match="empty result"):
            quality_gate._parse_response(wrapper_response)

    async def test_evaluate_no_criteria(
        self, quality_gate: QualityGate, project_root: Path
    ) -> None:
        """Test evaluation with no criteria auto-passes."""
        result = await quality_gate.evaluate(
            quality_criteria=[],
            outputs=["output.md"],
            project_root=project_root,
        )

        assert result.passed is True
        assert "auto-passing" in result.feedback.lower()


class TestQualityGateCommandConstruction:
    """Tests for command construction, specifically JSON schema inclusion."""

    @staticmethod
    def get_command_arg(captured_cmd: list[str], flag: str) -> str:
        """Extract the argument value following a command flag.

        Args:
            captured_cmd: List of command arguments.
            flag: The flag to find (e.g., "--json-schema").

        Returns:
            The argument value following the flag.

        Raises:
            AssertionError: If the flag is not found in the command.
        """
        assert flag in captured_cmd, f"Expected {flag} in command, got: {captured_cmd}"
        flag_index = captured_cmd.index(flag)
        return captured_cmd[flag_index + 1]

    async def test_command_includes_json_schema(
        self, output_file: Path, project_root: Path
    ) -> None:
        """Test that the command includes --json-schema with the correct schema."""
        gate = QualityGate(command="claude -p --output-format json", timeout=10)

        with patched_subprocess() as captured_cmd:
            await gate.evaluate(
                quality_criteria=["Test criterion"],
                outputs=[output_file.name],
                project_root=project_root,
            )

        schema_json = self.get_command_arg(captured_cmd, "--json-schema")
        parsed_schema = json.loads(schema_json)
        assert parsed_schema == QUALITY_GATE_RESPONSE_SCHEMA, (
            f"Schema mismatch. Expected:\n{QUALITY_GATE_RESPONSE_SCHEMA}\n"
            f"Got:\n{parsed_schema}"
        )

    async def test_command_includes_system_prompt(
        self, output_file: Path, project_root: Path
    ) -> None:
        """Test that the command includes --system-prompt with quality criteria."""
        gate = QualityGate(command="claude -p", timeout=10)

        with patched_subprocess() as captured_cmd:
            await gate.evaluate(
                quality_criteria=["Output must exist", "Output must be valid"],
                outputs=[output_file.name],
                project_root=project_root,
            )

        system_prompt = self.get_command_arg(captured_cmd, "--system-prompt")
        assert "Output must exist" in system_prompt
        assert "Output must be valid" in system_prompt

    async def test_schema_is_valid_json(self) -> None:
        """Test that QUALITY_GATE_RESPONSE_SCHEMA is valid JSON."""
        # This test ensures the schema can be serialized
        schema_json = json.dumps(QUALITY_GATE_RESPONSE_SCHEMA)
        assert schema_json  # Non-empty string

        # And parsed back
        parsed = json.loads(schema_json)
        assert parsed == QUALITY_GATE_RESPONSE_SCHEMA


class TestMockQualityGate:
    """Tests for MockQualityGate class."""

    @staticmethod
    async def evaluate_mock_gate(
        gate: MockQualityGate,
        project_root: Path,
        criteria: list[str] | None = None,
        outputs: list[str] | None = None,
    ) -> Any:
        """Helper to evaluate a mock gate with default parameters.

        Args:
            gate: The MockQualityGate instance to evaluate.
            project_root: The project root path.
            criteria: Quality criteria list. Defaults to ["Criterion 1"].
            outputs: Output files list. Defaults to ["output.md"].

        Returns:
            The evaluation result.
        """
        return await gate.evaluate(
            quality_criteria=criteria or ["Criterion 1"],
            outputs=outputs or ["output.md"],
            project_root=project_root,
        )

    async def test_mock_passes_by_default(self, project_root: Path) -> None:
        """Test mock gate passes by default."""
        gate = MockQualityGate()
        result = await self.evaluate_mock_gate(gate, project_root)

        assert result.passed is True
        assert len(gate.evaluations) == 1

    async def test_mock_can_fail(self, project_root: Path) -> None:
        """Test mock gate can be configured to fail."""
        gate = MockQualityGate(should_pass=False, feedback="Mock failure")
        result = await self.evaluate_mock_gate(gate, project_root)

        assert result.passed is False
        assert result.feedback == "Mock failure"

    async def test_mock_records_evaluations(self, project_root: Path) -> None:
        """Test mock gate records evaluations."""
        gate = MockQualityGate()

        await self.evaluate_mock_gate(
            gate, project_root, criteria=["Criterion 1"], outputs=["output1.md"]
        )
        await self.evaluate_mock_gate(
            gate, project_root, criteria=["Criterion 2"], outputs=["output2.md"]
        )

        assert len(gate.evaluations) == 2
        assert gate.evaluations[0]["quality_criteria"] == ["Criterion 1"]
        assert gate.evaluations[1]["quality_criteria"] == ["Criterion 2"]
