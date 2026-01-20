"""Tests for job definition parser."""

from pathlib import Path

import pytest

from deepwork.core.parser import (
    JobDefinition,
    OutputSpec,
    ParseError,
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

    def test_simple_output(self) -> None:
        """Test simple output without document type."""
        output = OutputSpec(file="output.md")

        assert output.file == "output.md"
        assert output.document_type is None
        assert not output.has_document_type()

    def test_output_with_document_type(self) -> None:
        """Test output with document type reference."""
        output = OutputSpec(file="report.md", document_type=".deepwork/doc_specs/monthly_report.md")

        assert output.file == "report.md"
        assert output.document_type == ".deepwork/doc_specs/monthly_report.md"
        assert output.has_document_type()

    def test_from_dict_string(self) -> None:
        """Test creating output from string."""
        output = OutputSpec.from_dict("output.md")

        assert output.file == "output.md"
        assert output.document_type is None
        assert not output.has_document_type()

    def test_from_dict_simple_object(self) -> None:
        """Test creating output from dict without document type."""
        data = {"file": "output.md"}
        output = OutputSpec.from_dict(data)

        assert output.file == "output.md"
        assert output.document_type is None
        assert not output.has_document_type()

    def test_from_dict_with_document_type(self) -> None:
        """Test creating output from dict with document type."""
        data = {"file": "report.md", "document_type": ".deepwork/doc_specs/monthly_report.md"}
        output = OutputSpec.from_dict(data)

        assert output.file == "report.md"
        assert output.document_type == ".deepwork/doc_specs/monthly_report.md"
        assert output.has_document_type()


class TestStep:
    """Tests for Step dataclass."""

    def test_from_dict_minimal(self) -> None:
        """Test creating step from minimal dictionary."""
        data = {
            "id": "step1",
            "name": "Step 1",
            "description": "First step",
            "instructions_file": "steps/step1.md",
            "outputs": ["output.md"],
        }
        step = Step.from_dict(data)

        assert step.id == "step1"
        assert step.name == "Step 1"
        assert step.description == "First step"
        assert step.instructions_file == "steps/step1.md"
        assert len(step.outputs) == 1
        assert step.outputs[0].file == "output.md"
        assert not step.outputs[0].has_document_type()
        assert step.inputs == []
        assert step.dependencies == []

    def test_from_dict_with_document_type_output(self) -> None:
        """Test creating step with document type-referenced output."""
        data = {
            "id": "step1",
            "name": "Step 1",
            "description": "First step",
            "instructions_file": "steps/step1.md",
            "outputs": [
                "simple_output.md",
                {"file": "report.md", "document_type": ".deepwork/doc_specs/monthly_report.md"},
            ],
        }
        step = Step.from_dict(data)

        assert len(step.outputs) == 2
        assert step.outputs[0].file == "simple_output.md"
        assert not step.outputs[0].has_document_type()
        assert step.outputs[1].file == "report.md"
        assert step.outputs[1].document_type == ".deepwork/doc_specs/monthly_report.md"
        assert step.outputs[1].has_document_type()

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
            "outputs": ["output.md"],
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
            "outputs": ["output.md"],
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
            "outputs": ["output.md"],
            "exposed": True,
        }
        step = Step.from_dict(data)

        assert step.exposed is True


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
                    outputs=["output.md"],
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
                    outputs=["output.md"],
                    dependencies=["step2"],
                ),
                Step(
                    id="step2",
                    name="Step 2",
                    description="Step",
                    instructions_file="steps/step2.md",
                    outputs=["output.md"],
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
                    outputs=["output.md"],
                    dependencies=["nonexistent"],
                )
            ],
            job_dir=Path("/tmp"),
        )

        with pytest.raises(ParseError, match="references non-existent step"):
            job.validate_file_inputs()

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
                    outputs=["output.md"],
                ),
                Step(
                    id="step2",
                    name="Step 2",
                    description="Step",
                    instructions_file="steps/step2.md",
                    inputs=[StepInput(file="data.md", from_step="step1")],
                    outputs=["output.md"],
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
