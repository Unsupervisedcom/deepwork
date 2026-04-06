"""Tests for job definition parser.

Validates requirements: JOBS-REQ-002, JOBS-REQ-002.1, JOBS-REQ-002.2, JOBS-REQ-002.3,
JOBS-REQ-002.4, JOBS-REQ-002.5, JOBS-REQ-002.6, JOBS-REQ-002.7, JOBS-REQ-002.8,
JOBS-REQ-002.9, JOBS-REQ-002.10, JOBS-REQ-002.11, JOBS-REQ-002.12, JOBS-REQ-002.13,
JOBS-REQ-002.14.
"""

from pathlib import Path

import pytest

from deepwork.jobs.parser import (
    JobDefinition,
    ParseError,
    ReviewBlock,
    StepArgument,
    StepInputRef,
    StepOutputRef,
    SubWorkflowRef,
    Workflow,
    WorkflowStep,
    parse_job_definition,
)


class TestReviewBlock:
    """Tests for ReviewBlock dataclass."""

    def test_from_dict(self) -> None:
        """Test creating ReviewBlock from dictionary."""
        # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-002.4.1, JOBS-REQ-002.4.4, JOBS-REQ-002.4.5).
        data = {
            "strategy": "individual",
            "instructions": "Review each file individually.",
            "agent": {"model": "claude-sonnet"},
            "additional_context": {"include_diff": True},
        }
        review = ReviewBlock.from_dict(data)

        assert review.strategy == "individual"
        assert review.instructions == "Review each file individually."
        assert review.agent == {"model": "claude-sonnet"}
        assert review.additional_context == {"include_diff": True}

    def test_from_dict_minimal(self) -> None:
        """Test creating ReviewBlock with only required fields."""
        # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-002.4.1, JOBS-REQ-002.4.2, JOBS-REQ-002.4.3).
        data = {
            "strategy": "matches_together",
            "instructions": "Review all matches together.",
        }
        review = ReviewBlock.from_dict(data)

        assert review.strategy == "matches_together"
        assert review.instructions == "Review all matches together."
        assert review.agent is None
        assert review.additional_context is None


class TestStepArgument:
    """Tests for StepArgument dataclass."""

    def test_from_dict_basic(self) -> None:
        """Test creating StepArgument from dictionary."""
        # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-002.3.1, JOBS-REQ-002.3.2, JOBS-REQ-002.3.3).
        data = {
            "name": "market_segment",
            "description": "The market segment to analyze",
            "type": "string",
        }
        arg = StepArgument.from_dict(data)

        assert arg.name == "market_segment"
        assert arg.description == "The market segment to analyze"
        assert arg.type == "string"
        assert arg.review is None
        assert arg.json_schema is None

    def test_from_dict_file_path_type(self) -> None:
        """Test creating StepArgument with file_path type."""
        # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-002.3.2).
        data = {
            "name": "report",
            "description": "The output report",
            "type": "file_path",
        }
        arg = StepArgument.from_dict(data)

        assert arg.type == "file_path"

    def test_from_dict_with_review(self) -> None:
        """Test creating StepArgument with review block."""
        # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-002.3.4).
        data = {
            "name": "report",
            "description": "The output report",
            "type": "file_path",
            "review": {
                "strategy": "individual",
                "instructions": "Check completeness.",
            },
        }
        arg = StepArgument.from_dict(data)

        assert arg.review is not None
        assert arg.review.strategy == "individual"
        assert arg.review.instructions == "Check completeness."

    def test_from_dict_with_json_schema(self) -> None:
        """Test creating StepArgument with json_schema."""
        # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-002.3.5).
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        data = {
            "name": "config",
            "description": "Configuration object",
            "type": "string",
            "json_schema": schema,
        }
        arg = StepArgument.from_dict(data)

        assert arg.json_schema == schema


