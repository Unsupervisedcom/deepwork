"""Tests for MCP quality gate (reviews-based implementation)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from deepwork.jobs.mcp.quality_gate import (
    build_dynamic_review_rules,
    run_quality_gate,
    validate_json_schemas,
)
from deepwork.jobs.parser import (
    JobDefinition,
    ReviewBlock,
    StepArgument,
    StepInputRef,
    StepOutputRef,
    Workflow,
    WorkflowStep,
)
from deepwork.review.config import ReviewRule, ReviewTask

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_job(
    tmp_path: Path,
    step_arguments: list[StepArgument],
    step: WorkflowStep,
) -> tuple[JobDefinition, Workflow]:
    """Build a minimal JobDefinition and Workflow for testing."""
    workflow = Workflow(name="main", summary="Test workflow", steps=[step])
    job = JobDefinition(
        name="test_job",
        summary="Test job",
        step_arguments=step_arguments,
        workflows={"main": workflow},
        job_dir=tmp_path / ".deepwork" / "jobs" / "test_job",
    )
    job.job_dir.mkdir(parents=True, exist_ok=True)
    return job, workflow


# ---------------------------------------------------------------------------
# TestValidateJsonSchemas
# ---------------------------------------------------------------------------


class TestValidateJsonSchemas:
    """Tests for validate_json_schemas."""

    def test_passes_when_no_json_schema_defined(self, tmp_path: Path) -> None:
        """No json_schema on the argument means nothing to validate."""
        arg = StepArgument(name="report", description="Report file", type="file_path")
        output_ref = StepOutputRef(argument_name="report", required=True)
        step = WorkflowStep(name="write", outputs={"report": output_ref})
        job, _ = _make_job(tmp_path, [arg], step)

        report_path = tmp_path / "report.md"
        report_path.write_text("some content")

        errors = validate_json_schemas({"report": "report.md"}, step, job, tmp_path)
        assert errors == []

    def test_passes_when_json_schema_validates(self, tmp_path: Path) -> None:
        """Valid JSON matching the schema produces no errors."""
        schema = {
            "type": "object",
            "properties": {"title": {"type": "string"}},
            "required": ["title"],
        }
        arg = StepArgument(
            name="data", description="JSON data", type="file_path", json_schema=schema
        )
        output_ref = StepOutputRef(argument_name="data", required=True)
        step = WorkflowStep(name="generate", outputs={"data": output_ref})
        job, _ = _make_job(tmp_path, [arg], step)

        data_file = tmp_path / "data.json"
        data_file.write_text(json.dumps({"title": "Hello"}))

        errors = validate_json_schemas({"data": "data.json"}, step, job, tmp_path)
        assert errors == []

    def test_fails_when_json_is_invalid(self, tmp_path: Path) -> None:
        """Non-JSON content in the output file produces an error."""
        schema = {"type": "object"}
        arg = StepArgument(
            name="data", description="JSON data", type="file_path", json_schema=schema
        )
        output_ref = StepOutputRef(argument_name="data", required=True)
        step = WorkflowStep(name="generate", outputs={"data": output_ref})
        job, _ = _make_job(tmp_path, [arg], step)

        data_file = tmp_path / "data.json"
        data_file.write_text("not json {{{")

        errors = validate_json_schemas({"data": "data.json"}, step, job, tmp_path)
        assert len(errors) == 1
        assert "failed to parse as JSON" in errors[0]

    def test_fails_when_schema_validation_fails(self, tmp_path: Path) -> None:
        """JSON that doesn't match the schema produces an error."""
        schema = {
            "type": "object",
            "properties": {"count": {"type": "integer"}},
            "required": ["count"],
        }
        arg = StepArgument(
            name="data", description="JSON data", type="file_path", json_schema=schema
        )
        output_ref = StepOutputRef(argument_name="data", required=True)
        step = WorkflowStep(name="generate", outputs={"data": output_ref})
        job, _ = _make_job(tmp_path, [arg], step)

        data_file = tmp_path / "data.json"
        data_file.write_text(json.dumps({"count": "not_an_integer"}))

        errors = validate_json_schemas({"data": "data.json"}, step, job, tmp_path)
        assert len(errors) == 1
        assert "schema validation failed" in errors[0]

    def test_skips_string_type_arguments(self, tmp_path: Path) -> None:
        """String-type arguments are skipped even if json_schema is set."""
        schema = {"type": "object"}
        arg = StepArgument(
            name="data", description="String data", type="string", json_schema=schema
        )
        output_ref = StepOutputRef(argument_name="data", required=True)
        step = WorkflowStep(name="generate", outputs={"data": output_ref})
        job, _ = _make_job(tmp_path, [arg], step)

        errors = validate_json_schemas({"data": "just a string value"}, step, job, tmp_path)
        assert errors == []


