"""Integration tests for quality gate with review pipeline.

The quality gate now uses the DeepWork Reviews infrastructure instead of
Claude CLI subprocess. These tests verify the integration between the
quality gate and the review pipeline.

These tests are skipped in CI since they validate end-to-end behavior
that depends on file system state and review infrastructure.
"""

from __future__ import annotations

from pathlib import Path

from deepwork.jobs.mcp.quality_gate import (
    build_dynamic_review_rules,
    run_quality_gate,
    validate_json_schemas,
)
from deepwork.jobs.parser import (
    JobDefinition,
    ReviewBlock,
    StepArgument,
    StepOutputRef,
    Workflow,
    WorkflowStep,
)


class TestQualityGatePipelineIntegration:
    """Integration tests for quality gate with the review pipeline."""

    def _make_job(
        self,
        tmp_path: Path,
        review: ReviewBlock | None = None,
        arg_review: ReviewBlock | None = None,
        json_schema: dict | None = None,
    ) -> tuple[WorkflowStep, JobDefinition, Workflow]:
        """Create a minimal job definition for testing."""
        arg = StepArgument(
            name="report",
            description="Report file",
            type="file_path",
            review=arg_review,
            json_schema=json_schema,
        )
        output_ref = StepOutputRef(argument_name="report", required=True, review=review)
        step = WorkflowStep(
            name="write_report",
            instructions="Write a report",
            outputs={"report": output_ref},
        )
        workflow = Workflow(name="main", summary="Test", steps=[step])
        job = JobDefinition(
            name="test_job",
            summary="Test",
            step_arguments=[arg],
            workflows={"main": workflow},
            job_dir=tmp_path,
        )
        return step, job, workflow

    def test_json_schema_validation_catches_invalid_file(self, tmp_path: Path) -> None:
        """Test that json_schema validation catches an invalid JSON file."""
        schema = {
            "type": "object",
            "required": ["title"],
            "properties": {"title": {"type": "string"}},
        }
        step, job, workflow = self._make_job(tmp_path, json_schema=schema)

        # Create a file that doesn't match the schema
        report = tmp_path / "report.json"
        report.write_text('{"content": "no title field"}')

        errors = validate_json_schemas(
            outputs={"report": "report.json"},
            step=step,
            job=job,
            project_root=tmp_path,
        )
        assert len(errors) == 1
        assert "schema validation failed" in errors[0].lower() or "title" in errors[0].lower()

    def test_dynamic_rules_created_from_output_review(self, tmp_path: Path) -> None:
        """Test that review blocks on outputs produce ReviewRule objects."""
        review = ReviewBlock(
            strategy="individual",
            instructions="Check the report for completeness",
        )
        step, job, workflow = self._make_job(tmp_path, review=review)

        rules = build_dynamic_review_rules(
            step=step,
            job=job,
            workflow=workflow,
            outputs={"report": "report.md"},
            input_values={},
            work_summary=None,
            project_root=tmp_path,
        )

        assert len(rules) == 1
        assert rules[0].name == "step_write_report_output_report"
        assert "completeness" in rules[0].instructions

    def test_run_quality_gate_returns_none_when_no_reviews(self, tmp_path: Path) -> None:
        """Test that run_quality_gate returns None when no reviews are configured."""
        step, job, workflow = self._make_job(tmp_path)

        # Create the output file
        report = tmp_path / "report.md"
        report.write_text("# Report\nSome content")

        result = run_quality_gate(
            step=step,
            job=job,
            workflow=workflow,
            outputs={"report": "report.md"},
            input_values={},
            work_summary=None,
            project_root=tmp_path,
        )

        assert result is None
