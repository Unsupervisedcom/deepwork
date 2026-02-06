"""Tests for job definition parser."""

from pathlib import Path

import pytest

from deepwork.core.parser import (
    JobDefinition,
    OutputSpec,
    ParseError,
    Review,
    Step,
    StepInput,
    parse_job_definition,
)


class TestStepInput:
    """Tests for StepInput dataclass."""

    def test_user_input(self) -> None:
        """Test user parameter input."""
        inp = StepInput(name="param1", description="First parameter")

        assert inp.is_user_input()
        assert not inp.is_file_input()

    def test_file_input(self) -> None:
        """Test file input from previous step."""
        inp = StepInput(file="data.md", from_step="step1")

        assert inp.is_file_input()
        assert not inp.is_user_input()

    def test_from_dict_user_input(self) -> None:
        """Test creating user input from dictionary."""
        data = {"name": "param1", "description": "First parameter"}
        inp = StepInput.from_dict(data)

        assert inp.name == "param1"
        assert inp.description == "First parameter"
        assert inp.is_user_input()

    def test_from_dict_file_input(self) -> None:
        """Test creating file input from dictionary."""
        data = {"file": "data.md", "from_step": "step1"}
        inp = StepInput.from_dict(data)

        assert inp.file == "data.md"
        assert inp.from_step == "step1"
        assert inp.is_file_input()


class TestOutputSpec:
    """Tests for OutputSpec dataclass."""

    def test_file_output(self) -> None:
        """Test single file output."""
        output = OutputSpec(name="output.md", type="file", description="An output file")

        assert output.name == "output.md"
        assert output.type == "file"
        assert output.description == "An output file"

    def test_files_output(self) -> None:
        """Test multiple files output."""
        output = OutputSpec(
            name="step_instruction_files", type="files", description="Instruction files"
        )

        assert output.name == "step_instruction_files"
        assert output.type == "files"
        assert output.description == "Instruction files"

    def test_from_dict(self) -> None:
        """Test creating output from name and dict."""
        data = {"type": "file", "description": "An output file"}
        output = OutputSpec.from_dict("output.md", data)

        assert output.name == "output.md"
        assert output.type == "file"
        assert output.description == "An output file"

    def test_from_dict_files_type(self) -> None:
        """Test creating files-type output from dict."""
        data = {"type": "files", "description": "Multiple output files"}
        output = OutputSpec.from_dict("reports", data)

        assert output.name == "reports"
        assert output.type == "files"
        assert output.description == "Multiple output files"


class TestReview:
    """Tests for Review dataclass."""

    def test_from_dict(self) -> None:
        """Test creating review from dictionary."""
        data = {
            "run_each": "step",
            "quality_criteria": {"Complete": "Is it complete?", "Valid": "Is it valid?"},
        }
        review = Review.from_dict(data)

        assert review.run_each == "step"
        assert review.quality_criteria == {"Complete": "Is it complete?", "Valid": "Is it valid?"}

    def test_from_dict_output_specific(self) -> None:
        """Test creating review targeting specific output."""
        data = {
            "run_each": "reports",
            "quality_criteria": {"Well Written": "Is it well written?"},
        }
        review = Review.from_dict(data)

        assert review.run_each == "reports"
        assert len(review.quality_criteria) == 1

    def test_from_dict_empty_criteria(self) -> None:
        """Test creating review with empty criteria defaults."""
        data = {"run_each": "step"}
        review = Review.from_dict(data)

        assert review.quality_criteria == {}