class TestStepInputRef:
    """Tests for StepInputRef dataclass."""

    def test_from_dict(self) -> None:
        """Test creating StepInputRef from name and config."""
        # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-002.6.1).
        ref = StepInputRef.from_dict("market_segment", {"required": True})

        assert ref.argument_name == "market_segment"
        assert ref.required is True

    def test_from_dict_defaults_required_true(self) -> None:
        """Test that required defaults to True."""
        # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-002.6.2).
        ref = StepInputRef.from_dict("param", {})

        assert ref.required is True

    def test_from_dict_optional(self) -> None:
        """Test creating optional StepInputRef."""
        # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-002.6.2).
        ref = StepInputRef.from_dict("optional_param", {"required": False})

        assert ref.required is False


class TestStepOutputRef:
    """Tests for StepOutputRef dataclass."""

    def test_from_dict(self) -> None:
        """Test creating StepOutputRef from name and config."""
        # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-002.6.3).
        ref = StepOutputRef.from_dict("report", {"required": True})

        assert ref.argument_name == "report"
        assert ref.required is True
        assert ref.review is None

    def test_from_dict_with_review(self) -> None:
        """Test creating StepOutputRef with inline review."""
        # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-002.6.5).
        data = {
            "required": True,
            "review": {
                "strategy": "individual",
                "instructions": "Check format.",
            },
        }
        ref = StepOutputRef.from_dict("report", data)

        assert ref.review is not None
        assert ref.review.strategy == "individual"

    def test_from_dict_defaults_required_true(self) -> None:
        """Test that required defaults to True."""
        # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-002.6.4).
        ref = StepOutputRef.from_dict("output", {})

        assert ref.required is True
        assert ref.review is None


class TestSubWorkflowRef:
    """Tests for SubWorkflowRef dataclass."""

    def test_from_dict_same_job(self) -> None:
        """Test creating SubWorkflowRef within same job."""
        # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-002.7.1).
        data = {"workflow_name": "secondary"}
        ref = SubWorkflowRef.from_dict(data)

        assert ref.workflow_name == "secondary"
        assert ref.workflow_job is None

    def test_from_dict_cross_job(self) -> None:
        """Test creating SubWorkflowRef referencing another job."""
        # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-002.7.2).
        data = {"workflow_name": "full", "workflow_job": "competitive_research"}
        ref = SubWorkflowRef.from_dict(data)

        assert ref.workflow_name == "full"
        assert ref.workflow_job == "competitive_research"


class TestWorkflowStep:
    """Tests for WorkflowStep dataclass."""

    def test_from_dict_with_instructions(self) -> None:
        """Test creating WorkflowStep with instructions."""
        # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-002.5.1, JOBS-REQ-002.5.3, JOBS-REQ-002.5.4).
        data = {
            "name": "research",
            "instructions": "Do the research.",
            "inputs": {"market_segment": {"required": True}},
            "outputs": {"report": {"required": True}},
        }
        step = WorkflowStep.from_dict(data)

        assert step.name == "research"
        assert step.instructions == "Do the research."
        assert step.sub_workflow is None
        assert "market_segment" in step.inputs
        assert step.inputs["market_segment"].argument_name == "market_segment"
        assert "report" in step.outputs
        assert step.outputs["report"].argument_name == "report"

    def test_from_dict_with_sub_workflow(self) -> None:
        """Test creating WorkflowStep with sub_workflow."""
        # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-002.5.2).
        data = {
            "name": "delegate",
            "sub_workflow": {"workflow_name": "detailed_analysis"},
        }
        step = WorkflowStep.from_dict(data)

        assert step.name == "delegate"
        assert step.instructions is None
        assert step.sub_workflow is not None
        assert step.sub_workflow.workflow_name == "detailed_analysis"

    def test_from_dict_minimal(self) -> None:
        """Test creating WorkflowStep with minimal fields."""
        # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-002.5.1, JOBS-REQ-002.5.4).
        data = {"name": "empty_step", "instructions": "Do nothing."}
        step = WorkflowStep.from_dict(data)

        assert step.name == "empty_step"
        assert step.inputs == {}
        assert step.outputs == {}
        assert step.process_requirements == {}

    def test_from_dict_with_process_requirements(self) -> None:
        """Test creating WorkflowStep with process requirements."""
        # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-002.5.5).
        data = {
            "name": "careful_step",
            "instructions": "Do carefully.",
            "process_requirements": {
                "thoroughness": "Must cover all cases",
            },
        }
        step = WorkflowStep.from_dict(data)

        assert step.process_requirements == {"thoroughness": "Must cover all cases"}


