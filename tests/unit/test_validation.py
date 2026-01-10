"""Tests for validation utilities."""

import pytest

from deepwork.schemas.job_schema import JOB_SCHEMA
from deepwork.utils.validation import ValidationError, validate_against_schema


class TestValidateAgainstSchema:
    """Tests for validate_against_schema function."""

    def test_validates_simple_job(self) -> None:
        """Test that validate_against_schema accepts valid simple job."""
        job_data = {
            "name": "simple_job",
            "version": "1.0.0",
            "description": "A simple job",
            "steps": [
                {
                    "id": "step1",
                    "name": "Step 1",
                    "description": "First step",
                    "instructions_file": "steps/step1.md",
                    "outputs": ["output.md"],
                    "dependencies": [],
                }
            ],
        }

        # Should not raise
        validate_against_schema(job_data, JOB_SCHEMA)

    def test_validates_job_with_user_inputs(self) -> None:
        """Test validation of job with user input parameters."""
        job_data = {
            "name": "job_with_inputs",
            "version": "1.0.0",
            "description": "Job with inputs",
            "steps": [
                {
                    "id": "step1",
                    "name": "Step 1",
                    "description": "Step with inputs",
                    "instructions_file": "steps/step1.md",
                    "inputs": [
                        {"name": "param1", "description": "First parameter"},
                        {"name": "param2", "description": "Second parameter"},
                    ],
                    "outputs": ["output.md"],
                    "dependencies": [],
                }
            ],
        }

        validate_against_schema(job_data, JOB_SCHEMA)

    def test_validates_job_with_file_inputs(self) -> None:
        """Test validation of job with file inputs from previous steps."""
        job_data = {
            "name": "job_with_deps",
            "version": "1.0.0",
            "description": "Job with dependencies",
            "steps": [
                {
                    "id": "step1",
                    "name": "Step 1",
                    "description": "First step",
                    "instructions_file": "steps/step1.md",
                    "outputs": ["data.md"],
                    "dependencies": [],
                },
                {
                    "id": "step2",
                    "name": "Step 2",
                    "description": "Second step",
                    "instructions_file": "steps/step2.md",
                    "inputs": [{"file": "data.md", "from_step": "step1"}],
                    "outputs": ["result.md"],
                    "dependencies": ["step1"],
                },
            ],
        }

        validate_against_schema(job_data, JOB_SCHEMA)

    def test_raises_for_missing_required_field(self) -> None:
        """Test that validation fails for missing required fields."""
        job_data = {
            "name": "incomplete_job",
            "version": "1.0.0",
            # Missing description
            "steps": [],
        }

        with pytest.raises(ValidationError, match="'description' is a required property"):
            validate_against_schema(job_data, JOB_SCHEMA)

    def test_raises_for_invalid_job_name(self) -> None:
        """Test that validation fails for invalid job name."""
        job_data = {
            "name": "Invalid-Job-Name",  # Dashes not allowed
            "version": "1.0.0",
            "description": "Invalid name",
            "steps": [
                {
                    "id": "step1",
                    "name": "Step 1",
                    "description": "Step",
                    "instructions_file": "steps/step1.md",
                    "outputs": ["output.md"],
                }
            ],
        }

        with pytest.raises(ValidationError, match="does not match"):
            validate_against_schema(job_data, JOB_SCHEMA)

    def test_raises_for_invalid_version(self) -> None:
        """Test that validation fails for invalid version format."""
        job_data = {
            "name": "job",
            "version": "1.0",  # Not semver
            "description": "Job",
            "steps": [
                {
                    "id": "step1",
                    "name": "Step 1",
                    "description": "Step",
                    "instructions_file": "steps/step1.md",
                    "outputs": ["output.md"],
                }
            ],
        }

        with pytest.raises(ValidationError, match="does not match"):
            validate_against_schema(job_data, JOB_SCHEMA)

    def test_raises_for_empty_steps(self) -> None:
        """Test that validation fails for empty steps array."""
        job_data = {
            "name": "job",
            "version": "1.0.0",
            "description": "Job with no steps",
            "steps": [],
        }

        with pytest.raises(ValidationError, match="should be non-empty"):
            validate_against_schema(job_data, JOB_SCHEMA)

    def test_raises_for_step_missing_outputs(self) -> None:
        """Test that validation fails for step without outputs."""
        job_data = {
            "name": "job",
            "version": "1.0.0",
            "description": "Job",
            "steps": [
                {
                    "id": "step1",
                    "name": "Step 1",
                    "description": "Step",
                    "instructions_file": "steps/step1.md",
                    # Missing outputs
                }
            ],
        }

        with pytest.raises(ValidationError, match="'outputs' is a required property"):
            validate_against_schema(job_data, JOB_SCHEMA)

    def test_raises_for_invalid_input_format(self) -> None:
        """Test that validation fails for invalid input format."""
        job_data = {
            "name": "job",
            "version": "1.0.0",
            "description": "Job",
            "steps": [
                {
                    "id": "step1",
                    "name": "Step 1",
                    "description": "Step",
                    "instructions_file": "steps/step1.md",
                    "inputs": [
                        {
                            "name": "param",
                            # Missing description for user input
                        }
                    ],
                    "outputs": ["output.md"],
                }
            ],
        }

        with pytest.raises(ValidationError):
            validate_against_schema(job_data, JOB_SCHEMA)

    def test_validates_complex_job(self, fixtures_dir) -> None:
        """Test validation of complex job fixture."""
        from deepwork.utils.yaml_utils import load_yaml

        complex_job_path = fixtures_dir / "jobs" / "complex_job" / "job.yml"
        job_data = load_yaml(complex_job_path)

        assert job_data is not None
        validate_against_schema(job_data, JOB_SCHEMA)