class TestStep:
    """Tests for Step dataclass."""

    def test_from_dict_minimal(self) -> None:
        """Test creating step from minimal dictionary."""
        data = {
            "id": "step1",
            "name": "Step 1",
            "description": "First step",
            "instructions_file": "steps/step1.md",
            "outputs": {
                "output.md": {"type": "file", "description": "An output file"},
            },
        }
        step = Step.from_dict(data)

        assert step.id == "step1"
        assert step.name == "Step 1"
        assert step.description == "First step"
        assert step.instructions_file == "steps/step1.md"
        assert len(step.outputs) == 1
        assert step.outputs[0].name == "output.md"
        assert step.outputs[0].type == "file"
        assert step.inputs == []
        assert step.dependencies == []

    def test_from_dict_with_multiple_outputs(self) -> None:
        """Test creating step with file and files type outputs."""
        data = {
            "id": "step1",
            "name": "Step 1",
            "description": "First step",
            "instructions_file": "steps/step1.md",
            "outputs": {
                "report.md": {"type": "file", "description": "A report"},
                "attachments": {"type": "files", "description": "Supporting files"},
            },
        }
        step = Step.from_dict(data)

        assert len(step.outputs) == 2
        output_names = {out.name for out in step.outputs}
        assert "report.md" in output_names
        assert "attachments" in output_names

        report = next(out for out in step.outputs if out.name == "report.md")
        assert report.type == "file"
        attachments = next(out for out in step.outputs if out.name == "attachments")
        assert attachments.type == "files"

    def test_from_dict_with_inputs(self) -> None:
        """Test creating step with inputs."""
        data = {
            "id": "step1",
            "name": "Step 1",
            "description": "First step",
            "instructions_file": "steps/step1.md",
            "inputs": [
                {"name": "param1", "description": "Parameter 1"},
                {"file": "data.md", "from_step": "step0"},
            ],
            "outputs": {
                "output.md": {"type": "file", "description": "An output file"},
            },
            "dependencies": ["step0"],
        }
        step = Step.from_dict(data)

        assert len(step.inputs) == 2
        assert step.inputs[0].is_user_input()
        assert step.inputs[1].is_file_input()
        assert step.dependencies == ["step0"]

    def test_from_dict_exposed_default_false(self) -> None:
        """Test that exposed defaults to False."""
        data = {
            "id": "step1",
            "name": "Step 1",
            "description": "First step",
            "instructions_file": "steps/step1.md",
            "outputs": {
                "output.md": {"type": "file", "description": "An output file"},
            },
        }
        step = Step.from_dict(data)

        assert step.exposed is False

    def test_from_dict_exposed_true(self) -> None:
        """Test creating step with exposed=True."""
        data = {
            "id": "step1",
            "name": "Step 1",
            "description": "First step",
            "instructions_file": "steps/step1.md",
            "outputs": {
                "output.md": {"type": "file", "description": "An output file"},
            },
            "exposed": True,
        }
        step = Step.from_dict(data)

        assert step.exposed is True

    def test_from_dict_with_reviews(self) -> None:
        """Test creating step with reviews."""
        data = {
            "id": "step1",
            "name": "Step 1",
            "description": "First step",
            "instructions_file": "steps/step1.md",
            "outputs": {
                "output.md": {"type": "file", "description": "An output file"},
            },
            "reviews": [
                {
                    "run_each": "step",
                    "quality_criteria": {"Complete": "Is it complete?"},
                },
                {
                    "run_each": "output.md",
                    "quality_criteria": {"Valid": "Is it valid?"},
                },
            ],
        }
        step = Step.from_dict(data)

        assert len(step.reviews) == 2
        assert step.reviews[0].run_each == "step"
        assert step.reviews[0].quality_criteria == {"Complete": "Is it complete?"}
        assert step.reviews[1].run_each == "output.md"

    def test_from_dict_empty_reviews(self) -> None:
        """Test creating step with empty reviews list."""
        data = {
            "id": "step1",
            "name": "Step 1",
            "description": "First step",
            "instructions_file": "steps/step1.md",
            "outputs": {
                "output.md": {"type": "file", "description": "An output file"},
            },
            "reviews": [],
        }
        step = Step.from_dict(data)

        assert step.reviews == []


