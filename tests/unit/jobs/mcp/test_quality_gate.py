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

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-004.2.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-004.2.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-004.2.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-004.2.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-004.2.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-004.3.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-004.3.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-004.3.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-004.4.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_creates_process_requirements_rules(self, tmp_path: Path) -> None:
        """process_requirements with a work_summary creates a process requirements rule."""
        arg = StepArgument(name="report", description="Report file", type="file_path")
        output_ref = StepOutputRef(argument_name="report", required=True)
        step = WorkflowStep(
            name="analyze",
            outputs={"report": output_ref},
            process_requirements={
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-004.4.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_no_pqa_rule_without_work_summary(self, tmp_path: Path) -> None:
        """process_requirements without a work_summary is skipped."""
        arg = StepArgument(name="report", description="Report", type="file_path")
        output_ref = StepOutputRef(argument_name="report", required=True)
        step = WorkflowStep(
            name="analyze",
            outputs={"report": output_ref},
            process_requirements={"accuracy": "Check it"},
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-004.3.5).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-004.7.1, JOBS-REQ-004.3.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-004.3.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-004.1.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-004.1.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-004.1.3, JOBS-REQ-004.5.7, JOBS-REQ-004.6.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-004.5.6).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-004.5.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
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


# ---------------------------------------------------------------------------
# TestValidateJsonSchemas — additional coverage
# ---------------------------------------------------------------------------


class TestValidateJsonSchemasExtra:
    """Additional tests for validate_json_schemas to cover missing lines."""

    def test_skips_nonexistent_file(self, tmp_path: Path) -> None:
        """When the output file doesn't exist on disk, it is silently skipped (line 60)."""
        schema = {"type": "object"}
        arg = StepArgument(
            name="data", description="JSON data", type="file_path", json_schema=schema
        )
        output_ref = StepOutputRef(argument_name="data", required=True)
        step = WorkflowStep(name="generate", outputs={"data": output_ref})
        job, _ = _make_job(tmp_path, [arg], step)

        # Do NOT create the file — it should be skipped
        errors = validate_json_schemas({"data": "nonexistent.json"}, step, job, tmp_path)
        assert errors == []

    def test_validates_list_of_file_paths(self, tmp_path: Path) -> None:
        """When the output value is a list of paths, each file is validated."""
        schema = {
            "type": "object",
            "properties": {"x": {"type": "integer"}},
            "required": ["x"],
        }
        arg = StepArgument(
            name="data", description="JSON files", type="file_path", json_schema=schema
        )
        output_ref = StepOutputRef(argument_name="data", required=True)
        step = WorkflowStep(name="gen", outputs={"data": output_ref})
        job, _ = _make_job(tmp_path, [arg], step)

        # One valid, one invalid
        (tmp_path / "good.json").write_text(json.dumps({"x": 1}))
        (tmp_path / "bad.json").write_text(json.dumps({"x": "not_int"}))

        errors = validate_json_schemas(
            {"data": ["good.json", "bad.json"]}, step, job, tmp_path
        )
        assert len(errors) == 1
        assert "bad.json" in errors[0]


# ---------------------------------------------------------------------------
# TestCollectOutputFilePaths
# ---------------------------------------------------------------------------


class TestCollectOutputFilePaths:
    """Tests for _collect_output_file_paths."""

    def test_skips_unknown_argument(self, tmp_path: Path) -> None:
        """Outputs whose argument is not found in the job are skipped (line 86->84)."""
        from deepwork.jobs.mcp.quality_gate import _collect_output_file_paths

        arg = StepArgument(name="known", description="Known", type="file_path")
        output_ref = StepOutputRef(argument_name="known", required=True)
        step = WorkflowStep(name="s", outputs={"known": output_ref})
        job, _ = _make_job(tmp_path, [arg], step)

        # "unknown" has no matching argument
        paths = _collect_output_file_paths({"known": "a.md", "unknown": "b.md"}, job)
        assert paths == ["a.md"]

    def test_handles_list_value(self, tmp_path: Path) -> None:
        """List values for file_path outputs are extended into the result (line 88)."""
        from deepwork.jobs.mcp.quality_gate import _collect_output_file_paths

        arg = StepArgument(name="files", description="Files", type="file_path")
        output_ref = StepOutputRef(argument_name="files", required=True)
        step = WorkflowStep(name="s", outputs={"files": output_ref})
        job, _ = _make_job(tmp_path, [arg], step)

        paths = _collect_output_file_paths({"files": ["a.md", "b.md"]}, job)
        assert paths == ["a.md", "b.md"]

    def test_skips_string_type_argument(self, tmp_path: Path) -> None:
        """String-type arguments are not collected as file paths."""
        from deepwork.jobs.mcp.quality_gate import _collect_output_file_paths

        arg = StepArgument(name="summary", description="Summary", type="string")
        output_ref = StepOutputRef(argument_name="summary", required=True)
        step = WorkflowStep(name="s", outputs={"summary": output_ref})
        job, _ = _make_job(tmp_path, [arg], step)

        paths = _collect_output_file_paths({"summary": "some text"}, job)
        assert paths == []


# ---------------------------------------------------------------------------
# TestBuildInputContext
# ---------------------------------------------------------------------------


class TestBuildInputContext:
    """Tests for _build_input_context."""

    def test_skips_unknown_input_argument(self, tmp_path: Path) -> None:
        """Input whose argument doesn't exist in job is skipped (line 109)."""
        from deepwork.jobs.mcp.quality_gate import _build_input_context

        # Step references "missing_arg" but job has no such argument
        input_ref = StepInputRef(argument_name="missing_arg", required=True)
        step = WorkflowStep(name="s", inputs={"missing_arg": input_ref}, outputs={})
        job, _ = _make_job(tmp_path, [], step)

        result = _build_input_context(step, job, {"missing_arg": "val"})
        # Should contain the header but no input entries
        assert "Step Inputs" in result
        assert "missing_arg" not in result.split("Step Inputs")[1]

    def test_renders_file_path_list_input(self, tmp_path: Path) -> None:
        """File-path list inputs render as comma-separated @-prefixed paths (lines 118-120)."""
        from deepwork.jobs.mcp.quality_gate import _build_input_context

        arg = StepArgument(name="refs", description="Ref files", type="file_path")
        input_ref = StepInputRef(argument_name="refs", required=True)
        step = WorkflowStep(name="s", inputs={"refs": input_ref}, outputs={})
        job, _ = _make_job(tmp_path, [arg], step)

        result = _build_input_context(step, job, {"refs": ["a.md", "b.md"]})
        assert "@a.md" in result
        assert "@b.md" in result

    def test_renders_file_path_single_input(self, tmp_path: Path) -> None:
        """File-path single input renders as @path (lines 121-122)."""
        from deepwork.jobs.mcp.quality_gate import _build_input_context

        arg = StepArgument(name="ref", description="Ref file", type="file_path")
        input_ref = StepInputRef(argument_name="ref", required=True)
        step = WorkflowStep(name="s", inputs={"ref": input_ref}, outputs={})
        job, _ = _make_job(tmp_path, [arg], step)

        result = _build_input_context(step, job, {"ref": "report.md"})
        assert "@report.md" in result


# ---------------------------------------------------------------------------
# TestBuildDynamicReviewRules — additional coverage
# ---------------------------------------------------------------------------


class TestBuildDynamicReviewRulesExtra:
    """Additional tests for build_dynamic_review_rules to cover missing lines."""

    def test_skips_output_with_unknown_argument(self, tmp_path: Path) -> None:
        """When a step output's argument is not found in job, it is skipped (line 162)."""
        review = ReviewBlock(strategy="individual", instructions="Check it")
        # Define a step with an output that references "missing" argument
        output_ref = StepOutputRef(argument_name="missing", required=True, review=review)
        step = WorkflowStep(name="write", outputs={"missing": output_ref})
        # Job has no "missing" argument
        job, workflow = _make_job(tmp_path, [], step)

        rules = build_dynamic_review_rules(
            step=step, job=job, workflow=workflow,
            outputs={"missing": "file.md"},
            input_values={}, work_summary=None, project_root=tmp_path,
        )
        assert rules == []

    def test_skips_output_with_none_value(self, tmp_path: Path) -> None:
        """When the output value is None, it is skipped (line 177)."""
        review = ReviewBlock(strategy="individual", instructions="Check it")
        arg = StepArgument(name="report", description="Report", type="file_path")
        output_ref = StepOutputRef(argument_name="report", required=True, review=review)
        step = WorkflowStep(name="write", outputs={"report": output_ref})
        job, workflow = _make_job(tmp_path, [arg], step)

        rules = build_dynamic_review_rules(
            step=step, job=job, workflow=workflow,
            outputs={},  # "report" not in outputs -> value is None
            input_values={}, work_summary=None, project_root=tmp_path,
        )
        assert rules == []

    def test_string_output_with_review_produces_no_file_rule(self, tmp_path: Path) -> None:
        """String-type output with a review block has empty file_paths (line 184)."""
        review = ReviewBlock(strategy="individual", instructions="Check summary")
        arg = StepArgument(name="summary", description="Summary", type="string")
        output_ref = StepOutputRef(argument_name="summary", required=True, review=review)
        step = WorkflowStep(name="write", outputs={"summary": output_ref})
        job, workflow = _make_job(tmp_path, [arg], step)

        rules = build_dynamic_review_rules(
            step=step, job=job, workflow=workflow,
            outputs={"summary": "I did the work"},
            input_values={}, work_summary=None, project_root=tmp_path,
        )
        # String type has empty file_paths, so no rule is created (line 197 check)
        assert rules == []

    def test_process_requirements_with_list_file_and_string_outputs(self, tmp_path: Path) -> None:
        """Process requirements correctly render list file_path and string outputs (lines 235-240)."""
        file_arg = StepArgument(name="files", description="Files", type="file_path")
        str_arg = StepArgument(name="note", description="Note", type="string")
        file_ref = StepOutputRef(argument_name="files", required=True)
        str_ref = StepOutputRef(argument_name="note", required=True)
        step = WorkflowStep(
            name="analyze",
            outputs={"files": file_ref, "note": str_ref},
            process_requirements={"done": "Must be done"},
        )
        job, workflow = _make_job(tmp_path, [file_arg, str_arg], step)

        rules = build_dynamic_review_rules(
            step=step, job=job, workflow=workflow,
            outputs={"files": ["a.md", "b.md"], "note": "all good"},
            input_values={}, work_summary="Did the work",
            project_root=tmp_path,
        )

        assert len(rules) == 1
        rule = rules[0]
        assert "step_analyze_process_quality" == rule.name
        assert "@a.md" in rule.instructions
        assert "@b.md" in rule.instructions
        assert "all good" in rule.instructions

    def test_process_requirements_skipped_when_no_output_paths(self, tmp_path: Path) -> None:
        """When there are no file_path outputs, PQA rule is not created (line 269->286)."""
        str_arg = StepArgument(name="note", description="Note", type="string")
        str_ref = StepOutputRef(argument_name="note", required=True)
        step = WorkflowStep(
            name="analyze",
            outputs={"note": str_ref},
            process_requirements={"done": "Must be done"},
        )
        job, workflow = _make_job(tmp_path, [str_arg], step)

        rules = build_dynamic_review_rules(
            step=step, job=job, workflow=workflow,
            outputs={"note": "text"},
            input_values={}, work_summary="Did stuff",
            project_root=tmp_path,
        )
        assert rules == []


# ---------------------------------------------------------------------------
# TestRunQualityGate — additional coverage
# ---------------------------------------------------------------------------


class TestRunQualityGateExtra:
    """Additional tests for run_quality_gate to cover edge cases."""

    def test_no_deepreview_rules_and_no_output_files_skips_matching(self, tmp_path: Path) -> None:
        """When there are no output files, matching is skipped (line 333->339)."""
        # Use string-type output only — no file paths
        str_arg = StepArgument(name="note", description="Note", type="string")
        output_ref = StepOutputRef(argument_name="note", required=True)
        step = WorkflowStep(name="write", outputs={"note": output_ref})
        job, workflow = _make_job(tmp_path, [str_arg], step)

        with patch("deepwork.jobs.mcp.quality_gate.load_all_rules", return_value=([], [])):
            result = run_quality_gate(
                step=step, job=job, workflow=workflow,
                outputs={"note": "some text"},
                input_values={}, work_summary=None,
                project_root=tmp_path,
            )

        assert result is None