class TestWorkflow:
    """Tests for Workflow dataclass."""

    @pytest.fixture
    def sample_workflow(self) -> Workflow:
        """Create a sample workflow for testing."""
        return Workflow.from_dict(
            "main",
            {
                "summary": "Main workflow",
                "steps": [
                    {"name": "step_a", "instructions": "Do A."},
                    {"name": "step_b", "instructions": "Do B."},
                    {"name": "step_c", "instructions": "Do C."},
                ],
            },
        )

    def test_step_names(self, sample_workflow: Workflow) -> None:
        """Test step_names property returns ordered names."""
        # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-002.13.3).
        assert sample_workflow.step_names == ["step_a", "step_b", "step_c"]

    def test_get_step_found(self, sample_workflow: Workflow) -> None:
        """Test getting an existing step by name."""
        # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-002.13.1).
        step = sample_workflow.get_step("step_b")
        assert step is not None
        assert step.name == "step_b"

    def test_get_step_not_found(self, sample_workflow: Workflow) -> None:
        """Test getting a non-existent step returns None."""
        # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-002.13.1).
        assert sample_workflow.get_step("nonexistent") is None

    def test_get_step_index(self, sample_workflow: Workflow) -> None:
        """Test getting step index by name."""
        # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-002.13.2).
        assert sample_workflow.get_step_index("step_a") == 0
        assert sample_workflow.get_step_index("step_b") == 1
        assert sample_workflow.get_step_index("step_c") == 2

    def test_get_step_index_not_found(self, sample_workflow: Workflow) -> None:
        """Test getting index of non-existent step returns None."""
        # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-002.13.2).
        assert sample_workflow.get_step_index("nonexistent") is None

    def test_from_dict_with_optional_fields(self) -> None:
        """Test creating Workflow with agent and post_workflow_instructions."""
        # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-002.8.1, JOBS-REQ-002.8.5, JOBS-REQ-002.8.6, JOBS-REQ-002.8.7).
        wf = Workflow.from_dict(
            "custom",
            {
                "summary": "Custom workflow",
                "agent": "general-purpose",
                "common_job_info_provided_to_all_steps_at_runtime": "Shared context.",
                "post_workflow_instructions": "Clean up after.",
                "steps": [{"name": "only_step", "instructions": "Do it."}],
            },
        )

        assert wf.name == "custom"
        assert wf.agent == "general-purpose"
        assert wf.common_job_info == "Shared context."
        assert wf.post_workflow_instructions == "Clean up after."

    def test_from_dict_defaults(self) -> None:
        """Test that optional fields default to None."""
        # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-002.8.1, JOBS-REQ-002.8.3, JOBS-REQ-002.8.4).
        wf = Workflow.from_dict(
            "minimal",
            {
                "summary": "Minimal workflow",
                "steps": [{"name": "s", "instructions": "Do."}],
            },
        )

        assert wf.agent is None
        assert wf.common_job_info is None
        assert wf.post_workflow_instructions is None