class TestJobDefinition:
    """Tests for JobDefinition dataclass."""

    def test_get_step(self, fixtures_dir: Path) -> None:
        """Test getting step by ID."""
        job_dir = fixtures_dir / "jobs" / "simple_job"
        job = parse_job_definition(job_dir)

        step = job.get_step("single_step")
        assert step is not None
        assert step.id == "single_step"

        assert job.get_step("nonexistent") is None

    def test_validate_dependencies_valid(self, fixtures_dir: Path) -> None:
        """Test validation passes for valid dependencies."""
        job_dir = fixtures_dir / "jobs" / "complex_job"
        job = parse_job_definition(job_dir)

        # Should not raise
        job.validate_dependencies()

    def test_validate_dependencies_missing_step(self) -> None:
        """Test validation fails for missing dependency."""
        job = JobDefinition(
            name="test_job",
            version="1.0.0",
            summary="Test job",
            description="Test",
            steps=[
                Step(
                    id="step1",
                    name="Step 1",
                    description="Step",
                    instructions_file="steps/step1.md",
                    outputs=[
                        OutputSpec(
                            name="output.md", type="file", description="Output file"
                        )
                    ],
                    dependencies=["nonexistent"],
                )
            ],
            job_dir=Path("/tmp"),
        )

        with pytest.raises(ParseError, match="depends on non-existent step"):
            job.validate_dependencies()

    def test_validate_dependencies_circular(self) -> None:
        """Test validation fails for circular dependencies."""
        job = JobDefinition(
            name="test_job",
            version="1.0.0",
            summary="Test job",
            description="Test",
            steps=[
                Step(
                    id="step1",
                    name="Step 1",
                    description="Step",
                    instructions_file="steps/step1.md",
                    outputs=[
                        OutputSpec(
                            name="output.md", type="file", description="Output file"
                        )
                    ],
                    dependencies=["step2"],
                ),
                Step(
                    id="step2",
                    name="Step 2",
                    description="Step",
                    instructions_file="steps/step2.md",
                    outputs=[
                        OutputSpec(
                            name="output.md", type="file", description="Output file"
                        )
                    ],
                    dependencies=["step1"],
                ),
            ],
            job_dir=Path("/tmp"),
        )

        with pytest.raises(ParseError, match="Circular dependency detected"):
            job.validate_dependencies()

    def test_validate_file_inputs_valid(self, fixtures_dir: Path) -> None:
        """Test file input validation passes for valid inputs."""
        job_dir = fixtures_dir / "jobs" / "complex_job"
        job = parse_job_definition(job_dir)

        # Should not raise
        job.validate_file_inputs()

    def test_validate_file_inputs_missing_step(self) -> None:
        """Test file input validation fails for missing from_step."""
        job = JobDefinition(
            name="test_job",
            version="1.0.0",
            summary="Test job",
            description="Test",
            steps=[
                Step(
                    id="step1",
                    name="Step 1",
                    description="Step",
                    instructions_file="steps/step1.md",
                    inputs=[StepInput(file="data.md", from_step="nonexistent")],
                    outputs=[
                        OutputSpec(
                            name="output.md", type="file", description="Output file"
                        )
                    ],
                    dependencies=["nonexistent"],
                )
            ],
            job_dir=Path("/tmp"),
        )

        with pytest.raises(ParseError, match="references non-existent step"):
            job.validate_file_inputs()

    def test_validate_reviews_valid(self) -> None:
        """Test that validate_reviews passes for valid run_each values."""
        job = JobDefinition(
            name="test_job",
            version="1.0.0",
            summary="Test job",
            description="Test",
            steps=[
                Step(
                    id="step1",
                    name="Step 1",
                    description="Step",
                    instructions_file="steps/step1.md",
                    outputs=[
                        OutputSpec(name="report.md", type="file", description="Report")
                    ],
                    reviews=[
                        Review(run_each="step", quality_criteria={"Complete": "Is it?"}),
                        Review(run_each="report.md", quality_criteria={"Valid": "Is it?"}),
                    ],
                )
            ],
            job_dir=Path("/tmp"),
        )

        # Should not raise
        job.validate_reviews()

    def test_validate_reviews_invalid_run_each(self) -> None:
        """Test that validate_reviews fails for invalid run_each."""
        job = JobDefinition(
            name="test_job",
            version="1.0.0",
            summary="Test job",
            description="Test",
            steps=[
                Step(
                    id="step1",
                    name="Step 1",
                    description="Step",
                    instructions_file="steps/step1.md",
                    outputs=[
                        OutputSpec(name="report.md", type="file", description="Report")
                    ],
                    reviews=[
                        Review(
                            run_each="nonexistent_output",
                            quality_criteria={"Test": "Is it?"},
                        ),
                    ],
                )
            ],
            job_dir=Path("/tmp"),
        )

        with pytest.raises(ParseError, match="run_each='nonexistent_output'"):
            job.validate_reviews()

    def test_validate_file_inputs_not_in_dependencies(self) -> None:
        """Test file input validation fails if from_step not in dependencies."""
        job = JobDefinition(
            name="test_job",
            version="1.0.0",
            summary="Test job",
            description="Test",
            steps=[
                Step(
                    id="step1",
                    name="Step 1",
                    description="Step",
                    instructions_file="steps/step1.md",
                    outputs=[
                        OutputSpec(
                            name="output.md", type="file", description="Output file"
                        )
                    ],
                ),
                Step(
                    id="step2",
                    name="Step 2",
                    description="Step",
                    instructions_file="steps/step2.md",
                    inputs=[StepInput(file="data.md", from_step="step1")],
                    outputs=[
                        OutputSpec(
                            name="output.md", type="file", description="Output file"
                        )
                    ],
                    # Missing step1 in dependencies!
                    dependencies=[],
                ),
            ],
            job_dir=Path("/tmp"),
        )

        with pytest.raises(ParseError, match="not in dependencies"):
            job.validate_file_inputs()


