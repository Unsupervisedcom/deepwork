"""Tests for MCP quality gate."""

from pathlib import Path

import pytest

from deepwork.mcp.quality_gate import MockQualityGate, QualityGate, QualityGateError


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    """Create a temporary project root."""
    return tmp_path


@pytest.fixture
def quality_gate() -> QualityGate:
    """Create a QualityGate instance."""
    return QualityGate(command="echo test", timeout=10)


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


class TestMockQualityGate:
    """Tests for MockQualityGate class."""

    async def test_mock_passes_by_default(self, project_root: Path) -> None:
        """Test mock gate passes by default."""
        gate = MockQualityGate()

        result = await gate.evaluate(
            quality_criteria=["Criterion 1"],
            outputs=["output.md"],
            project_root=project_root,
        )

        assert result.passed is True
        assert len(gate.evaluations) == 1

    async def test_mock_can_fail(self, project_root: Path) -> None:
        """Test mock gate can be configured to fail."""
        gate = MockQualityGate(should_pass=False, feedback="Mock failure")

        result = await gate.evaluate(
            quality_criteria=["Criterion 1"],
            outputs=["output.md"],
            project_root=project_root,
        )

        assert result.passed is False
        assert result.feedback == "Mock failure"

    async def test_mock_records_evaluations(self, project_root: Path) -> None:
        """Test mock gate records evaluations."""
        gate = MockQualityGate()

        await gate.evaluate(
            quality_criteria=["Criterion 1"],
            outputs=["output1.md"],
            project_root=project_root,
        )
        await gate.evaluate(
            quality_criteria=["Criterion 2"],
            outputs=["output2.md"],
            project_root=project_root,
        )

        assert len(gate.evaluations) == 2
        assert gate.evaluations[0]["quality_criteria"] == ["Criterion 1"]
        assert gate.evaluations[1]["quality_criteria"] == ["Criterion 2"]
