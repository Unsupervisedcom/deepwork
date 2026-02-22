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

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-004.1.1, REQ-004.1.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_init_no_cli(self) -> None:
        """Test QualityGate with no CLI provided has _cli=None and default max_inline_files."""
        gate = QualityGate()
        assert gate._cli is None
        assert gate.max_inline_files == QualityGate.DEFAULT_MAX_INLINE_FILES

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-004.1.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_init_custom_cli(self, mock_cli: ClaudeCLI) -> None:
        """Test QualityGate uses provided ClaudeCLI."""
        gate = QualityGate(cli=mock_cli)
        assert gate._cli is mock_cli

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-004.2.2, REQ-004.10.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-004.10.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_build_instructions_with_guidance(self, quality_gate: QualityGate) -> None:
        """Test that additional_review_guidance appears in system instructions."""
        instructions = quality_gate._build_instructions(
            quality_criteria={"Valid": "Is it valid?"},
            additional_review_guidance="Read the job.yml file for context.",
        )

        assert "Additional Context" in instructions
        assert "Read the job.yml file for context." in instructions

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-004.10.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_build_instructions_without_guidance(self, quality_gate: QualityGate) -> None:
        """Test that guidance section is absent when not provided."""
        instructions = quality_gate._build_instructions(
            quality_criteria={"Valid": "Is it valid?"},
        )

        assert "Additional Context" not in instructions

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-004.3.1, REQ-004.3.5, REQ-004.3.6, REQ-004.4.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-004.4.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-004.3.1, REQ-004.4.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-004.4.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-004.4.2, REQ-004.4.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-004.3.6).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_build_payload_only_outputs(
        self, quality_gate: QualityGate, project_root: Path
    ) -> None:
        """Test that payload only contains outputs section (no inputs)."""
        (project_root / "output.md").write_text("Output only")

        payload = await quality_gate._build_payload(
            outputs={"report": "output.md"},
            project_root=project_root,
        )

        assert "BEGIN OUTPUTS" in payload
        assert "END OUTPUTS" in payload
        assert "BEGIN INPUTS" not in payload
        assert "END INPUTS" not in payload

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-004.9.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-004.9.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_parse_result_failed(self, quality_gate: QualityGate) -> None:
        """Test parsing failed evaluation data."""
        data = {
            "passed": False,
            "feedback": "Issues found",
            "criteria_results": [{"criterion": "Test 1", "passed": False, "feedback": "Failed"}],
        }

        result = quality_gate._parse_result(data)

        assert result.passed is False
        assert result.feedback == "Issues found"
        assert result.criteria_results[0].passed is False

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-004.9.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-004.6.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-004.2.1, REQ-004.2.2, REQ-004.2.3, REQ-004.2.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-004.6.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_evaluate_wraps_cli_error(self, mock_cli: ClaudeCLI, project_root: Path) -> None:
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-004.2.4, REQ-004.2.5, REQ-004.2.6).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_schema_is_valid_json(self) -> None:
        """Test that QUALITY_GATE_RESPONSE_SCHEMA is valid JSON-serializable."""
        import json

        schema_json = json.dumps(QUALITY_GATE_RESPONSE_SCHEMA)
        assert schema_json
        parsed = json.loads(schema_json)
        assert parsed == QUALITY_GATE_RESPONSE_SCHEMA