class TestParseJobDefinition:
    """Tests for parse_job_definition function."""

    def test_parses_simple_job(self, fixtures_dir: Path) -> None:
        """Test parsing simple job definition."""
        job_dir = fixtures_dir / "jobs" / "simple_job"
        job = parse_job_definition(job_dir)

        assert job.name == "simple_job"
        assert job.summary == "A simple single-step job for testing"
        assert "DeepWork framework" in job.description  # Multi-line description
        assert len(job.steps) == 1
        assert job.steps[0].id == "single_step"
        assert job.job_dir == job_dir

    def test_parses_complex_job(self, fixtures_dir: Path) -> None:
        """Test parsing complex job with dependencies."""
        job_dir = fixtures_dir / "jobs" / "complex_job"
        job = parse_job_definition(job_dir)

        assert job.name == "competitive_research"
        assert len(job.steps) == 4
        assert job.steps[0].id == "identify_competitors"
        assert job.steps[1].id == "primary_research"
        assert job.steps[2].id == "secondary_research"
        assert job.steps[3].id == "comparative_report"

        # Check dependencies
        assert job.steps[0].dependencies == []
        assert job.steps[1].dependencies == ["identify_competitors"]
        assert "identify_competitors" in job.steps[2].dependencies
        assert "primary_research" in job.steps[2].dependencies
        assert "primary_research" in job.steps[3].dependencies
        assert "secondary_research" in job.steps[3].dependencies

    def test_parses_user_inputs(self, fixtures_dir: Path) -> None:
        """Test parsing step with user inputs."""
        job_dir = fixtures_dir / "jobs" / "simple_job"
        job = parse_job_definition(job_dir)

        step = job.steps[0]
        assert len(step.inputs) == 1
        assert step.inputs[0].is_user_input()
        assert step.inputs[0].name == "input_param"

    def test_parses_file_inputs(self, fixtures_dir: Path) -> None:
        """Test parsing step with file inputs."""
        job_dir = fixtures_dir / "jobs" / "complex_job"
        job = parse_job_definition(job_dir)

        step = job.steps[1]  # primary_research
        assert len(step.inputs) == 1
        assert step.inputs[0].is_file_input()
        assert step.inputs[0].file == "competitors.md"
        assert step.inputs[0].from_step == "identify_competitors"

    def test_parses_exposed_steps(self, fixtures_dir: Path) -> None:
        """Test parsing job with exposed and hidden steps."""
        job_dir = fixtures_dir / "jobs" / "exposed_step_job"
        job = parse_job_definition(job_dir)

        assert len(job.steps) == 2
        # First step is hidden by default
        assert job.steps[0].id == "hidden_step"
        assert job.steps[0].exposed is False
        # Second step is explicitly exposed
        assert job.steps[1].id == "exposed_step"
        assert job.steps[1].exposed is True

    def test_raises_for_missing_directory(self, temp_dir: Path) -> None:
        """Test parsing fails for missing directory."""
        nonexistent = temp_dir / "nonexistent"

        with pytest.raises(ParseError, match="does not exist"):
            parse_job_definition(nonexistent)

    def test_raises_for_file_instead_of_directory(self, temp_dir: Path) -> None:
        """Test parsing fails for file path."""
        file_path = temp_dir / "file.txt"
        file_path.write_text("content")

        with pytest.raises(ParseError, match="not a directory"):
            parse_job_definition(file_path)

    def test_raises_for_missing_job_yml(self, temp_dir: Path) -> None:
        """Test parsing fails for directory without job.yml."""
        job_dir = temp_dir / "job"
        job_dir.mkdir()

        with pytest.raises(ParseError, match="job.yml not found"):
            parse_job_definition(job_dir)

    def test_raises_for_empty_job_yml(self, temp_dir: Path) -> None:
        """Test parsing fails for empty job.yml."""
        job_dir = temp_dir / "job"
        job_dir.mkdir()
        (job_dir / "job.yml").write_text("")

        with pytest.raises(ParseError, match="validation failed"):
            parse_job_definition(job_dir)

    def test_raises_for_invalid_yaml(self, temp_dir: Path) -> None:
        """Test parsing fails for invalid YAML."""
        job_dir = temp_dir / "job"
        job_dir.mkdir()
        (job_dir / "job.yml").write_text("invalid: [yaml: content")

        with pytest.raises(ParseError, match="Failed to load"):
            parse_job_definition(job_dir)

    def test_raises_for_invalid_schema(self, fixtures_dir: Path) -> None:
        """Test parsing fails for schema validation errors."""
        job_dir = fixtures_dir / "jobs" / "invalid_job"

        with pytest.raises(ParseError, match="validation failed"):
            parse_job_definition(job_dir)


