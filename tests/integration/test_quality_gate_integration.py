"""Integration tests for quality gate subprocess execution.

These tests actually run the subprocess and verify that pass/fail
detection works correctly with real process invocation.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from deepwork.mcp.quality_gate import QualityGate, QualityGateError


# Path to our mock review agent script
MOCK_AGENT_PATH = Path(__file__).parent.parent / "fixtures" / "mock_review_agent.py"


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    """Create a temporary project root with test files."""
    # Create a sample output file
    output_file = tmp_path / "output.md"
    output_file.write_text("Test content for review")
    return tmp_path


@pytest.fixture
def mock_agent_command() -> str:
    """Get the command to run the mock review agent."""
    return f"{sys.executable} {MOCK_AGENT_PATH}"


class TestQualityGateIntegration:
    """Integration tests that run real subprocesses."""

    def test_subprocess_returns_pass(
        self, project_root: Path, mock_agent_command: str
    ) -> None:
        """Test that a passing response is correctly detected."""
        gate = QualityGate(command=mock_agent_command, timeout=30)

        # Set environment to force pass
        env_backup = os.environ.get("REVIEW_RESULT")
        os.environ["REVIEW_RESULT"] = "pass"

        try:
            result = gate.evaluate(
                quality_criteria=["Output must exist", "Output must be valid"],
                outputs=["output.md"],
                project_root=project_root,
            )

            assert result.passed is True, f"Expected pass but got: {result}"
            assert result.feedback == "All criteria met"
        finally:
            if env_backup is not None:
                os.environ["REVIEW_RESULT"] = env_backup
            else:
                os.environ.pop("REVIEW_RESULT", None)

    def test_subprocess_returns_fail(
        self, project_root: Path, mock_agent_command: str
    ) -> None:
        """Test that a failing response is correctly detected."""
        gate = QualityGate(command=mock_agent_command, timeout=30)

        # Set environment to force fail
        env_backup = os.environ.get("REVIEW_RESULT")
        os.environ["REVIEW_RESULT"] = "fail"

        try:
            result = gate.evaluate(
                quality_criteria=["Output must exist"],
                outputs=["output.md"],
                project_root=project_root,
            )

            assert result.passed is False, f"Expected fail but got pass: {result}"
            assert "not met" in result.feedback.lower()
            assert len(result.criteria_results) > 0
            assert result.criteria_results[0].passed is False
        finally:
            if env_backup is not None:
                os.environ["REVIEW_RESULT"] = env_backup
            else:
                os.environ.pop("REVIEW_RESULT", None)

    def test_subprocess_malformed_response_raises_error(
        self, project_root: Path, mock_agent_command: str
    ) -> None:
        """Test that malformed JSON raises an error."""
        gate = QualityGate(command=mock_agent_command, timeout=30)

        env_backup = os.environ.get("REVIEW_RESULT")
        os.environ["REVIEW_RESULT"] = "malformed"

        try:
            with pytest.raises(QualityGateError, match="Failed to parse"):
                gate.evaluate(
                    quality_criteria=["Criterion 1"],
                    outputs=["output.md"],
                    project_root=project_root,
                )
        finally:
            if env_backup is not None:
                os.environ["REVIEW_RESULT"] = env_backup
            else:
                os.environ.pop("REVIEW_RESULT", None)

    def test_subprocess_nonzero_exit_raises_error(
        self, project_root: Path, mock_agent_command: str
    ) -> None:
        """Test that non-zero exit code raises an error."""
        gate = QualityGate(command=mock_agent_command, timeout=30)

        env_backup = os.environ.get("REVIEW_RESULT")
        os.environ["REVIEW_RESULT"] = "error"

        try:
            with pytest.raises(QualityGateError, match="failed with exit code"):
                gate.evaluate(
                    quality_criteria=["Criterion 1"],
                    outputs=["output.md"],
                    project_root=project_root,
                )
        finally:
            if env_backup is not None:
                os.environ["REVIEW_RESULT"] = env_backup
            else:
                os.environ.pop("REVIEW_RESULT", None)

    def test_subprocess_timeout(
        self, project_root: Path, mock_agent_command: str
    ) -> None:
        """Test that subprocess timeout is handled correctly."""
        gate = QualityGate(command=mock_agent_command, timeout=1)  # 1 second timeout

        env_backup = os.environ.get("REVIEW_RESULT")
        os.environ["REVIEW_RESULT"] = "timeout"

        try:
            with pytest.raises(QualityGateError, match="timed out"):
                gate.evaluate(
                    quality_criteria=["Criterion 1"],
                    outputs=["output.md"],
                    project_root=project_root,
                )
        finally:
            if env_backup is not None:
                os.environ["REVIEW_RESULT"] = env_backup
            else:
                os.environ.pop("REVIEW_RESULT", None)

    def test_subprocess_command_not_found(self, project_root: Path) -> None:
        """Test that missing command is handled correctly."""
        gate = QualityGate(command="nonexistent_command_12345", timeout=30)

        with pytest.raises(QualityGateError, match="command not found"):
            gate.evaluate(
                quality_criteria=["Criterion 1"],
                outputs=["output.md"],
                project_root=project_root,
            )

    def test_auto_mode_detects_force_pass_marker(
        self, project_root: Path, mock_agent_command: str
    ) -> None:
        """Test that FORCE_PASS marker in content causes pass."""
        gate = QualityGate(command=mock_agent_command, timeout=30)

        # Create output with FORCE_PASS marker
        output_file = project_root / "marker_output.md"
        output_file.write_text("Content with FORCE_PASS marker")

        # Clear any environment override
        env_backup = os.environ.get("REVIEW_RESULT")
        os.environ.pop("REVIEW_RESULT", None)

        try:
            result = gate.evaluate(
                quality_criteria=["Criterion 1"],
                outputs=["marker_output.md"],
                project_root=project_root,
            )

            assert result.passed is True
        finally:
            if env_backup is not None:
                os.environ["REVIEW_RESULT"] = env_backup

    def test_auto_mode_detects_force_fail_marker(
        self, project_root: Path, mock_agent_command: str
    ) -> None:
        """Test that FORCE_FAIL marker in content causes fail."""
        gate = QualityGate(command=mock_agent_command, timeout=30)

        # Create output with FORCE_FAIL marker
        output_file = project_root / "marker_output.md"
        output_file.write_text("Content with FORCE_FAIL marker")

        # Clear any environment override
        env_backup = os.environ.get("REVIEW_RESULT")
        os.environ.pop("REVIEW_RESULT", None)

        try:
            result = gate.evaluate(
                quality_criteria=["Criterion 1"],
                outputs=["marker_output.md"],
                project_root=project_root,
            )

            assert result.passed is False
        finally:
            if env_backup is not None:
                os.environ["REVIEW_RESULT"] = env_backup

    def test_missing_output_file_causes_fail(
        self, project_root: Path, mock_agent_command: str
    ) -> None:
        """Test that missing output file is detected as failure."""
        gate = QualityGate(command=mock_agent_command, timeout=30)

        # Clear any environment override - let auto mode handle it
        env_backup = os.environ.get("REVIEW_RESULT")
        os.environ.pop("REVIEW_RESULT", None)

        try:
            result = gate.evaluate(
                quality_criteria=["Output files must exist"],
                outputs=["nonexistent_file.md"],
                project_root=project_root,
            )

            # The mock agent should detect "File not found" in prompt and fail
            assert result.passed is False
        finally:
            if env_backup is not None:
                os.environ["REVIEW_RESULT"] = env_backup


class TestQualityGateResponseParsing:
    """Test response parsing with various JSON formats."""

    def test_parse_json_in_code_block(self) -> None:
        """Test parsing JSON wrapped in markdown code block."""
        gate = QualityGate()

        response = '''Here's my evaluation:

```json
{
    "passed": true,
    "feedback": "All good",
    "criteria_results": [
        {"criterion": "Test", "passed": true, "feedback": null}
    ]
}
```

Hope that helps!'''

        result = gate._parse_response(response)

        assert result.passed is True
        assert result.feedback == "All good"

    def test_parse_json_in_plain_code_block(self) -> None:
        """Test parsing JSON in plain code block (no json tag)."""
        gate = QualityGate()

        response = '''```
{
    "passed": false,
    "feedback": "Issues found",
    "criteria_results": []
}
```'''

        result = gate._parse_response(response)

        assert result.passed is False
        assert result.feedback == "Issues found"

    def test_parse_raw_json(self) -> None:
        """Test parsing raw JSON without code block."""
        gate = QualityGate()

        response = '{"passed": true, "feedback": "OK", "criteria_results": []}'

        result = gate._parse_response(response)

        assert result.passed is True
        assert result.feedback == "OK"

    def test_parse_missing_passed_field_raises_error(self) -> None:
        """Test that missing 'passed' field raises schema validation error."""
        gate = QualityGate()

        # JSON without 'passed' field - now fails schema validation
        response = '{"feedback": "Some feedback", "criteria_results": []}'

        with pytest.raises(QualityGateError, match="failed schema validation"):
            gate._parse_response(response)

    def test_parse_non_boolean_passed_field_raises_error(self) -> None:
        """Test that non-boolean 'passed' field raises schema validation error."""
        gate = QualityGate()

        # Various truthy but not boolean values - all should fail schema validation
        test_cases = [
            ('{"passed": 1, "feedback": "test", "criteria_results": []}', "integer 1"),
            ('{"passed": "true", "feedback": "test", "criteria_results": []}', "string 'true'"),
            ('{"passed": "yes", "feedback": "test", "criteria_results": []}', "string 'yes'"),
            ('{"passed": null, "feedback": "test", "criteria_results": []}', "null"),
        ]

        for response, case_name in test_cases:
            with pytest.raises(
                QualityGateError, match="failed schema validation"
            ):
                gate._parse_response(response)

    def test_parse_without_schema_validation_is_lenient(self) -> None:
        """Test that schema validation can be disabled for lenient parsing."""
        gate = QualityGate()

        # JSON without 'passed' field - without schema validation, defaults to False
        response = '{"feedback": "Some feedback", "criteria_results": []}'

        result = gate._parse_response(response, validate_schema=False)

        # Without schema validation, missing passed defaults to False (fail-safe)
        assert result.passed is False

    def test_parse_criteria_results_structure(self) -> None:
        """Test that criteria results are properly parsed."""
        gate = QualityGate()

        response = '''```json
{
    "passed": false,
    "feedback": "Two criteria failed",
    "criteria_results": [
        {"criterion": "First check", "passed": true, "feedback": null},
        {"criterion": "Second check", "passed": false, "feedback": "Missing data"},
        {"criterion": "Third check", "passed": false, "feedback": "Wrong format"}
    ]
}
```'''

        result = gate._parse_response(response)

        assert result.passed is False
        assert len(result.criteria_results) == 3
        assert result.criteria_results[0].passed is True
        assert result.criteria_results[0].feedback is None
        assert result.criteria_results[1].passed is False
        assert result.criteria_results[1].feedback == "Missing data"
        assert result.criteria_results[2].passed is False
        assert result.criteria_results[2].feedback == "Wrong format"

    def test_parse_empty_criteria_results(self) -> None:
        """Test parsing with empty criteria results."""
        gate = QualityGate()

        response = '{"passed": true, "feedback": "OK", "criteria_results": []}'

        result = gate._parse_response(response)

        assert result.passed is True
        assert result.criteria_results == []


class TestQualityGateSchemaValidation:
    """Test JSON schema validation for quality gate responses."""

    def test_valid_response_passes_schema(self) -> None:
        """Test that valid response passes schema validation."""
        gate = QualityGate()

        response = '''```json
{
    "passed": true,
    "feedback": "All criteria met",
    "criteria_results": [
        {"criterion": "Test 1", "passed": true, "feedback": null},
        {"criterion": "Test 2", "passed": true}
    ]
}
```'''

        result = gate._parse_response(response)

        assert result.passed is True
        assert result.feedback == "All criteria met"

    def test_missing_feedback_field_raises_error(self) -> None:
        """Test that missing feedback field raises schema error."""
        gate = QualityGate()

        # Missing required 'feedback' field
        response = '{"passed": true, "criteria_results": []}'

        with pytest.raises(QualityGateError, match="failed schema validation"):
            gate._parse_response(response)

    def test_invalid_criteria_result_type_raises_error(self) -> None:
        """Test that invalid criteria_results type raises schema error."""
        gate = QualityGate()

        # criteria_results should be an array, not a string
        response = '{"passed": true, "feedback": "test", "criteria_results": "invalid"}'

        with pytest.raises(QualityGateError, match="failed schema validation"):
            gate._parse_response(response)

    def test_missing_criterion_in_results_raises_error(self) -> None:
        """Test that missing criterion field in results raises schema error."""
        gate = QualityGate()

        # criteria_results item missing required 'criterion' field
        response = '''{"passed": true, "feedback": "test", "criteria_results": [
            {"passed": true, "feedback": null}
        ]}'''

        with pytest.raises(QualityGateError, match="failed schema validation"):
            gate._parse_response(response)

    def test_criteria_results_optional(self) -> None:
        """Test that criteria_results can be omitted."""
        gate = QualityGate()

        # criteria_results is optional
        response = '{"passed": true, "feedback": "All good"}'

        result = gate._parse_response(response)

        assert result.passed is True
        assert result.feedback == "All good"
        assert result.criteria_results == []


class TestQualityGateEdgeCases:
    """Test edge cases and potential failure scenarios."""

    def test_empty_quality_criteria_auto_passes(self, project_root: Path) -> None:
        """Test that no criteria means auto-pass (no subprocess called)."""
        gate = QualityGate(command="nonexistent_command", timeout=30)

        # Even with a command that doesn't exist, empty criteria should auto-pass
        result = gate.evaluate(
            quality_criteria=[],  # No criteria
            outputs=["output.md"],
            project_root=project_root,
        )

        assert result.passed is True
        assert "auto-passing" in result.feedback.lower()

    def test_multiple_output_files(
        self, project_root: Path, mock_agent_command: str
    ) -> None:
        """Test evaluation with multiple output files."""
        gate = QualityGate(command=mock_agent_command, timeout=30)

        # Create multiple output files
        (project_root / "output1.md").write_text("Content 1")
        (project_root / "output2.md").write_text("Content 2")
        (project_root / "output3.md").write_text("Content 3")

        env_backup = os.environ.get("REVIEW_RESULT")
        os.environ["REVIEW_RESULT"] = "pass"

        try:
            result = gate.evaluate(
                quality_criteria=["All outputs must exist"],
                outputs=["output1.md", "output2.md", "output3.md"],
                project_root=project_root,
            )

            assert result.passed is True
        finally:
            if env_backup is not None:
                os.environ["REVIEW_RESULT"] = env_backup
            else:
                os.environ.pop("REVIEW_RESULT", None)

    def test_large_output_file(
        self, project_root: Path, mock_agent_command: str
    ) -> None:
        """Test evaluation with a large output file."""
        gate = QualityGate(command=mock_agent_command, timeout=30)

        # Create a large file (100KB)
        large_content = "Large content line\n" * 5000
        (project_root / "large_output.md").write_text(large_content)

        env_backup = os.environ.get("REVIEW_RESULT")
        os.environ["REVIEW_RESULT"] = "pass"

        try:
            result = gate.evaluate(
                quality_criteria=["Output must be complete"],
                outputs=["large_output.md"],
                project_root=project_root,
            )

            assert result.passed is True
        finally:
            if env_backup is not None:
                os.environ["REVIEW_RESULT"] = env_backup
            else:
                os.environ.pop("REVIEW_RESULT", None)

    def test_unicode_in_output(
        self, project_root: Path, mock_agent_command: str
    ) -> None:
        """Test evaluation with unicode content."""
        gate = QualityGate(command=mock_agent_command, timeout=30)

        # Create file with unicode content
        unicode_content = "Unicode: 你好世界 🚀 émojis and spëcial çharacters"
        (project_root / "unicode_output.md").write_text(unicode_content)

        env_backup = os.environ.get("REVIEW_RESULT")
        os.environ["REVIEW_RESULT"] = "pass"

        try:
            result = gate.evaluate(
                quality_criteria=["Content must be valid"],
                outputs=["unicode_output.md"],
                project_root=project_root,
            )

            assert result.passed is True
        finally:
            if env_backup is not None:
                os.environ["REVIEW_RESULT"] = env_backup
            else:
                os.environ.pop("REVIEW_RESULT", None)