class TestEvaluateReviews:
    """Tests for QualityGate.evaluate_reviews method."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-004.7.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_empty_reviews(self, quality_gate: QualityGate, project_root: Path) -> None:
        """Test that empty reviews returns empty list."""
        result = await quality_gate.evaluate_reviews(
            reviews=[],
            outputs={"report": "output.md"},
            output_specs={"report": "file"},
            project_root=project_root,
        )
        assert result == []

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-004.7.3, REQ-004.7.7).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_step_review_passes(self, mock_cli: ClaudeCLI, project_root: Path) -> None:
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-004.7.7).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_step_review_fails(self, mock_cli: ClaudeCLI, project_root: Path) -> None:
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-004.7.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_per_file_review(self, mock_cli: ClaudeCLI, project_root: Path) -> None:
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-004.7.5).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_single_file_review(self, mock_cli: ClaudeCLI, project_root: Path) -> None:
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-004.7.8).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_review_passes_guidance_to_system_prompt(
        self, mock_cli: ClaudeCLI, project_root: Path
    ) -> None:
        """Test that additional_review_guidance is included in the CLI system prompt."""
        mock_cli.run = AsyncMock(
            return_value={"passed": True, "feedback": "OK", "criteria_results": []}
        )
        gate = QualityGate(cli=mock_cli)

        (project_root / "output.md").write_text("content")

        await gate.evaluate_reviews(
            reviews=[
                {
                    "run_each": "step",
                    "quality_criteria": {"Valid": "Is it valid?"},
                    "additional_review_guidance": "Read the job.yml for workflow context.",
                }
            ],
            outputs={"report": "output.md"},
            output_specs={"report": "file"},
            project_root=project_root,
        )

        mock_cli.run.assert_called_once()
        system_prompt = mock_cli.run.call_args.kwargs["system_prompt"]
        assert "Read the job.yml for workflow context." in system_prompt
        assert "Additional Context" in system_prompt

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-004.7.8).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_review_without_guidance_omits_section(
        self, mock_cli: ClaudeCLI, project_root: Path
    ) -> None:
        """Test that reviews without guidance don't include the section."""
        mock_cli.run = AsyncMock(
            return_value={"passed": True, "feedback": "OK", "criteria_results": []}
        )
        gate = QualityGate(cli=mock_cli)

        (project_root / "output.md").write_text("content")

        await gate.evaluate_reviews(
            reviews=[
                {
                    "run_each": "step",
                    "quality_criteria": {"Valid": "Is it valid?"},
                }
            ],
            outputs={"report": "output.md"},
            output_specs={"report": "file"},
            project_root=project_root,
        )

        system_prompt = mock_cli.run.call_args.kwargs["system_prompt"]
        assert "Additional Context" not in system_prompt

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-004.7.4, REQ-004.7.8).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_per_file_review_passes_guidance_to_each(
        self, mock_cli: ClaudeCLI, project_root: Path
    ) -> None:
        """Test that guidance is passed to each per-file review invocation."""
        mock_cli.run = AsyncMock(
            return_value={"passed": True, "feedback": "OK", "criteria_results": []}
        )
        gate = QualityGate(cli=mock_cli)

        (project_root / "a.md").write_text("File A")
        (project_root / "b.md").write_text("File B")

        await gate.evaluate_reviews(
            reviews=[
                {
                    "run_each": "reports",
                    "quality_criteria": {"Valid": "Is it valid?"},
                    "additional_review_guidance": "Check against the spec.",
                }
            ],
            outputs={"reports": ["a.md", "b.md"]},
            output_specs={"reports": "files"},
            project_root=project_root,
        )

        assert mock_cli.run.call_count == 2
        for call in mock_cli.run.call_args_list:
            system_prompt = call.kwargs["system_prompt"]
            assert "Check against the spec." in system_prompt