# ---------------------------------------------------------------------------
# TestBuildDynamicReviewRules
# ---------------------------------------------------------------------------


class TestBuildDynamicReviewRules:
    """Tests for build_dynamic_review_rules."""

    def test_creates_rules_from_output_level_review(self, tmp_path: Path) -> None:
        """A review block on the output ref creates a ReviewRule."""
        review = ReviewBlock(strategy="individual", instructions="Check the report")
        arg = StepArgument(name="report", description="Report file", type="file_path")
        output_ref = StepOutputRef(argument_name="report", required=True, review=review)
        step = WorkflowStep(name="write_report", outputs={"report": output_ref})
        job, workflow = _make_job(tmp_path, [arg], step)

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
        assert rules[0].strategy == "individual"
        assert "Check the report" in rules[0].instructions
        assert rules[0].include_patterns == ["report.md"]

    def test_creates_rules_from_step_argument_level_review(self, tmp_path: Path) -> None:
        """A review block on the step_argument (not the output ref) creates a rule."""
        arg_review = ReviewBlock(strategy="matches_together", instructions="Verify data")
        arg = StepArgument(
            name="report", description="Report file", type="file_path", review=arg_review
        )
        output_ref = StepOutputRef(argument_name="report", required=True)
        step = WorkflowStep(name="write_report", outputs={"report": output_ref})
        job, workflow = _make_job(tmp_path, [arg], step)

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
        # When only arg-level review exists (index 0), no _arg suffix
        assert rules[0].name == "step_write_report_output_report"
        assert rules[0].strategy == "matches_together"
        assert "Verify data" in rules[0].instructions

    def test_creates_both_output_and_arg_level_rules(self, tmp_path: Path) -> None:
        """Both output-level and argument-level reviews produce separate rules."""
        output_review = ReviewBlock(strategy="individual", instructions="Output check")
        arg_review = ReviewBlock(strategy="matches_together", instructions="Arg check")
        arg = StepArgument(name="report", description="Report", type="file_path", review=arg_review)
        output_ref = StepOutputRef(argument_name="report", required=True, review=output_review)
        step = WorkflowStep(name="write", outputs={"report": output_ref})
        job, workflow = _make_job(tmp_path, [arg], step)

        rules = build_dynamic_review_rules(
            step=step,
            job=job,
            workflow=workflow,
            outputs={"report": "report.md"},
            input_values={},
            work_summary=None,
            project_root=tmp_path,
        )

        assert len(rules) == 2
        assert rules[0].name == "step_write_output_report"
        assert rules[1].name == "step_write_output_report_arg"

    def test_creates_process_quality_attributes_rules(self, tmp_path: Path) -> None:
        """process_quality_attributes with a work_summary creates a PQA rule."""
        arg = StepArgument(name="report", description="Report file", type="file_path")
        output_ref = StepOutputRef(argument_name="report", required=True)
        step = WorkflowStep(
            name="analyze",
            outputs={"report": output_ref},
            process_quality_attributes={
                "accuracy": "All data points are verified",
                "completeness": "All sections are filled",
            },
        )
        job, workflow = _make_job(tmp_path, [arg], step)

        rules = build_dynamic_review_rules(
            step=step,
            job=job,
            workflow=workflow,
            outputs={"report": "report.md"},
            input_values={},
            work_summary="I analyzed the data and wrote the report.",
            project_root=tmp_path,
        )

        assert len(rules) == 1
        rule = rules[0]
        assert rule.name == "step_analyze_process_quality"
        assert rule.strategy == "matches_together"
        assert "accuracy" in rule.instructions
        assert "completeness" in rule.instructions
        assert "I analyzed the data and wrote the report." in rule.instructions

    def test_no_pqa_rule_without_work_summary(self, tmp_path: Path) -> None:
        """process_quality_attributes without a work_summary are skipped."""
        arg = StepArgument(name="report", description="Report", type="file_path")
        output_ref = StepOutputRef(argument_name="report", required=True)
        step = WorkflowStep(
            name="analyze",
            outputs={"report": output_ref},
            process_quality_attributes={"accuracy": "Check it"},
        )
        job, workflow = _make_job(tmp_path, [arg], step)

        rules = build_dynamic_review_rules(
            step=step,
            job=job,
            workflow=workflow,
            outputs={"report": "report.md"},
            input_values={},
            work_summary=None,
            project_root=tmp_path,
        )

        assert rules == []

    def test_no_rules_when_no_reviews_defined(self, tmp_path: Path) -> None:
        """No review blocks and no PQA means no rules."""
        arg = StepArgument(name="report", description="Report file", type="file_path")
        output_ref = StepOutputRef(argument_name="report", required=True)
        step = WorkflowStep(name="write", outputs={"report": output_ref})
        job, workflow = _make_job(tmp_path, [arg], step)

        rules = build_dynamic_review_rules(
            step=step,
            job=job,
            workflow=workflow,
            outputs={"report": "report.md"},
            input_values={},
            work_summary=None,
            project_root=tmp_path,
        )

        assert rules == []

    def test_includes_input_context_in_review_instructions(self, tmp_path: Path) -> None:
        """Input values are included as context in the review instructions."""
        review = ReviewBlock(strategy="individual", instructions="Review the report")
        input_arg = StepArgument(name="topic", description="Research topic", type="string")
        output_arg = StepArgument(name="report", description="Report", type="file_path")
        input_ref = StepInputRef(argument_name="topic", required=True)
        output_ref = StepOutputRef(argument_name="report", required=True, review=review)
        step = WorkflowStep(
            name="write",
            inputs={"topic": input_ref},
            outputs={"report": output_ref},
        )
        job, workflow = _make_job(tmp_path, [input_arg, output_arg], step)

        rules = build_dynamic_review_rules(
            step=step,
            job=job,
            workflow=workflow,
            outputs={"report": "report.md"},
            input_values={"topic": "AI safety"},
            work_summary=None,
            project_root=tmp_path,
        )

        assert len(rules) == 1
        assert "topic" in rules[0].instructions
        assert "AI safety" in rules[0].instructions

    def test_includes_common_job_info_in_instructions(self, tmp_path: Path) -> None:
        """common_job_info from workflow is included in rule instructions."""
        review = ReviewBlock(strategy="individual", instructions="Check it")
        arg = StepArgument(name="report", description="Report", type="file_path")
        output_ref = StepOutputRef(argument_name="report", required=True, review=review)
        step = WorkflowStep(name="write", outputs={"report": output_ref})
        workflow = Workflow(
            name="main",
            summary="Test",
            steps=[step],
            common_job_info="This job is about competitive analysis.",
        )
        job = JobDefinition(
            name="test_job",
            summary="Test",
            step_arguments=[arg],
            workflows={"main": workflow},
            job_dir=tmp_path / ".deepwork" / "jobs" / "test_job",
        )
        job.job_dir.mkdir(parents=True, exist_ok=True)

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
        assert "competitive analysis" in rules[0].instructions


