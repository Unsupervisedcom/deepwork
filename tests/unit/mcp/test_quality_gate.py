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
        """Test building system instructions with dict format."""
        instructions = quality_gate._build_instructions(
            quality_criteria={
                "Output Exists": "Does the output file exist?",
                "Output Valid": "Is the output valid?",
            },
        )

        assert "**Output Exists**" in instructions
        assert "Does the output file exist?" in instructions
        assert "**Output Valid**" in instructions
        assert "Is the output valid?" in instructions
        assert "editor" in instructions.lower()
        assert "passed" in instructions  # JSON format mentioned
        assert "feedback" in instructions  # JSON format mentioned

    async def test_build_payload(self, quality_gate: QualityGate, project_root: Path) -> None:
        """Test building payload with file contents."""
        output_file = project_root / "output.md"
        output_file.write_text("Test content")

        payload = await quality_gate._build_payload(
            outputs={"report": "output.md"},
            project_root=project_root,
        )

        assert "Test content" in payload
        assert "output.md" in payload
        assert "--------------------" in payload
        assert "BEGIN OUTPUTS" in payload
        assert "END OUTPUTS" in payload

    async def test_build_payload_missing_file(
        self, quality_gate: QualityGate, project_root: Path
    ) -> None:
        """Test building payload with missing file."""
        payload = await quality_gate._build_payload(
            outputs={"report": "nonexistent.md"},
            project_root=project_root,
        )

        assert "File not found" in payload
        assert "nonexistent.md" in payload

    async def test_build_payload_files_type(
        self, quality_gate: QualityGate, project_root: Path
    ) -> None:
        """Test building payload with multi-file outputs."""
        (project_root / "a.md").write_text("File A")
        (project_root / "b.md").write_text("File B")

        payload = await quality_gate._build_payload(
            outputs={"reports": ["a.md", "b.md"]},
            project_root=project_root,
        )

        assert "File A" in payload
        assert "File B" in payload
        assert "a.md" in payload
        assert "b.md" in payload

    async def test_build_payload_binary_file(
        self, quality_gate: QualityGate, project_root: Path
    ) -> None:
        """Test building payload with a binary file produces a placeholder message."""
        binary_file = project_root / "report.pdf"
        binary_file.write_bytes(b"%PDF-1.4 \x00\x01\x02\xff\xfe binary content")

        payload = await quality_gate._build_payload(
            outputs={"report": "report.pdf"},
            project_root=project_root,
        )

        assert "Binary file" in payload
        assert "not included in review" in payload
        assert str(binary_file.resolve()) in payload
        assert "report.pdf" in payload
        # Should NOT contain the raw binary content
        assert "%PDF" not in payload

    async def test_build_payload_binary_file_in_multi_output(
        self, quality_gate: QualityGate, project_root: Path
    ) -> None:
        """Test building payload with a mix of text and binary files."""
        text_file = project_root / "summary.md"
        text_file.write_text("Summary text content")
        binary_file = project_root / "data.pdf"
        binary_file.write_bytes(b"\x00\x01\x02\xff\xfe binary data")

        payload = await quality_gate._build_payload(
            outputs={"docs": ["summary.md", "data.pdf"]},
            project_root=project_root,
        )

        # Text file content should be included
        assert "Summary text content" in payload
        # Binary file should have placeholder
        assert "Binary file" in payload
        assert "not included in review" in payload
        assert str(binary_file.resolve()) in payload

    async def test_build_payload_with_inputs_and_outputs(
        self, quality_gate: QualityGate, project_root: Path
    ) -> None:
        """Test building payload with both inputs and outputs in separate sections."""
        (project_root / "input_data.md").write_text("Input content from prior step")
        (project_root / "output_report.md").write_text("Output content from current step")

        payload = await quality_gate._build_payload(
            outputs={"report": "output_report.md"},
            project_root=project_root,
            inputs={"data": "input_data.md"},
        )

        # Both sections present
        assert "BEGIN INPUTS" in payload
        assert "END INPUTS" in payload
        assert "BEGIN OUTPUTS" in payload
        assert "END OUTPUTS" in payload
        # Content included
        assert "Input content from prior step" in payload
        assert "Output content from current step" in payload
        # Inputs section comes before outputs section
        assert payload.index("BEGIN INPUTS") < payload.index("BEGIN OUTPUTS")

    async def test_build_payload_outputs_only_no_input_headers(
        self, quality_gate: QualityGate, project_root: Path
    ) -> None:
        """Test that when no inputs provided, only outputs section appears."""
        (project_root / "output.md").write_text("Output only")

        payload = await quality_gate._build_payload(
            outputs={"report": "output.md"},
            project_root=project_root,
        )

        assert "BEGIN OUTPUTS" in payload
        assert "END OUTPUTS" in payload
        assert "BEGIN INPUTS" not in payload
        assert "END INPUTS" not in payload

    async def test_build_payload_empty_inputs_no_input_headers(
        self, quality_gate: QualityGate, project_root: Path
    ) -> None:
        """Test that empty inputs dict doesn't add input headers."""
        (project_root / "output.md").write_text("Output only")

        payload = await quality_gate._build_payload(
            outputs={"report": "output.md"},
            project_root=project_root,
            inputs={},
        )

        assert "BEGIN OUTPUTS" in payload
        assert "BEGIN INPUTS" not in payload

    async def test_build_payload_multiple_inputs(
        self, quality_gate: QualityGate, project_root: Path
    ) -> None:
        """Test building payload with multiple input files."""
        (project_root / "data1.md").write_text("Data file 1")
        (project_root / "data2.md").write_text("Data file 2")
        (project_root / "output.md").write_text("Final output")

        payload = await quality_gate._build_payload(
            outputs={"report": "output.md"},
            project_root=project_root,
            inputs={"data_a": "data1.md", "data_b": "data2.md"},
        )

        assert "Data file 1" in payload
        assert "Data file 2" in payload
        assert "Final output" in payload
        # Both files should be within the inputs section
        inputs_start = payload.index("BEGIN INPUTS")
        inputs_end = payload.index("END INPUTS")
        assert payload.index("data1.md") > inputs_start
        assert payload.index("data1.md") < inputs_end

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
            quality_criteria={},
            outputs={"report": "output.md"},
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
            quality_criteria={"Validity": "Must be valid"},
            outputs={"report": "output.md"},
            project_root=project_root,
        )

        mock_cli.run.assert_called_once()
        call_kwargs = mock_cli.run.call_args
        assert call_kwargs.kwargs["json_schema"] == QUALITY_GATE_RESPONSE_SCHEMA
        assert call_kwargs.kwargs["cwd"] == project_root
        assert "Validity" in call_kwargs.kwargs["system_prompt"]
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
                quality_criteria={"Test": "Test criterion"},
                outputs={"report": "output.md"},
                project_root=project_root,
            )

    async def test_schema_is_valid_json(self) -> None:
        """Test that QUALITY_GATE_RESPONSE_SCHEMA is valid JSON-serializable."""
        import json

        schema_json = json.dumps(QUALITY_GATE_RESPONSE_SCHEMA)
        assert schema_json
        parsed = json.loads(schema_json)
        assert parsed == QUALITY_GATE_RESPONSE_SCHEMA