class TestJobDefinition:
    """Tests for JobDefinition dataclass."""

    def _make_job(
        self,
        step_arguments: list[StepArgument] | None = None,
        workflows: dict[str, Workflow] | None = None,
    ) -> JobDefinition:
        """Helper to build a JobDefinition for validation tests."""
        if step_arguments is None:
            step_arguments = [
                StepArgument(name="input", description="Input", type="string"),
                StepArgument(name="output", description="Output", type="file_path"),
            ]
        if workflows is None:
            workflows = {
                "main": Workflow(
                    name="main",
                    summary="Main",
                    steps=[
                        WorkflowStep(
                            name="s1",
                            instructions="Do.",
                            inputs={"input": StepInputRef(argument_name="input")},
                            outputs={"output": StepOutputRef(argument_name="output")},
                        ),
                    ],
                ),
            }
        return JobDefinition(
            name="test_job",
            summary="Test",
            step_arguments=step_arguments,
            workflows=workflows,
            job_dir=Path("/tmp"),
        )

    def test_get_argument_found(self) -> None:
        """Test getting an existing argument."""
        # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-002.12.1).
        job = self._make_job()
        arg = job.get_argument("input")
        assert arg is not None
        assert arg.name == "input"

    def test_get_argument_not_found(self) -> None:
        """Test getting a non-existent argument returns None."""
        # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-002.12.1).
        job = self._make_job()
        assert job.get_argument("nonexistent") is None

    def test_get_workflow_found(self) -> None:
        """Test getting an existing workflow."""
        # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-002.12.2).
        job = self._make_job()
        wf = job.get_workflow("main")
        assert wf is not None
        assert wf.name == "main"

    def test_get_workflow_not_found(self) -> None:
        """Test getting a non-existent workflow returns None."""
        # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-002.12.2).
        job = self._make_job()
        assert job.get_workflow("nonexistent") is None

    def test_validate_argument_refs_valid(self) -> None:
        """Test validation passes when all refs point to valid arguments."""
        # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-002.9.1).
        job = self._make_job()
        # Should not raise
        job.validate_argument_refs()

    def test_validate_argument_refs_invalid_input(self) -> None:
        """Test validation fails when input ref points to non-existent argument."""
        # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-002.9.1).
        job = self._make_job(
            workflows={
                "main": Workflow(
                    name="main",
                    summary="Main",
                    steps=[
                        WorkflowStep(
                            name="s1",
                            instructions="Do.",
                            inputs={"bogus": StepInputRef(argument_name="bogus")},
                        ),
                    ],
                ),
            },
        )

        with pytest.raises(ParseError, match="non-existent step_argument 'bogus' in inputs"):
            job.validate_argument_refs()

    def test_validate_argument_refs_invalid_output(self) -> None:
        """Test validation fails when output ref points to non-existent argument."""
        # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-002.9.1).
        job = self._make_job(
            workflows={
                "main": Workflow(
                    name="main",
                    summary="Main",
                    steps=[
                        WorkflowStep(
                            name="s1",
                            instructions="Do.",
                            outputs={"bogus": StepOutputRef(argument_name="bogus")},
                        ),
                    ],
                ),
            },
        )

        with pytest.raises(ParseError, match="non-existent step_argument 'bogus' in outputs"):
            job.validate_argument_refs()

    def test_validate_sub_workflows_valid(self) -> None:
        """Test validation passes for valid same-job sub_workflow ref."""
        # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-002.10.1).
        job = self._make_job(
            workflows={
                "main": Workflow(
                    name="main",
                    summary="Main",
                    steps=[
                        WorkflowStep(
                            name="delegate",
                            sub_workflow=SubWorkflowRef(workflow_name="helper"),
                        ),
                    ],
                ),
                "helper": Workflow(
                    name="helper",
                    summary="Helper",
                    steps=[
                        WorkflowStep(name="h1", instructions="Help."),
                    ],
                ),
            },
        )

        # Should not raise
        job.validate_sub_workflows()

    def test_validate_sub_workflows_invalid(self) -> None:
        """Test validation fails when sub_workflow points to non-existent workflow."""
        # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-002.10.1).
        job = self._make_job(
            workflows={
                "main": Workflow(
                    name="main",
                    summary="Main",
                    steps=[
                        WorkflowStep(
                            name="delegate",
                            sub_workflow=SubWorkflowRef(workflow_name="missing"),
                        ),
                    ],
                ),
            },
        )

        with pytest.raises(ParseError, match="non-existent workflow 'missing'"):
            job.validate_sub_workflows()

    def test_validate_sub_workflows_cross_job_skipped(self) -> None:
        """Test that cross-job sub_workflow refs are not validated."""
        # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-002.10.2).
        job = self._make_job(
            workflows={
                "main": Workflow(
                    name="main",
                    summary="Main",
                    steps=[
                        WorkflowStep(
                            name="delegate",
                            sub_workflow=SubWorkflowRef(
                                workflow_name="external_wf",
                                workflow_job="other_job",
                            ),
                        ),
                    ],
                ),
            },
        )

        # Should not raise even though external_wf doesn't exist locally
        job.validate_sub_workflows()

    def test_validate_step_exclusivity_valid(self) -> None:
        """Test validation passes when steps have exactly one of instructions/sub_workflow."""
        # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-002.5.2).
        job = self._make_job()
        # Default _make_job uses instructions
        job.validate_step_exclusivity()

    def test_validate_step_exclusivity_both(self) -> None:
        """Test validation fails when step has both instructions and sub_workflow."""
        # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-002.5.2).
        job = self._make_job(
            workflows={
                "main": Workflow(
                    name="main",
                    summary="Main",
                    steps=[
                        WorkflowStep(
                            name="bad_step",
                            instructions="Do.",
                            sub_workflow=SubWorkflowRef(workflow_name="other"),
                        ),
                    ],
                ),
            },
        )

        with pytest.raises(ParseError, match="has both"):
            job.validate_step_exclusivity()

    def test_validate_step_exclusivity_neither(self) -> None:
        """Test validation fails when step has neither instructions nor sub_workflow."""
        # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-002.5.2).
        job = self._make_job(
            workflows={
                "main": Workflow(
                    name="main",
                    summary="Main",
                    steps=[
                        WorkflowStep(name="empty_step"),
                    ],
                ),
            },
        )

        with pytest.raises(ParseError, match="has neither"):
            job.validate_step_exclusivity()

    def test_validate_unique_step_names_valid(self) -> None:
        """Test validation passes when step names are unique."""
        # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-002.11.1).
        job = self._make_job()
        job.validate_unique_step_names()

    def test_validate_unique_step_names_duplicate(self) -> None:
        """Test validation fails for duplicate step names within a workflow."""
        # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-002.11.1).
        job = self._make_job(
            workflows={
                "main": Workflow(
                    name="main",
                    summary="Main",
                    steps=[
                        WorkflowStep(name="dup", instructions="First."),
                        WorkflowStep(name="dup", instructions="Second."),
                    ],
                ),
            },
        )

        with pytest.raises(ParseError, match="duplicate step name 'dup'"):
            job.validate_unique_step_names()


