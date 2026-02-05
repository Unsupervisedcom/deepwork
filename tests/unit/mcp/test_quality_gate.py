"""Tests for MCP quality gate."""

from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock

import pytest

from deepwork.mcp.claude_cli import ClaudeCLI, ClaudeCLIError
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
def mock_cli() -> ClaudeCLI:
    """Create a ClaudeCLI with a mocked run method."""
    cli = ClaudeCLI(timeout=10)
    cli.run = AsyncMock(return_value={"passed": True, "feedback": "OK", "criteria_results": []})
    return cli


@pytest.fixture
def quality_gate(mock_cli: ClaudeCLI) -> QualityGate:
    """Create a QualityGate instance with mocked CLI."""
    return QualityGate(cli=mock_cli)


@pytest.fixture
def output_file(project_root: Path) -> Path:
    """Create a test output file with default content."""
    output = project_root / "output.md"
    output.write_text("Test content")
    return output


class TestQualityGate:
    """Tests for QualityGate class."""

    def test_init_default_cli(self) -> None:
        """Test QualityGate creates a default ClaudeCLI if none provided."""
        gate = QualityGate()
        assert isinstance(gate._cli, ClaudeCLI)

    def test_init_custom_cli(self, mock_cli: ClaudeCLI) -> None:
        """Test QualityGate uses provided ClaudeCLI."""
        gate = QualityGate(cli=mock_cli)
        assert gate._cli is mock_cli

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
        output_file = project_root / "output.md"
        output_file.write_text("Test content")

        payload = await quality_gate._build_payload(
            outputs=["output.md"],
            project_root=project_root,
        )

        assert "Test content" in payload
        assert "output.md" in payload
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

    def test_parse_result_valid(self, quality_gate: QualityGate) -> None:
        """Test parsing valid structured output data."""
        data = {
            "passed": True,
            "feedback": "All good",
            "criteria_results": [{"criterion": "Test 1", "passed": True, "feedback": None}],
        }

        result = quality_gate._parse_result(data)

        assert result.passed is True
        assert result.feedback == "All good"
        assert len(result.criteria_results) == 1

    def test_parse_result_failed(self, quality_gate: QualityGate) -> None:
        """Test parsing failed evaluation data."""
        data = {
            "passed": False,
            "feedback": "Issues found",
            "criteria_results": [
                {"criterion": "Test 1", "passed": False, "feedback": "Failed"}
            ],
        }

        result = quality_gate._parse_result(data)

        assert result.passed is False
        assert result.feedback == "Issues found"
        assert result.criteria_results[0].passed is False

    def test_parse_result_multiple_criteria(self, quality_gate: QualityGate) -> None:
        """Test that criteria results are properly parsed with multiple entries."""
        data = {
            "passed": False,
            "feedback": "Two criteria failed",
            "criteria_results": [
                {"criterion": "First check", "passed": True, "feedback": None},
                {"criterion": "Second check", "passed": False, "feedback": "Missing data"},
                {"criterion": "Third check", "passed": False, "feedback": "Wrong format"},
            ],
        }

        result = quality_gate._parse_result(data)

        assert result.passed is False
        assert len(result.criteria_results) == 3
        assert result.criteria_results[0].passed is True
        assert result.criteria_results[0].feedback is None
        assert result.criteria_results[1].passed is False
        assert result.criteria_results[1].feedback == "Missing data"
        assert result.criteria_results[2].passed is False
        assert result.criteria_results[2].feedback == "Wrong format"

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

    async def test_evaluate_calls_cli_with_correct_args(
        self, mock_cli: ClaudeCLI, project_root: Path
    ) -> None:
        """Test that evaluate passes correct arguments to ClaudeCLI."""
        gate = QualityGate(cli=mock_cli)

        # Create output file
        output_file = project_root / "output.md"
        output_file.write_text("Test content")

        await gate.evaluate(
            quality_criteria=["Must be valid"],
            outputs=["output.md"],
            project_root=project_root,
        )

        mock_cli.run.assert_called_once()
        call_kwargs = mock_cli.run.call_args
        assert call_kwargs.kwargs["json_schema"] == QUALITY_GATE_RESPONSE_SCHEMA
        assert call_kwargs.kwargs["cwd"] == project_root
        assert "Must be valid" in call_kwargs.kwargs["system_prompt"]
        assert "Test content" in call_kwargs.kwargs["prompt"]

    async def test_evaluate_wraps_cli_error(
        self, mock_cli: ClaudeCLI, project_root: Path
    ) -> None:
        """Test that ClaudeCLIError is wrapped in QualityGateError."""
        mock_cli.run = AsyncMock(side_effect=ClaudeCLIError("CLI failed"))
        gate = QualityGate(cli=mock_cli)

        output_file = project_root / "output.md"
        output_file.write_text("content")

        with pytest.raises(QualityGateError, match="CLI failed"):
            await gate.evaluate(
                quality_criteria=["Test"],
                outputs=["output.md"],
                project_root=project_root,
            )

    async def test_schema_is_valid_json(self) -> None:
        """Test that QUALITY_GATE_RESPONSE_SCHEMA is valid JSON-serializable."""
        import json

        schema_json = json.dumps(QUALITY_GATE_RESPONSE_SCHEMA)
        assert schema_json
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
        """Helper to evaluate a mock gate with default parameters."""
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
