"""Tests for MCP quality gate (reviews-based implementation).

Validates requirements: JOBS-REQ-004, JOBS-REQ-004.1, JOBS-REQ-004.2, JOBS-REQ-004.3,
JOBS-REQ-004.4, JOBS-REQ-004.5, JOBS-REQ-004.6, JOBS-REQ-004.7.

Note: JOBS-REQ-009 is DEPRECATED (superseded by JOBS-REQ-004). No tests required.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from deepwork.jobs.mcp.quality_gate import (
    build_dynamic_review_rules,
    build_string_output_review_tasks,
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
from deepwork.review.instructions import INSTRUCTIONS_DIR, compute_review_id

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
    def test_fails_when_file_is_unparseable(self, tmp_path: Path) -> None:
        """Unparseable content in the output file produces an error."""
        schema = {"type": "object"}
        arg = StepArgument(
            name="data", description="data file", type="file_path", json_schema=schema
        )
        output_ref = StepOutputRef(argument_name="data", required=True)
        step = WorkflowStep(name="generate", outputs={"data": output_ref})
        job, _ = _make_job(tmp_path, [arg], step)

        data_file = tmp_path / "data.yml"
        data_file.write_text(":\n  bad: [yaml\n  unclosed")

        errors = validate_json_schemas({"data": "data.yml"}, step, job, tmp_path)
        assert len(errors) == 1
        assert "failed to parse" in errors[0]

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

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-004.2.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_passes_when_yaml_file_matches_schema(self, tmp_path: Path) -> None:
        """YAML files should be parsed with yaml.safe_load, not json.loads."""
        schema = {
            "type": "object",
            "properties": {"title": {"type": "string"}},
            "required": ["title"],
        }
        arg = StepArgument(
            name="data", description="YAML data", type="file_path", json_schema=schema
        )
        output_ref = StepOutputRef(argument_name="data", required=True)
        step = WorkflowStep(name="generate", outputs={"data": output_ref})
        job, _ = _make_job(tmp_path, [arg], step)

        data_file = tmp_path / "data.yml"
        data_file.write_text("title: Hello\n")

        errors = validate_json_schemas({"data": "data.yml"}, step, job, tmp_path)
        assert errors == []

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-004.2.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_fails_when_yaml_file_violates_schema(self, tmp_path: Path) -> None:
        """YAML files that don't match the schema produce errors."""
        schema = {
            "type": "object",
            "properties": {"count": {"type": "integer"}},
            "required": ["count"],
        }
        arg = StepArgument(
            name="data", description="YAML data", type="file_path", json_schema=schema
        )
        output_ref = StepOutputRef(argument_name="data", required=True)
        step = WorkflowStep(name="generate", outputs={"data": output_ref})
        job, _ = _make_job(tmp_path, [arg], step)

        data_file = tmp_path / "data.yaml"
        data_file.write_text("count: not_an_integer\n")

        errors = validate_json_schemas({"data": "data.yaml"}, step, job, tmp_path)
        assert len(errors) == 1
        assert "schema validation failed" in errors[0]


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

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-004.2.6).
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-004.1.3, JOBS-REQ-004.5.9, JOBS-REQ-004.6.1).
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-004.5.8).
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-004.5.5).
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
            precomputed_info_bash_command=None,
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
                "deepwork.jobs.mcp.quality_gate.get_changed_files",
                return_value=["report.md"],
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-004.5.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_deepreview_rules_skip_unchanged_output_files(self, tmp_path: Path) -> None:
        """Deepreview rules should only match output files that are actually changed in git."""
        arg = StepArgument(name="refs", description="Reference files", type="file_path")
        output_ref = StepOutputRef(argument_name="refs", required=False)
        step = WorkflowStep(name="explore", outputs={"refs": output_ref})
        job, workflow = _make_job(tmp_path, [arg], step)

        deepreview_rule = ReviewRule(
            name="python_lint",
            description="Lint Python files",
            include_patterns=["**/*.py"],
            exclude_patterns=[],
            strategy="matches_together",
            instructions="Run linting",
            agent=None,
            all_changed_filenames=False,
            unchanged_matching_files=False,
            precomputed_info_bash_command=None,
            source_dir=tmp_path,
            source_file=tmp_path / ".deepreview",
            source_line=1,
        )

        with (
            patch(
                "deepwork.jobs.mcp.quality_gate.load_all_rules",
                return_value=([deepreview_rule], []),
            ),
            # git says no files changed — output files are just references
            patch(
                "deepwork.jobs.mcp.quality_gate.get_changed_files",
                return_value=[],
            ),
            patch(
                "deepwork.jobs.mcp.quality_gate.match_files_to_rules",
            ) as mock_match,
        ):
            result = run_quality_gate(
                step=step,
                job=job,
                workflow=workflow,
                outputs={"refs": ["src/foo.py", "src/bar.py"]},
                input_values={},
                work_summary=None,
                project_root=tmp_path,
            )

        # match_files_to_rules should not be called for deepreview since
        # no output files are in the git changed set
        assert mock_match.call_count == 0
        assert result is None

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-004.5.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_dynamic_rules_match_all_outputs_regardless_of_git(self, tmp_path: Path) -> None:
        """Dynamic rules run against all output files even when git says nothing changed."""
        review = ReviewBlock(strategy="individual", instructions="Check it")
        arg = StepArgument(name="report", description="Report", type="file_path")
        output_ref = StepOutputRef(argument_name="report", required=True, review=review)
        step = WorkflowStep(name="write", outputs={"report": output_ref})
        job, workflow = _make_job(tmp_path, [arg], step)

        dynamic_task = ReviewTask(
            rule_name="step_write_output_report",
            files_to_review=["report.md"],
            instructions="Check it",
            agent_name=None,
        )
        instruction_path = tmp_path / ".deepwork" / "tmp" / "instr.md"
        instruction_path.parent.mkdir(parents=True, exist_ok=True)
        instruction_path.write_text("content")

        with (
            patch(
                "deepwork.jobs.mcp.quality_gate.load_all_rules",
                return_value=([], []),
            ),
            patch(
                "deepwork.jobs.mcp.quality_gate.match_files_to_rules",
                return_value=[dynamic_task],
            ) as mock_match,
            patch(
                "deepwork.jobs.mcp.quality_gate.write_instruction_files",
                return_value=[(dynamic_task, instruction_path)],
            ),
            patch(
                "deepwork.jobs.mcp.quality_gate.format_for_claude",
                return_value="formatted",
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

        # Dynamic rules matched even though no deepreview rules exist and
        # get_changed_files was never called (no deepreview rules to trigger it)
        mock_match.assert_called_once()
        assert result is not None

    def test_uses_openclaw_formatter_when_requested(self, tmp_path: Path) -> None:
        """OpenClaw quality-gate output uses the OpenClaw formatter, not Claude's."""
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

        def openclaw_formatter(*_args: object, **_kwargs: object) -> str:
            return "openclaw formatted output"

        def claude_formatter(*_args: object, **_kwargs: object) -> str:
            return "claude formatted output"

        with (
            patch("deepwork.jobs.mcp.quality_gate.load_all_rules", return_value=([], [])),
            patch(
                "deepwork.jobs.mcp.quality_gate.match_files_to_rules",
                return_value=[mock_task],
            ),
            patch(
                "deepwork.jobs.mcp.quality_gate.write_instruction_files",
                return_value=[(mock_task, instruction_path)],
            ),
            patch.dict(
                "deepwork.jobs.mcp.quality_gate.FORMATTERS",
                {"claude": claude_formatter, "openclaw": openclaw_formatter},
                clear=False,
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
                platform="openclaw",
            )

        assert result is not None
        assert "openclaw formatted output" in result
        assert "claude formatted output" not in result
        assert "sessions_spawn" in result
        assert "sessions_yield" in result
        assert "Do not set `timeoutSeconds`" in result

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-004.5.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_deepreview_skipped_when_get_changed_files_fails(self, tmp_path: Path) -> None:
        """If get_changed_files() fails, .deepreview matching is skipped; dynamic rules unaffected."""
        review = ReviewBlock(strategy="individual", instructions="Check it")
        arg = StepArgument(name="report", description="Report", type="file_path")
        output_ref = StepOutputRef(argument_name="report", required=True, review=review)
        step = WorkflowStep(name="write", outputs={"report": output_ref})
        job, workflow = _make_job(tmp_path, [arg], step)

        deepreview_rule = ReviewRule(
            name="lint",
            description="Lint",
            include_patterns=["*.md"],
            exclude_patterns=[],
            strategy="individual",
            instructions="Lint it",
            agent=None,
            all_changed_filenames=False,
            unchanged_matching_files=False,
            precomputed_info_bash_command=None,
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
        instruction_path = tmp_path / ".deepwork" / "tmp" / "instr.md"
        instruction_path.parent.mkdir(parents=True, exist_ok=True)
        instruction_path.write_text("content")

        from deepwork.review.matcher import GitDiffError

        with (
            patch(
                "deepwork.jobs.mcp.quality_gate.load_all_rules",
                return_value=([deepreview_rule], []),
            ),
            patch(
                "deepwork.jobs.mcp.quality_gate.get_changed_files",
                side_effect=GitDiffError("git not available"),
            ),
            patch(
                "deepwork.jobs.mcp.quality_gate.match_files_to_rules",
                return_value=[dynamic_task],
            ) as mock_match,
            patch(
                "deepwork.jobs.mcp.quality_gate.write_instruction_files",
                return_value=[(dynamic_task, instruction_path)],
            ),
            patch(
                "deepwork.jobs.mcp.quality_gate.format_for_claude",
                return_value="formatted",
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

        # match_files_to_rules called only once (for dynamic rules, not deepreview)
        mock_match.assert_called_once()
        assert result is not None


# ---------------------------------------------------------------------------
# TestValidateJsonSchemas — additional coverage
# ---------------------------------------------------------------------------


class TestValidateJsonSchemasExtra:
    """Additional tests for validate_json_schemas to cover missing lines."""

    def test_skips_nonexistent_file(self, tmp_path: Path) -> None:
        """When the output file doesn't exist on disk, it is silently skipped."""
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

        errors = validate_json_schemas({"data": ["good.json", "bad.json"]}, step, job, tmp_path)
        assert len(errors) == 1
        assert "bad.json" in errors[0]


# ---------------------------------------------------------------------------
# TestCollectOutputFilePaths
# ---------------------------------------------------------------------------


class TestCollectOutputFilePaths:
    """Tests for _collect_output_file_paths."""

    def test_skips_unknown_argument(self, tmp_path: Path) -> None:
        """Outputs whose argument is not found in the job are skipped."""
        from deepwork.jobs.mcp.quality_gate import _collect_output_file_paths

        arg = StepArgument(name="known", description="Known", type="file_path")
        output_ref = StepOutputRef(argument_name="known", required=True)
        step = WorkflowStep(name="s", outputs={"known": output_ref})
        job, _ = _make_job(tmp_path, [arg], step)

        # "unknown" has no matching argument
        paths = _collect_output_file_paths({"known": "a.md", "unknown": "b.md"}, job)
        assert paths == ["a.md"]

    def test_handles_list_value(self, tmp_path: Path) -> None:
        """List values for file_path outputs are extended into the result."""
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
        """Input whose argument doesn't exist in job is skipped."""
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
        """File-path list inputs render as comma-separated @-prefixed paths."""
        from deepwork.jobs.mcp.quality_gate import _build_input_context

        arg = StepArgument(name="refs", description="Ref files", type="file_path")
        input_ref = StepInputRef(argument_name="refs", required=True)
        step = WorkflowStep(name="s", inputs={"refs": input_ref}, outputs={})
        job, _ = _make_job(tmp_path, [arg], step)

        result = _build_input_context(step, job, {"refs": ["a.md", "b.md"]})
        assert "@a.md" in result
        assert "@b.md" in result

    def test_renders_file_path_single_input(self, tmp_path: Path) -> None:
        """File-path single input renders as @path."""
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
        """When a step output's argument is not found in job, it is skipped."""
        review = ReviewBlock(strategy="individual", instructions="Check it")
        # Define a step with an output that references "missing" argument
        output_ref = StepOutputRef(argument_name="missing", required=True, review=review)
        step = WorkflowStep(name="write", outputs={"missing": output_ref})
        # Job has no "missing" argument
        job, workflow = _make_job(tmp_path, [], step)

        rules = build_dynamic_review_rules(
            step=step,
            job=job,
            workflow=workflow,
            outputs={"missing": "file.md"},
            input_values={},
            work_summary=None,
            project_root=tmp_path,
        )
        assert rules == []

    def test_skips_output_with_none_value(self, tmp_path: Path) -> None:
        """When the output value is None, it is skipped."""
        review = ReviewBlock(strategy="individual", instructions="Check it")
        arg = StepArgument(name="report", description="Report", type="file_path")
        output_ref = StepOutputRef(argument_name="report", required=True, review=review)
        step = WorkflowStep(name="write", outputs={"report": output_ref})
        job, workflow = _make_job(tmp_path, [arg], step)

        rules = build_dynamic_review_rules(
            step=step,
            job=job,
            workflow=workflow,
            outputs={},  # "report" not in outputs -> value is None
            input_values={},
            work_summary=None,
            project_root=tmp_path,
        )
        assert rules == []

    def test_string_output_with_review_produces_no_rule_in_build_dynamic(
        self, tmp_path: Path
    ) -> None:
        """String-type outputs do not produce ReviewRule objects.

        ReviewRule is for file-pattern matching; string outputs flow through
        build_string_output_review_tasks() instead (see JOBS-REQ-004.8).
        """
        review = ReviewBlock(strategy="individual", instructions="Check summary")
        arg = StepArgument(name="summary", description="Summary", type="string")
        output_ref = StepOutputRef(argument_name="summary", required=True, review=review)
        step = WorkflowStep(name="write", outputs={"summary": output_ref})
        job, workflow = _make_job(tmp_path, [arg], step)

        rules = build_dynamic_review_rules(
            step=step,
            job=job,
            workflow=workflow,
            outputs={"summary": "I did the work"},
            input_values={},
            work_summary=None,
            project_root=tmp_path,
        )
        # String type has empty file_paths, so no ReviewRule is created
        assert rules == []

    def test_process_requirements_with_list_file_and_string_outputs(self, tmp_path: Path) -> None:
        """Process requirements correctly render list file_path and string outputs."""
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
            step=step,
            job=job,
            workflow=workflow,
            outputs={"files": ["a.md", "b.md"], "note": "all good"},
            input_values={},
            work_summary="Did the work",
            project_root=tmp_path,
        )

        assert len(rules) == 1
        rule = rules[0]
        assert "step_analyze_process_quality" == rule.name
        assert "@a.md" in rule.instructions
        assert "@b.md" in rule.instructions
        assert "all good" in rule.instructions

    def test_process_requirements_skipped_when_no_output_paths(self, tmp_path: Path) -> None:
        """When there are no file_path outputs, PQA rule is not created."""
        str_arg = StepArgument(name="note", description="Note", type="string")
        str_ref = StepOutputRef(argument_name="note", required=True)
        step = WorkflowStep(
            name="analyze",
            outputs={"note": str_ref},
            process_requirements={"done": "Must be done"},
        )
        job, workflow = _make_job(tmp_path, [str_arg], step)

        rules = build_dynamic_review_rules(
            step=step,
            job=job,
            workflow=workflow,
            outputs={"note": "text"},
            input_values={},
            work_summary="Did stuff",
            project_root=tmp_path,
        )
        assert rules == []


# ---------------------------------------------------------------------------
# TestRunQualityGate — additional coverage
# ---------------------------------------------------------------------------


class TestRunQualityGateExtra:
    """Additional tests for run_quality_gate to cover edge cases."""

    def test_no_deepreview_rules_and_no_output_files_skips_matching(self, tmp_path: Path) -> None:
        """When there are no output files, matching is skipped."""
        # Use string-type output only — no file paths
        str_arg = StepArgument(name="note", description="Note", type="string")
        output_ref = StepOutputRef(argument_name="note", required=True)
        step = WorkflowStep(name="write", outputs={"note": output_ref})
        job, workflow = _make_job(tmp_path, [str_arg], step)

        with patch("deepwork.jobs.mcp.quality_gate.load_all_rules", return_value=([], [])):
            result = run_quality_gate(
                step=step,
                job=job,
                workflow=workflow,
                outputs={"note": "some text"},
                input_values={},
                work_summary=None,
                project_root=tmp_path,
            )

        assert result is None


class TestBuildStringOutputReviewTasks:
    """Tests for build_string_output_review_tasks — validates JOBS-REQ-004.8."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-004.8.1, JOBS-REQ-004.8.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_output_level_review_produces_inline_task(self, tmp_path: Path) -> None:
        """A review block on a string output-ref produces a synthetic ReviewTask."""
        review = ReviewBlock(strategy="individual", instructions="Check the summary")
        arg = StepArgument(name="summary", description="Summary", type="string")
        output_ref = StepOutputRef(argument_name="summary", required=True, review=review)
        step = WorkflowStep(name="write", outputs={"summary": output_ref})
        job, workflow = _make_job(tmp_path, [arg], step)

        tasks = build_string_output_review_tasks(
            step=step,
            job=job,
            workflow=workflow,
            outputs={"summary": "I did the research and found X."},
            input_values={},
            project_root=tmp_path,
        )

        assert len(tasks) == 1
        task = tasks[0]
        assert task.rule_name == "step_write_output_summary"
        assert task.files_to_review == []
        assert task.inline_content == "I did the research and found X."
        assert "Check the summary" in task.instructions

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-004.8.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_argument_level_review_produces_inline_task(self, tmp_path: Path) -> None:
        """A review block on the step_argument (not the output-ref) produces a task."""
        arg_review = ReviewBlock(strategy="matches_together", instructions="Verify the note")
        arg = StepArgument(name="note", description="Note", type="string", review=arg_review)
        output_ref = StepOutputRef(argument_name="note", required=True)
        step = WorkflowStep(name="write", outputs={"note": output_ref})
        job, workflow = _make_job(tmp_path, [arg], step)

        tasks = build_string_output_review_tasks(
            step=step,
            job=job,
            workflow=workflow,
            outputs={"note": "all good"},
            input_values={},
            project_root=tmp_path,
        )

        assert len(tasks) == 1
        # When only arg-level review exists (index 0), no _arg suffix
        assert tasks[0].rule_name == "step_write_output_note"
        assert tasks[0].inline_content == "all good"
        assert "Verify the note" in tasks[0].instructions

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-004.8.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_both_output_and_arg_level_reviews_produce_separate_tasks(self, tmp_path: Path) -> None:
        """Output-level and arg-level reviews on the same string output both execute."""
        output_review = ReviewBlock(strategy="individual", instructions="Output check")
        arg_review = ReviewBlock(strategy="individual", instructions="Arg check")
        arg = StepArgument(name="summary", description="Summary", type="string", review=arg_review)
        output_ref = StepOutputRef(argument_name="summary", required=True, review=output_review)
        step = WorkflowStep(name="write", outputs={"summary": output_ref})
        job, workflow = _make_job(tmp_path, [arg], step)

        tasks = build_string_output_review_tasks(
            step=step,
            job=job,
            workflow=workflow,
            outputs={"summary": "the value"},
            input_values={},
            project_root=tmp_path,
        )

        assert len(tasks) == 2
        assert tasks[0].rule_name == "step_write_output_summary"
        assert tasks[1].rule_name == "step_write_output_summary_arg"

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-004.8.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_preamble_includes_common_job_info_and_inputs(self, tmp_path: Path) -> None:
        """The synthetic task's instructions include common_job_info and step inputs."""
        review = ReviewBlock(strategy="individual", instructions="Check it")
        input_arg = StepArgument(name="topic", description="Topic", type="string")
        output_arg = StepArgument(name="summary", description="Summary", type="string")
        input_ref = StepInputRef(argument_name="topic", required=True)
        output_ref = StepOutputRef(argument_name="summary", required=True, review=review)
        step = WorkflowStep(
            name="write",
            inputs={"topic": input_ref},
            outputs={"summary": output_ref},
        )
        workflow = Workflow(
            name="main",
            summary="Test",
            steps=[step],
            common_job_info="This job analyses narrative summaries.",
        )
        job = JobDefinition(
            name="test_job",
            summary="Test",
            step_arguments=[input_arg, output_arg],
            workflows={"main": workflow},
            job_dir=tmp_path / ".deepwork" / "jobs" / "test_job",
        )
        job.job_dir.mkdir(parents=True, exist_ok=True)

        tasks = build_string_output_review_tasks(
            step=step,
            job=job,
            workflow=workflow,
            outputs={"summary": "done"},
            input_values={"topic": "AI safety"},
            project_root=tmp_path,
        )

        assert len(tasks) == 1
        assert "narrative summaries" in tasks[0].instructions
        assert "topic" in tasks[0].instructions
        assert "AI safety" in tasks[0].instructions

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-004.8.5).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_none_value_skipped(self, tmp_path: Path) -> None:
        """String outputs without a value do not produce synthetic tasks."""
        review = ReviewBlock(strategy="individual", instructions="Check it")
        arg = StepArgument(name="summary", description="Summary", type="string")
        output_ref = StepOutputRef(argument_name="summary", required=True, review=review)
        step = WorkflowStep(name="write", outputs={"summary": output_ref})
        job, workflow = _make_job(tmp_path, [arg], step)

        tasks = build_string_output_review_tasks(
            step=step,
            job=job,
            workflow=workflow,
            outputs={},  # no value for "summary"
            input_values={},
            project_root=tmp_path,
        )
        assert tasks == []

    def test_file_path_outputs_are_ignored(self, tmp_path: Path) -> None:
        """file_path outputs do not flow through this function."""
        review = ReviewBlock(strategy="individual", instructions="Check it")
        arg = StepArgument(name="report", description="Report", type="file_path")
        output_ref = StepOutputRef(argument_name="report", required=True, review=review)
        step = WorkflowStep(name="write", outputs={"report": output_ref})
        job, workflow = _make_job(tmp_path, [arg], step)

        tasks = build_string_output_review_tasks(
            step=step,
            job=job,
            workflow=workflow,
            outputs={"report": "report.md"},
            input_values={},
            project_root=tmp_path,
        )
        assert tasks == []

    def test_no_review_block_skipped(self, tmp_path: Path) -> None:
        """String outputs without any review block produce no tasks."""
        arg = StepArgument(name="summary", description="Summary", type="string")
        output_ref = StepOutputRef(argument_name="summary", required=True)  # no review
        step = WorkflowStep(name="write", outputs={"summary": output_ref})
        job, workflow = _make_job(tmp_path, [arg], step)

        tasks = build_string_output_review_tasks(
            step=step,
            job=job,
            workflow=workflow,
            outputs={"summary": "value"},
            input_values={},
            project_root=tmp_path,
        )
        assert tasks == []

    def test_agent_name_resolved_from_review_block(self, tmp_path: Path) -> None:
        """When the review block specifies an agent for the target platform, it flows through."""
        review = ReviewBlock(
            strategy="individual",
            instructions="Check it",
            agent={"claude": "string-reviewer"},
        )
        arg = StepArgument(name="summary", description="Summary", type="string")
        output_ref = StepOutputRef(argument_name="summary", required=True, review=review)
        step = WorkflowStep(name="write", outputs={"summary": output_ref})
        job, workflow = _make_job(tmp_path, [arg], step)

        tasks = build_string_output_review_tasks(
            step=step,
            job=job,
            workflow=workflow,
            outputs={"summary": "value"},
            input_values={},
            project_root=tmp_path,
            platform="claude",
        )
        assert len(tasks) == 1
        assert tasks[0].agent_name == "string-reviewer"

    def test_job_dir_outside_project_root_falls_back(self, tmp_path: Path) -> None:
        """When job.job_dir is not under project_root, source_location falls back to the absolute path."""
        review = ReviewBlock(strategy="individual", instructions="Check it")
        arg = StepArgument(name="summary", description="Summary", type="string")
        output_ref = StepOutputRef(argument_name="summary", required=True, review=review)
        step = WorkflowStep(name="write", outputs={"summary": output_ref})
        # job.job_dir lives in a sibling directory, NOT under tmp_path
        outside = tmp_path.parent / f"outside_{tmp_path.name}"
        outside.mkdir()
        workflow = Workflow(name="main", summary="Test", steps=[step])
        job = JobDefinition(
            name="test_job",
            summary="Test",
            step_arguments=[arg],
            workflows={"main": workflow},
            job_dir=outside / ".deepwork" / "jobs" / "test_job",
        )

        tasks = build_string_output_review_tasks(
            step=step,
            job=job,
            workflow=workflow,
            outputs={"summary": "value"},
            input_values={},
            project_root=tmp_path,
        )
        assert len(tasks) == 1
        # source_location falls back to the absolute job.yml path
        assert str(outside) in tasks[0].source_location
        assert tasks[0].source_location.endswith("job.yml:0")


class TestRunQualityGateStringOutputs:
    """End-to-end tests: run_quality_gate emits reviews for string outputs.

    Validates JOBS-REQ-004.8.1 — string output reviews are not silently dropped.
    """

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-004.8.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_string_output_review_produces_instructions(self, tmp_path: Path) -> None:
        """run_quality_gate returns guidance when a string output has a review block."""
        review = ReviewBlock(strategy="individual", instructions="Check the summary value")
        arg = StepArgument(name="summary", description="Summary", type="string")
        output_ref = StepOutputRef(argument_name="summary", required=True, review=review)
        step = WorkflowStep(name="write", outputs={"summary": output_ref})
        job, workflow = _make_job(tmp_path, [arg], step)

        with patch("deepwork.jobs.mcp.quality_gate.load_all_rules", return_value=([], [])):
            result = run_quality_gate(
                step=step,
                job=job,
                workflow=workflow,
                outputs={"summary": "processed 42 documents"},
                input_values={},
                work_summary=None,
                project_root=tmp_path,
            )

        assert result is not None
        assert "Quality reviews are required" in result

        # The generated instruction file must include the string value
        instructions_dir = tmp_path / ".deepwork" / "tmp" / "review_instructions"
        md_files = list(instructions_dir.glob("*.md"))
        assert len(md_files) == 1
        body = md_files[0].read_text()
        assert "## Content to Review" in body
        assert "processed 42 documents" in body
        assert "Check the summary value" in body
        # No Files to Review section for inline-content tasks
        assert "## Files to Review" not in body

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-004.8.6).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_passed_marker_skips_string_review_on_same_value(self, tmp_path: Path) -> None:
        """A .passed marker for an inline review is honored when the value is unchanged."""
        review = ReviewBlock(strategy="individual", instructions="Check it")
        arg = StepArgument(name="summary", description="Summary", type="string")
        output_ref = StepOutputRef(argument_name="summary", required=True, review=review)
        step = WorkflowStep(name="write", outputs={"summary": output_ref})
        job, workflow = _make_job(tmp_path, [arg], step)

        # First run: produces a task and writes the instruction file.
        with patch("deepwork.jobs.mcp.quality_gate.load_all_rules", return_value=([], [])):
            first = run_quality_gate(
                step=step,
                job=job,
                workflow=workflow,
                outputs={"summary": "cached value"},
                input_values={},
                work_summary=None,
                project_root=tmp_path,
            )
        assert first is not None

        # Drop a .passed marker next to the instruction file.
        instructions_dir = tmp_path / ".deepwork" / "tmp" / "review_instructions"
        md_files = list(instructions_dir.glob("*.md"))
        assert len(md_files) == 1
        review_id = md_files[0].stem
        (instructions_dir / f"{review_id}.passed").write_bytes(b"")

        # Second run with the same value — should be skipped by the cache.
        with patch("deepwork.jobs.mcp.quality_gate.load_all_rules", return_value=([], [])):
            second = run_quality_gate(
                step=step,
                job=job,
                workflow=workflow,
                outputs={"summary": "cached value"},
                input_values={},
                work_summary=None,
                project_root=tmp_path,
            )
        assert second is None

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-004.8.6).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_changed_string_value_invalidates_cache(self, tmp_path: Path) -> None:
        """Changing the string value produces a new review_id so the cache is bypassed."""
        review = ReviewBlock(strategy="individual", instructions="Check it")
        arg = StepArgument(name="summary", description="Summary", type="string")
        output_ref = StepOutputRef(argument_name="summary", required=True, review=review)
        step = WorkflowStep(name="write", outputs={"summary": output_ref})
        job, workflow = _make_job(tmp_path, [arg], step)

        # Run with value A and mark as passed.
        with patch("deepwork.jobs.mcp.quality_gate.load_all_rules", return_value=([], [])):
            run_quality_gate(
                step=step,
                job=job,
                workflow=workflow,
                outputs={"summary": "value A"},
                input_values={},
                work_summary=None,
                project_root=tmp_path,
            )
        instructions_dir = tmp_path / ".deepwork" / "tmp" / "review_instructions"
        md_files = list(instructions_dir.glob("*.md"))
        assert len(md_files) == 1
        review_id_a = md_files[0].stem
        (instructions_dir / f"{review_id_a}.passed").write_bytes(b"")

        # Run with value B — different review_id, so review runs again.
        with patch("deepwork.jobs.mcp.quality_gate.load_all_rules", return_value=([], [])):
            result = run_quality_gate(
                step=step,
                job=job,
                workflow=workflow,
                outputs={"summary": "value B"},
                input_values={},
                work_summary=None,
                project_root=tmp_path,
            )
        assert result is not None
        assert "Quality reviews are required" in result


class TestQualityGatePassCaching:
    """Tests for JOBS-REQ-004.5.7: quality gate skips reviews with .passed markers."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-004.5.7).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_skips_review_when_passed_marker_exists_for_unchanged_file(
        self, tmp_path: Path
    ) -> None:
        """Quality gate returns None when a .passed marker exists for the exact content.

        This is an integration test that does NOT mock write_instruction_files —
        it creates a real .passed marker file and verifies the caching mechanism
        works end-to-end through the quality gate.
        """
        review = ReviewBlock(strategy="individual", instructions="Check it")
        arg = StepArgument(name="report", description="Report", type="file_path")
        output_ref = StepOutputRef(argument_name="report", required=True, review=review)
        step = WorkflowStep(name="write", outputs={"report": output_ref})
        job, workflow = _make_job(tmp_path, [arg], step)

        # Create the output file with known content
        report_path = tmp_path / "report.md"
        report_path.write_text("Report content here")

        # Build the ReviewTask that the quality gate would produce
        task = ReviewTask(
            rule_name="step_write_output_report",
            files_to_review=[str(report_path)],
            instructions="Check it",
            agent_name=None,
        )

        # Compute the review_id for this task and create a .passed marker
        review_id = compute_review_id(task, tmp_path)
        instructions_dir = tmp_path / INSTRUCTIONS_DIR
        instructions_dir.mkdir(parents=True, exist_ok=True)
        (instructions_dir / f"{review_id}.passed").write_bytes(b"")

        with (
            patch(
                "deepwork.jobs.mcp.quality_gate.load_all_rules",
                return_value=([], []),
            ),
            patch(
                "deepwork.jobs.mcp.quality_gate.match_files_to_rules",
                return_value=[task],
            ),
        ):
            result = run_quality_gate(
                step=step,
                job=job,
                workflow=workflow,
                outputs={"report": str(report_path)},
                input_values={},
                work_summary=None,
                project_root=tmp_path,
            )

        assert result is None

    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-004.5.7).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_reruns_review_when_file_content_changes_after_pass(self, tmp_path: Path) -> None:
        """Quality gate runs review again when file content changes after a prior pass.

        Verifies that changing file content produces a different review_id,
        so the old .passed marker no longer applies.
        """
        review = ReviewBlock(strategy="individual", instructions="Check it")
        arg = StepArgument(name="report", description="Report", type="file_path")
        output_ref = StepOutputRef(argument_name="report", required=True, review=review)
        step = WorkflowStep(name="write", outputs={"report": output_ref})
        job, workflow = _make_job(tmp_path, [arg], step)

        report_path = tmp_path / "report.md"

        # First: create the file with original content and mark the review as passed
        report_path.write_text("Original content")
        task_v1 = ReviewTask(
            rule_name="step_write_output_report",
            files_to_review=[str(report_path)],
            instructions="Check it",
            agent_name=None,
        )
        review_id_v1 = compute_review_id(task_v1, tmp_path)
        instructions_dir = tmp_path / INSTRUCTIONS_DIR
        instructions_dir.mkdir(parents=True, exist_ok=True)
        (instructions_dir / f"{review_id_v1}.passed").write_bytes(b"")

        # Now: change the file content (simulating a new edit in the PR)
        report_path.write_text("Updated content with new edits")

        # The task from match_files_to_rules will have the same rule/files
        task_v2 = ReviewTask(
            rule_name="step_write_output_report",
            files_to_review=[str(report_path)],
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
                return_value=[task_v2],
            ),
            patch(
                "deepwork.jobs.mcp.quality_gate.format_for_claude",
                return_value="formatted review instructions",
            ),
        ):
            result = run_quality_gate(
                step=step,
                job=job,
                workflow=workflow,
                outputs={"report": str(report_path)},
                input_values={},
                work_summary=None,
                project_root=tmp_path,
            )

        # Review MUST run again because content changed
        assert result is not None
        assert "Quality reviews are required" in result