class TestConcurrentSteps:
    """Tests for concurrent step parsing in workflows."""

    def test_parses_concurrent_steps_workflow(self, fixtures_dir: Path) -> None:
        """Test parsing job with concurrent steps in workflow."""
        job_dir = fixtures_dir / "jobs" / "concurrent_steps_job"
        job = parse_job_definition(job_dir)

        assert job.name == "concurrent_workflow"
        assert len(job.workflows) == 1
        assert job.workflows[0].name == "full_analysis"

    def test_workflow_step_entries(self, fixtures_dir: Path) -> None:
        """Test workflow step_entries structure with concurrent steps."""
        job_dir = fixtures_dir / "jobs" / "concurrent_steps_job"
        job = parse_job_definition(job_dir)

        workflow = job.workflows[0]
        assert len(workflow.step_entries) == 4

        # First entry: sequential step
        assert not workflow.step_entries[0].is_concurrent
        assert workflow.step_entries[0].step_ids == ["setup"]

        # Second entry: concurrent steps
        assert workflow.step_entries[1].is_concurrent
        assert workflow.step_entries[1].step_ids == [
            "research_web",
            "research_docs",
            "research_interviews",
        ]

        # Third entry: sequential step
        assert not workflow.step_entries[2].is_concurrent
        assert workflow.step_entries[2].step_ids == ["compile_results"]

        # Fourth entry: sequential step
        assert not workflow.step_entries[3].is_concurrent
        assert workflow.step_entries[3].step_ids == ["final_review"]

    def test_workflow_flattened_steps(self, fixtures_dir: Path) -> None:
        """Test backward-compatible flattened steps list."""
        job_dir = fixtures_dir / "jobs" / "concurrent_steps_job"
        job = parse_job_definition(job_dir)

        workflow = job.workflows[0]
        # Flattened list should include all step IDs
        assert workflow.steps == [
            "setup",
            "research_web",
            "research_docs",
            "research_interviews",
            "compile_results",
            "final_review",
        ]

    def test_get_step_entry_for_step(self, fixtures_dir: Path) -> None:
        """Test getting the step entry containing a step."""
        job_dir = fixtures_dir / "jobs" / "concurrent_steps_job"
        job = parse_job_definition(job_dir)

        workflow = job.workflows[0]

        # Sequential step
        entry = workflow.get_step_entry_for_step("setup")
        assert entry is not None
        assert not entry.is_concurrent
        assert entry.step_ids == ["setup"]

        # Concurrent step
        entry = workflow.get_step_entry_for_step("research_web")
        assert entry is not None
        assert entry.is_concurrent
        assert "research_web" in entry.step_ids

    def test_get_step_entry_position_in_workflow(self, fixtures_dir: Path) -> None:
        """Test getting entry-based position in workflow."""
        job_dir = fixtures_dir / "jobs" / "concurrent_steps_job"
        job = parse_job_definition(job_dir)

        # Sequential step
        result = job.get_step_entry_position_in_workflow("setup")
        assert result is not None
        entry_pos, total_entries, entry = result
        assert entry_pos == 1
        assert total_entries == 4
        assert not entry.is_concurrent

        # Concurrent step - all share same entry position
        for step_id in ["research_web", "research_docs", "research_interviews"]:
            result = job.get_step_entry_position_in_workflow(step_id)
            assert result is not None
            entry_pos, total_entries, entry = result
            assert entry_pos == 2  # All in second position
            assert total_entries == 4
            assert entry.is_concurrent

    def test_get_concurrent_step_info(self, fixtures_dir: Path) -> None:
        """Test getting info about position within concurrent group."""
        job_dir = fixtures_dir / "jobs" / "concurrent_steps_job"
        job = parse_job_definition(job_dir)

        # Sequential step returns None
        assert job.get_concurrent_step_info("setup") is None

        # Concurrent steps return their position in group
        result = job.get_concurrent_step_info("research_web")
        assert result == (1, 3)

        result = job.get_concurrent_step_info("research_docs")
        assert result == (2, 3)

        result = job.get_concurrent_step_info("research_interviews")
        assert result == (3, 3)