class TestEvaluateReviews:
    """Tests for QualityGate.evaluate_reviews method."""

    async def test_empty_reviews(self, quality_gate: QualityGate, project_root: Path) -> None:
        """Test that empty reviews returns empty list."""
        result = await quality_gate.evaluate_reviews(
            reviews=[],
            outputs={"report": "output.md"},
            output_specs={"report": "file"},
            project_root=project_root,
        )
        assert result == []

    async def test_step_review_passes(
        self, mock_cli: ClaudeCLI, project_root: Path
    ) -> None:
        """Test step-level review that passes."""
        mock_cli.run = AsyncMock(
            return_value={"passed": True, "feedback": "All good", "criteria_results": []}
        )
        gate = QualityGate(cli=mock_cli)

        (project_root / "output.md").write_text("content")

        result = await gate.evaluate_reviews(
            reviews=[
                {
                    "run_each": "step",
                    "quality_criteria": {"Complete": "Is it complete?"},
                }
            ],
            outputs={"report": "output.md"},
            output_specs={"report": "file"},
            project_root=project_root,
        )
        assert result == []  # No failures

    async def test_step_review_fails(
        self, mock_cli: ClaudeCLI, project_root: Path
    ) -> None:
        """Test step-level review that fails."""
        mock_cli.run = AsyncMock(
            return_value={
                "passed": False,
                "feedback": "Issues found",
                "criteria_results": [
                    {"criterion": "Complete", "passed": False, "feedback": "Missing content"}
                ],
            }
        )
        gate = QualityGate(cli=mock_cli)

        (project_root / "output.md").write_text("content")

        result = await gate.evaluate_reviews(
            reviews=[
                {
                    "run_each": "step",
                    "quality_criteria": {"Complete": "Is it complete?"},
                }
            ],
            outputs={"report": "output.md"},
            output_specs={"report": "file"},
            project_root=project_root,
        )
        assert len(result) == 1
        assert result[0].review_run_each == "step"
        assert result[0].passed is False

    async def test_per_file_review(
        self, mock_cli: ClaudeCLI, project_root: Path
    ) -> None:
        """Test per-file review for files-type output."""
        call_count = 0

        async def mock_run(**kwargs: Any) -> dict[str, Any]:
            nonlocal call_count
            call_count += 1
            return {"passed": True, "feedback": "OK", "criteria_results": []}

        mock_cli.run = AsyncMock(side_effect=mock_run)
        gate = QualityGate(cli=mock_cli)

        (project_root / "a.md").write_text("File A")
        (project_root / "b.md").write_text("File B")

        result = await gate.evaluate_reviews(
            reviews=[
                {
                    "run_each": "reports",
                    "quality_criteria": {"Valid": "Is it valid?"},
                }
            ],
            outputs={"reports": ["a.md", "b.md"]},
            output_specs={"reports": "files"},
            project_root=project_root,
        )
        assert result == []  # All pass
        assert call_count == 2  # Called once per file

    async def test_single_file_review(
        self, mock_cli: ClaudeCLI, project_root: Path
    ) -> None:
        """Test review targeting a single-file output."""
        mock_cli.run = AsyncMock(
            return_value={"passed": True, "feedback": "OK", "criteria_results": []}
        )
        gate = QualityGate(cli=mock_cli)

        (project_root / "report.md").write_text("content")

        result = await gate.evaluate_reviews(
            reviews=[
                {
                    "run_each": "report",
                    "quality_criteria": {"Valid": "Is it valid?"},
                }
            ],
            outputs={"report": "report.md"},
            output_specs={"report": "file"},
            project_root=project_root,
        )
        assert result == []
        mock_cli.run.assert_called_once()


class TestMockQualityGate:
    """Tests for MockQualityGate class."""

    @staticmethod
    async def evaluate_mock_gate(
        gate: MockQualityGate,
        project_root: Path,
        criteria: dict[str, str] | None = None,
        outputs: dict[str, str | list[str]] | None = None,
    ) -> Any:
        """Helper to evaluate a mock gate with default parameters."""
        return await gate.evaluate(
            quality_criteria=criteria or {"Criterion 1": "Is criterion 1 met?"},
            outputs=outputs or {"report": "output.md"},
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
            gate,
            project_root,
            criteria={"Criterion 1": "Is criterion 1 met?"},
            outputs={"out1": "output1.md"},
        )
        await self.evaluate_mock_gate(
            gate,
            project_root,
            criteria={"Criterion 2": "Is criterion 2 met?"},
            outputs={"out2": "output2.md"},
        )

        assert len(gate.evaluations) == 2
        assert gate.evaluations[0]["quality_criteria"] == {"Criterion 1": "Is criterion 1 met?"}
        assert gate.evaluations[1]["quality_criteria"] == {"Criterion 2": "Is criterion 2 met?"}