class TestBuildPayloadLargeFileSet:
    """Tests for _build_payload behavior when file count exceeds max_inline_files."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-004.3.2, REQ-004.3.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_payload_lists_paths_when_over_threshold(
        self, quality_gate: QualityGate, project_root: Path
    ) -> None:
        """Test that >5 files produces path listing instead of inline content."""
        for i in range(6):
            (project_root / f"file{i}.md").write_text(f"Content {i}")

        payload = await quality_gate._build_payload(
            outputs={"reports": [f"file{i}.md" for i in range(6)]},
            project_root=project_root,
        )

        assert "6 files" in payload
        assert "too many to include inline" in payload
        for i in range(6):
            assert f"file{i}.md" in payload
        # Content should NOT be embedded
        assert "Content 0" not in payload
        assert "Content 5" not in payload

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-004.3.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_payload_inlines_content_at_threshold(
        self, quality_gate: QualityGate, project_root: Path
    ) -> None:
        """Test that exactly 5 files still gets inline content."""
        for i in range(5):
            (project_root / f"file{i}.md").write_text(f"Content {i}")

        payload = await quality_gate._build_payload(
            outputs={"reports": [f"file{i}.md" for i in range(5)]},
            project_root=project_root,
        )

        # Should have inline content, not path listing
        assert "too many to include inline" not in payload
        for i in range(5):
            assert f"Content {i}" in payload

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-004.3.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_path_listing_includes_output_names(
        self, quality_gate: QualityGate, project_root: Path
    ) -> None:
        """Test that path listing shows which output each file belongs to."""
        for i in range(4):
            (project_root / f"doc{i}.md").write_text("x")
        for i in range(3):
            (project_root / f"data{i}.csv").write_text("x")

        payload = await quality_gate._build_payload(
            outputs={
                "docs": [f"doc{i}.md" for i in range(4)],
                "data": [f"data{i}.csv" for i in range(3)],
            },
            project_root=project_root,
        )

        assert "7 files" in payload
        assert "(output: docs)" in payload
        assert "(output: data)" in payload

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-004.3.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_path_listing_counts_across_outputs(
        self, quality_gate: QualityGate, project_root: Path
    ) -> None:
        """Test that file count is summed across all outputs."""
        # 3 files in one output + 3 in another = 6 total > 5
        for i in range(3):
            (project_root / f"a{i}.md").write_text("x")
            (project_root / f"b{i}.md").write_text("x")

        payload = await quality_gate._build_payload(
            outputs={
                "alpha": [f"a{i}.md" for i in range(3)],
                "beta": [f"b{i}.md" for i in range(3)],
            },
            project_root=project_root,
        )

        assert "6 files" in payload
        assert "too many to include inline" in payload


class TestBuildPathListing:
    """Tests for _build_path_listing static method."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-004.3.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_single_file_output(self) -> None:
        """Test path listing with single file outputs."""
        lines = QualityGate._build_path_listing({"report": "report.md"})
        assert lines == ["- report.md  (output: report)"]

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-004.3.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_multi_file_output(self) -> None:
        """Test path listing with list outputs."""
        lines = QualityGate._build_path_listing({"reports": ["a.md", "b.md"]})
        assert lines == [
            "- a.md  (output: reports)",
            "- b.md  (output: reports)",
        ]

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-004.3.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_mixed_outputs(self) -> None:
        """Test path listing with both single and list outputs."""
        lines = QualityGate._build_path_listing(
            {
                "summary": "summary.md",
                "details": ["d1.md", "d2.md"],
            }
        )
        assert len(lines) == 3
        assert "- summary.md  (output: summary)" in lines
        assert "- d1.md  (output: details)" in lines
        assert "- d2.md  (output: details)" in lines