# ---------------------------------------------------------------------------
# TestRunQualityGate
# ---------------------------------------------------------------------------


class TestRunQualityGate:
    """Tests for run_quality_gate."""

    def test_returns_none_when_no_reviews_needed(self, tmp_path: Path) -> None:
        """No review blocks, no PQA, no .deepreview files => None."""
        arg = StepArgument(name="report", description="Report file", type="file_path")
        output_ref = StepOutputRef(argument_name="report", required=True)
        step = WorkflowStep(name="write", outputs={"report": output_ref})
        job, workflow = _make_job(tmp_path, [arg], step)

        report_path = tmp_path / "report.md"
        report_path.write_text("content")

        with patch("deepwork.jobs.mcp.quality_gate.load_all_rules", return_value=([], [])):
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

    def test_returns_none_when_no_review_blocks_defined(self, tmp_path: Path) -> None:
        """Outputs exist but have no review blocks and no .deepreview rules."""
        arg = StepArgument(name="data", description="Data file", type="file_path")
        output_ref = StepOutputRef(argument_name="data", required=True)
        step = WorkflowStep(name="process", outputs={"data": output_ref})
        job, workflow = _make_job(tmp_path, [arg], step)

        data_file = tmp_path / "data.json"
        data_file.write_text("{}")

        with patch("deepwork.jobs.mcp.quality_gate.load_all_rules", return_value=([], [])):
            result = run_quality_gate(
                step=step,
                job=job,
                workflow=workflow,
                outputs={"data": "data.json"},
                input_values={},
                work_summary=None,
                project_root=tmp_path,
            )

        assert result is None

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-001.4.8).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_returns_feedback_when_json_schema_fails(self, tmp_path: Path) -> None:
        """Schema validation failure returns an error string without running reviews."""
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }
        arg = StepArgument(
            name="data", description="JSON data", type="file_path", json_schema=schema
        )
        output_ref = StepOutputRef(argument_name="data", required=True)
        step = WorkflowStep(name="generate", outputs={"data": output_ref})
        job, workflow = _make_job(tmp_path, [arg], step)

        data_file = tmp_path / "data.json"
        data_file.write_text(json.dumps({"wrong_field": 123}))

        result = run_quality_gate(
            step=step,
            job=job,
            workflow=workflow,
            outputs={"data": "data.json"},
            input_values={},
            work_summary=None,
            project_root=tmp_path,
        )

        assert result is not None
        assert "JSON schema validation failed" in result
        assert "finished_step" in result

    def test_returns_review_instructions_when_reviews_exist(self, tmp_path: Path) -> None:
        """When dynamic rules produce tasks, review instructions are returned."""
        review = ReviewBlock(strategy="individual", instructions="Check quality")
        arg = StepArgument(name="report", description="Report", type="file_path")
        output_ref = StepOutputRef(argument_name="report", required=True, review=review)
        step = WorkflowStep(name="write", outputs={"report": output_ref})
        job, workflow = _make_job(tmp_path, [arg], step)

        report_file = tmp_path / "report.md"
        report_file.write_text("Report content")

        mock_task = ReviewTask(
            rule_name="step_write_output_report",
            files_to_review=["report.md"],
            instructions="Check quality",
            agent_name=None,
        )
        instruction_path = tmp_path / ".deepwork" / "tmp" / "review_instruction.md"
        instruction_path.parent.mkdir(parents=True, exist_ok=True)
        instruction_path.write_text("Review instruction content")

        with (
            patch(
                "deepwork.jobs.mcp.quality_gate.load_all_rules",
                return_value=([], []),
            ),
            patch(
                "deepwork.jobs.mcp.quality_gate.match_files_to_rules",
                return_value=[mock_task],
            ),
            patch(
                "deepwork.jobs.mcp.quality_gate.write_instruction_files",
                return_value=[(mock_task, instruction_path)],
            ),
            patch(
                "deepwork.jobs.mcp.quality_gate.format_for_claude",
                return_value="## Review Tasks\n\n- Task: step_write_output_report",
            ),
        ):
            result = run_quality_gate(
                step=step,
                job=job,
                workflow=workflow,
                outputs={"report": "report.md"},
                input_values={},
                work_summary=None,
                project_root=tmp_path,
            )

        assert result is not None
        assert "Quality reviews are required" in result
        assert "step_write_output_report" in result

    def test_returns_none_when_all_reviews_already_passed(self, tmp_path: Path) -> None:
        """If write_instruction_files returns empty (all .passed), result is None."""
        review = ReviewBlock(strategy="individual", instructions="Check it")
        arg = StepArgument(name="report", description="Report", type="file_path")
        output_ref = StepOutputRef(argument_name="report", required=True, review=review)
        step = WorkflowStep(name="write", outputs={"report": output_ref})
        job, workflow = _make_job(tmp_path, [arg], step)

        mock_task = ReviewTask(
            rule_name="step_write_output_report",
            files_to_review=["report.md"],
            instructions="Check it",
            agent_name=None,
        )

        with (
            patch(
                "deepwork.jobs.mcp.quality_gate.load_all_rules",
                return_value=([], []),
            ),
            patch(
                "deepwork.jobs.mcp.quality_gate.match_files_to_rules",
                return_value=[mock_task],
            ),
            patch(
                "deepwork.jobs.mcp.quality_gate.write_instruction_files",
                return_value=[],
            ),
        ):
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

    def test_merges_deepreview_and_dynamic_tasks(self, tmp_path: Path) -> None:
        """Both .deepreview rules and dynamic rules are processed together."""
        review = ReviewBlock(strategy="individual", instructions="Check it")
        arg = StepArgument(name="report", description="Report", type="file_path")
        output_ref = StepOutputRef(argument_name="report", required=True, review=review)
        step = WorkflowStep(name="write", outputs={"report": output_ref})
        job, workflow = _make_job(tmp_path, [arg], step)

        deepreview_rule = ReviewRule(
            name="external_rule",
            description="From .deepreview",
            include_patterns=["*.md"],
            exclude_patterns=[],
            strategy="individual",
            instructions="External check",
            agent=None,
            all_changed_filenames=False,
            unchanged_matching_files=False,
            source_dir=tmp_path,
            source_file=tmp_path / ".deepreview",
            source_line=1,
        )

        dynamic_task = ReviewTask(
            rule_name="step_write_output_report",
            files_to_review=["report.md"],
            instructions="Check it",
            agent_name=None,
        )
        deepreview_task = ReviewTask(
            rule_name="external_rule",
            files_to_review=["report.md"],
            instructions="External check",
            agent_name=None,
        )
        instruction_path = tmp_path / ".deepwork" / "tmp" / "instr.md"
        instruction_path.parent.mkdir(parents=True, exist_ok=True)
        instruction_path.write_text("content")

        # match_files_to_rules is called twice: first for deepreview (step 5), then dynamic (step 6)
        with (
            patch(
                "deepwork.jobs.mcp.quality_gate.load_all_rules",
                return_value=([deepreview_rule], []),
            ),
            patch(
                "deepwork.jobs.mcp.quality_gate.match_files_to_rules",
                side_effect=[[deepreview_task], [dynamic_task]],
            ),
            patch(
                "deepwork.jobs.mcp.quality_gate.write_instruction_files",
                return_value=[
                    (dynamic_task, instruction_path),
                    (deepreview_task, instruction_path),
                ],
            ) as mock_write,
            patch(
                "deepwork.jobs.mcp.quality_gate.format_for_claude",
                return_value="formatted output",
            ),
        ):
            result = run_quality_gate(
                step=step,
                job=job,
                workflow=workflow,
                outputs={"report": "report.md"},
                input_values={},
                work_summary=None,
                project_root=tmp_path,
            )

        # write_instruction_files should receive both tasks (dynamic first, then deepreview)
        all_tasks = mock_write.call_args[0][0]
        assert len(all_tasks) == 2
        assert all_tasks[0].rule_name == "step_write_output_report"
        assert all_tasks[1].rule_name == "external_rule"
        assert result is not None