class TestParseJobDefinition:
    """Tests for parse_job_definition function."""

    def test_parses_simple_job(self, fixtures_dir: Path) -> None:
        """Test parsing simple job definition."""
        # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-002.1.1, JOBS-REQ-002.2.3, JOBS-REQ-002.2.5, JOBS-REQ-002.2.6).
        job_dir = fixtures_dir / "jobs" / "simple_job"
        job = parse_job_definition(job_dir)

        assert job.name == "simple_job"
        assert job.summary == "A simple single-step job for testing"
        assert len(job.step_arguments) == 2
        assert job.step_arguments[0].name == "input_param"
        assert job.step_arguments[0].type == "string"
        assert job.step_arguments[1].name == "output"
        assert job.step_arguments[1].type == "file_path"
        assert "main" in job.workflows
        assert job.job_dir == job_dir

    def test_simple_job_workflow(self, fixtures_dir: Path) -> None:
        """Test simple job's workflow structure."""
        # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-002.8.2, JOBS-REQ-002.8.4).
        job_dir = fixtures_dir / "jobs" / "simple_job"
        job = parse_job_definition(job_dir)

        wf = job.get_workflow("main")
        assert wf is not None
        assert wf.summary == "Run the single step"
        assert wf.step_names == ["single_step"]

        step = wf.get_step("single_step")
        assert step is not None
        assert "input_param" in step.inputs
        assert "output" in step.outputs

    def test_parses_complex_job(self, fixtures_dir: Path) -> None:
        """Test parsing complex job with multiple steps."""
        # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-002.1.1, JOBS-REQ-002.8.4).
        job_dir = fixtures_dir / "jobs" / "complex_job"
        job = parse_job_definition(job_dir)

        assert job.name == "competitive_research"
        assert len(job.step_arguments) == 8

        wf = job.get_workflow("full")
        assert wf is not None
        assert len(wf.steps) == 4
        assert wf.step_names == [
            "identify_competitors",
            "primary_research",
            "secondary_research",
            "comparative_report",
        ]

    def test_complex_job_inputs_outputs(self, fixtures_dir: Path) -> None:
        """Test complex job step inputs and outputs."""
        # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-002.5.4).
        job_dir = fixtures_dir / "jobs" / "complex_job"
        job = parse_job_definition(job_dir)

        wf = job.get_workflow("full")
        assert wf is not None

        # identify_competitors: 2 inputs, 1 output
        step0 = wf.steps[0]
        assert "market_segment" in step0.inputs
        assert "product_category" in step0.inputs
        assert "competitors" in step0.outputs

        # primary_research: 1 input, 2 outputs
        step1 = wf.steps[1]
        assert "competitors" in step1.inputs
        assert "primary_research" in step1.outputs
        assert "competitor_profiles" in step1.outputs

        # secondary_research: 2 inputs, 1 output
        step2 = wf.steps[2]
        assert "competitors" in step2.inputs
        assert "primary_research" in step2.inputs
        assert "secondary_research" in step2.outputs

        # comparative_report: 2 inputs, 2 outputs
        step3 = wf.steps[3]
        assert "primary_research" in step3.inputs
        assert "secondary_research" in step3.inputs
        assert "comparison_matrix" in step3.outputs
        assert "strengths_weaknesses" in step3.outputs

    def test_raises_for_missing_directory(self, temp_dir: Path) -> None:
        """Test parsing fails for missing directory."""
        # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-002.1.2).
        nonexistent = temp_dir / "nonexistent"

        with pytest.raises(ParseError, match="does not exist"):
            parse_job_definition(nonexistent)

    def test_raises_for_file_instead_of_directory(self, temp_dir: Path) -> None:
        """Test parsing fails for file path."""
        # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-002.1.3).
        file_path = temp_dir / "file.txt"
        file_path.write_text("content")

        with pytest.raises(ParseError, match="not a directory"):
            parse_job_definition(file_path)

    def test_raises_for_missing_job_yml(self, temp_dir: Path) -> None:
        """Test parsing fails for directory without job.yml."""
        # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-002.1.4).
        job_dir = temp_dir / "job"
        job_dir.mkdir()

        with pytest.raises(ParseError, match="job.yml not found"):
            parse_job_definition(job_dir)

    def test_raises_for_empty_job_yml(self, temp_dir: Path) -> None:
        """Test parsing fails for empty job.yml."""
        # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-002.1.5).
        job_dir = temp_dir / "job"
        job_dir.mkdir()
        (job_dir / "job.yml").write_text("")

        with pytest.raises(ParseError, match="empty"):
            parse_job_definition(job_dir)

    def test_raises_for_invalid_yaml(self, temp_dir: Path) -> None:
        """Test parsing fails for invalid YAML."""
        # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-002.1.6).
        job_dir = temp_dir / "job"
        job_dir.mkdir()
        (job_dir / "job.yml").write_text("invalid: [yaml: content")

        with pytest.raises(ParseError, match="Failed to load"):
            parse_job_definition(job_dir)

    def test_raises_for_invalid_schema(self, fixtures_dir: Path) -> None:
        """Test parsing fails for schema validation errors."""
        # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-002.2.1, JOBS-REQ-002.2.2).
        job_dir = fixtures_dir / "jobs" / "invalid_job"

        with pytest.raises(ParseError, match="validation failed"):
            parse_job_definition(job_dir)


class TestRealJobDefinitions:
    """Validate all shipped job.yml files parse against the schema."""

    _REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

    @pytest.mark.parametrize(
        "job_dir",
        sorted(
            [
                *(_REPO_ROOT / "src" / "deepwork" / "standard_jobs").glob("*/"),
                *(_REPO_ROOT / "library" / "jobs").glob("*/"),
            ]
        ),
        ids=lambda p: p.name,
    )
    def test_job_parses_successfully(self, job_dir: Path) -> None:
        """Every standard and library job.yml must parse and validate."""
        # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-002.14.1, JOBS-REQ-002.14.2).
        if not (job_dir / "job.yml").exists():
            pytest.skip(f"No job.yml in {job_dir.name}")
        job = parse_job_definition(job_dir)
        assert job.name == job_dir.name