class TestComputeTimeout:
    """Tests for QualityGate.compute_timeout."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-004.8.1, REQ-004.8.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_base_timeout_for_few_files(self) -> None:
        """Test that <=5 files gives base 240s (4 min) timeout."""
        assert QualityGate.compute_timeout(0) == 240
        assert QualityGate.compute_timeout(1) == 240
        assert QualityGate.compute_timeout(5) == 240

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-004.8.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_timeout_increases_after_five(self) -> None:
        """Test that each file after 5 adds 30 seconds."""
        assert QualityGate.compute_timeout(6) == 270
        assert QualityGate.compute_timeout(10) == 390  # 240 + 5*30
        assert QualityGate.compute_timeout(20) == 690  # 240 + 15*30


class TestDynamicTimeout:
    """Tests that evaluate passes dynamic timeout to CLI."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-004.6.3, REQ-004.8.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_timeout_passed_to_cli(self, mock_cli: ClaudeCLI, project_root: Path) -> None:
        """Test that evaluate passes computed timeout to CLI.run."""
        gate = QualityGate(cli=mock_cli)

        (project_root / "output.md").write_text("content")

        await gate.evaluate(
            quality_criteria={"Valid": "Is it valid?"},
            outputs={"report": "output.md"},
            project_root=project_root,
        )

        call_kwargs = mock_cli.run.call_args.kwargs
        # 1 file -> timeout = 240
        assert call_kwargs["timeout"] == 240

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-004.6.3, REQ-004.8.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_timeout_scales_with_file_count(
        self, mock_cli: ClaudeCLI, project_root: Path
    ) -> None:
        """Test that timeout increases with many files."""
        gate = QualityGate(cli=mock_cli)

        for i in range(10):
            (project_root / f"f{i}.md").write_text(f"content {i}")

        await gate.evaluate(
            quality_criteria={"Valid": "Is it valid?"},
            outputs={"reports": [f"f{i}.md" for i in range(10)]},
            project_root=project_root,
        )

        call_kwargs = mock_cli.run.call_args.kwargs
        # 10 files -> 240 + 5*30 = 390
        assert call_kwargs["timeout"] == 390


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

    async def test_mock_records_additional_review_guidance(self, project_root: Path) -> None:
        """Test mock gate records additional_review_guidance when provided."""
        gate = MockQualityGate()

        await gate.evaluate(
            quality_criteria={"Check": "Is it good?"},
            outputs={"report": "output.md"},
            project_root=project_root,
            additional_review_guidance="Look at the job.yml for context.",
        )

        assert len(gate.evaluations) == 1
        assert (
            gate.evaluations[0]["additional_review_guidance"] == "Look at the job.yml for context."
        )

    async def test_mock_records_none_guidance_when_omitted(self, project_root: Path) -> None:
        """Test mock gate records None for guidance when not provided."""
        gate = MockQualityGate()

        await gate.evaluate(
            quality_criteria={"Check": "Is it good?"},
            outputs={"report": "output.md"},
            project_root=project_root,
        )

        assert gate.evaluations[0]["additional_review_guidance"] is None


class TestConfigurableMaxInlineFiles:
    """Tests for configurable max_inline_files on QualityGate."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-004.1.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_default_max_inline_files(self) -> None:
        """Test QualityGate defaults to DEFAULT_MAX_INLINE_FILES."""
        gate = QualityGate()
        assert gate.max_inline_files == QualityGate.DEFAULT_MAX_INLINE_FILES
        assert gate.max_inline_files == 5

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-004.1.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_custom_max_inline_files(self) -> None:
        """Test QualityGate respects explicit max_inline_files."""
        gate = QualityGate(max_inline_files=10)
        assert gate.max_inline_files == 10

    def test_zero_max_inline_files(self) -> None:
        """Test QualityGate with max_inline_files=0 always lists paths."""
        gate = QualityGate(max_inline_files=0)
        assert gate.max_inline_files == 0

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-004.1.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_max_inline_files_none_uses_default(self) -> None:
        """Test that passing None explicitly uses the default."""
        gate = QualityGate(max_inline_files=None)
        assert gate.max_inline_files == QualityGate.DEFAULT_MAX_INLINE_FILES

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-004.1.1, REQ-004.1.2, REQ-004.1.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_cli_and_max_inline_files_independent(self, mock_cli: ClaudeCLI) -> None:
        """Test that cli and max_inline_files are independent parameters."""
        gate = QualityGate(cli=mock_cli, max_inline_files=3)
        assert gate._cli is mock_cli
        assert gate.max_inline_files == 3

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-004.3.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_zero_max_inline_always_lists_paths(self, project_root: Path) -> None:
        """Test that max_inline_files=0 uses path listing even for 1 file."""
        gate = QualityGate(max_inline_files=0)
        (project_root / "single.md").write_text("Single file content")

        payload = await gate._build_payload(
            outputs={"report": "single.md"},
            project_root=project_root,
        )

        assert "too many to include inline" in payload
        assert "single.md" in payload
        assert "Single file content" not in payload

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-004.3.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_high_max_inline_embeds_many_files(self, project_root: Path) -> None:
        """Test that a high max_inline_files embeds content for many files."""
        gate = QualityGate(max_inline_files=100)
        for i in range(10):
            (project_root / f"f{i}.md").write_text(f"Embedded content {i}")

        payload = await gate._build_payload(
            outputs={"files": [f"f{i}.md" for i in range(10)]},
            project_root=project_root,
        )

        assert "too many to include inline" not in payload
        for i in range(10):
            assert f"Embedded content {i}" in payload


class TestEvaluateWithoutCli:
    """Tests that evaluate() raises when no CLI is configured."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-004.1.6, REQ-004.6.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_evaluate_raises_without_cli(self, project_root: Path) -> None:
        """Test that evaluate raises QualityGateError when _cli is None."""
        gate = QualityGate(cli=None)
        (project_root / "output.md").write_text("content")

        with pytest.raises(QualityGateError, match="Cannot evaluate.*without a CLI runner"):
            await gate.evaluate(
                quality_criteria={"Valid": "Is it valid?"},
                outputs={"report": "output.md"},
                project_root=project_root,
            )

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-004.6.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_evaluate_no_criteria_still_passes_without_cli(self, project_root: Path) -> None:
        """Test that empty criteria auto-passes even without CLI."""
        gate = QualityGate(cli=None)

        result = await gate.evaluate(
            quality_criteria={},
            outputs={"report": "output.md"},
            project_root=project_root,
        )

        assert result.passed is True
        assert "auto-passing" in result.feedback.lower()


class TestBuildReviewInstructionsFile:
    """Tests for QualityGate.build_review_instructions_file method."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-004.5.1, REQ-004.5.6, REQ-004.5.7, REQ-004.10.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_basic_structure(self, project_root: Path) -> None:
        """Test that the instructions file has the expected structure."""
        gate = QualityGate(max_inline_files=0)
        (project_root / "output.md").write_text("content")

        content = await gate.build_review_instructions_file(
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

        assert "# Quality Review Instructions" in content
        assert "editor" in content.lower()
        assert "BEGIN OUTPUTS" in content
        assert "END OUTPUTS" in content
        assert "Complete" in content
        assert "Is it complete?" in content
        assert "## Guidelines" in content
        assert "## Your Task" in content
        assert "PASS" in content
        assert "FAIL" in content

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-004.10.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_contains_all_criteria(self, project_root: Path) -> None:
        """Test that all criteria from all reviews appear in the file."""
        gate = QualityGate(max_inline_files=0)
        (project_root / "out.md").write_text("x")

        content = await gate.build_review_instructions_file(
            reviews=[
                {
                    "run_each": "step",
                    "quality_criteria": {
                        "Accuracy": "Are the facts correct?",
                        "Completeness": "Is all data present?",
                    },
                }
            ],
            outputs={"report": "out.md"},
            output_specs={"report": "file"},
            project_root=project_root,
        )

        assert "**Accuracy**" in content
        assert "Are the facts correct?" in content
        assert "**Completeness**" in content
        assert "Is all data present?" in content

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-004.5.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_multiple_reviews_numbered(self, project_root: Path) -> None:
        """Test that multiple reviews get numbered sections."""
        gate = QualityGate(max_inline_files=0)
        (project_root / "out.md").write_text("x")

        content = await gate.build_review_instructions_file(
            reviews=[
                {
                    "run_each": "step",
                    "quality_criteria": {"First": "First check?"},
                },
                {
                    "run_each": "report",
                    "quality_criteria": {"Second": "Second check?"},
                },
            ],
            outputs={"report": "out.md"},
            output_specs={"report": "file"},
            project_root=project_root,
        )

        assert "## Review 1" in content
        assert "## Review 2" in content
        assert "scope: all outputs together" in content
        assert "scope: output 'report'" in content

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-004.5.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_single_review_not_numbered(self, project_root: Path) -> None:
        """Test that a single review uses 'Criteria to Evaluate' heading."""
        gate = QualityGate(max_inline_files=0)
        (project_root / "out.md").write_text("x")

        content = await gate.build_review_instructions_file(
            reviews=[
                {
                    "run_each": "step",
                    "quality_criteria": {"Only": "Only check?"},
                }
            ],
            outputs={"report": "out.md"},
            output_specs={"report": "file"},
            project_root=project_root,
        )

        assert "## Criteria to Evaluate" in content
        assert "Review 1" not in content

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-004.5.9, REQ-004.10.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_includes_author_notes(self, project_root: Path) -> None:
        """Test that notes are included when provided."""
        gate = QualityGate(max_inline_files=0)
        (project_root / "out.md").write_text("x")

        content = await gate.build_review_instructions_file(
            reviews=[
                {
                    "run_each": "step",
                    "quality_criteria": {"Check": "Is it ok?"},
                }
            ],
            outputs={"report": "out.md"},
            output_specs={"report": "file"},
            project_root=project_root,
            notes="I focused on section 3 the most.",
        )

        assert "## Author Notes" in content
        assert "I focused on section 3 the most." in content

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-004.5.9).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_excludes_notes_when_none(self, project_root: Path) -> None:
        """Test that notes section is absent when not provided."""
        gate = QualityGate(max_inline_files=0)
        (project_root / "out.md").write_text("x")

        content = await gate.build_review_instructions_file(
            reviews=[
                {
                    "run_each": "step",
                    "quality_criteria": {"Check": "Is it ok?"},
                }
            ],
            outputs={"report": "out.md"},
            output_specs={"report": "file"},
            project_root=project_root,
        )

        assert "## Author Notes" not in content

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-004.5.5, REQ-004.10.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_includes_guidance(self, project_root: Path) -> None:
        """Test that additional_review_guidance is included."""
        gate = QualityGate(max_inline_files=0)
        (project_root / "out.md").write_text("x")

        content = await gate.build_review_instructions_file(
            reviews=[
                {
                    "run_each": "step",
                    "quality_criteria": {"Check": "Is it ok?"},
                    "additional_review_guidance": "Also read config.yml for context.",
                }
            ],
            outputs={"report": "out.md"},
            output_specs={"report": "file"},
            project_root=project_root,
        )

        assert "### Additional Context" in content
        assert "Also read config.yml for context." in content

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-004.5.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_per_file_review_lists_files(self, project_root: Path) -> None:
        """Test that per-file reviews list each file to evaluate."""
        gate = QualityGate(max_inline_files=0)
        (project_root / "a.md").write_text("x")
        (project_root / "b.md").write_text("x")

        content = await gate.build_review_instructions_file(
            reviews=[
                {
                    "run_each": "pages",
                    "quality_criteria": {"Valid": "Is it valid?"},
                }
            ],
            outputs={"pages": ["a.md", "b.md"]},
            output_specs={"pages": "files"},
            project_root=project_root,
        )

        assert "each file" in content.lower()
        assert "a.md" in content
        assert "b.md" in content

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-004.3.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    async def test_output_paths_listed_not_inlined_at_zero(self, project_root: Path) -> None:
        """Test that with max_inline_files=0, file contents are NOT embedded."""
        gate = QualityGate(max_inline_files=0)
        (project_root / "report.md").write_text("SECRET_CONTENT_MARKER")

        content = await gate.build_review_instructions_file(
            reviews=[
                {
                    "run_each": "step",
                    "quality_criteria": {"Check": "Is it ok?"},
                }
            ],
            outputs={"report": "report.md"},
            output_specs={"report": "file"},
            project_root=project_root,
        )

        assert "report.md" in content
        assert "SECRET_CONTENT_MARKER" not in content
        assert "too many to include inline" in content
