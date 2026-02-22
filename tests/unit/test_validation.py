"""Tests for validation utilities."""

import pytest

from deepwork.jobs.schema import JOB_SCHEMA
from deepwork.utils.validation import ValidationError, validate_against_schema


class TestValidateAgainstSchema:
    """Tests for validate_against_schema function."""

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-010.10.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_validates_simple_job(self) -> None:
        """Test that validate_against_schema accepts valid simple job."""
        job_data = {
            "name": "simple_job",
            "version": "1.0.0",
            "summary": "A simple job for testing",
            "common_job_info_provided_to_all_steps_at_runtime": "A simple job",
            "steps": [
                {
                    "id": "step1",
                    "name": "Step 1",
                    "description": "First step",
                    "instructions_file": "steps/step1.md",
                    "outputs": {
                        "output.md": {"type": "file", "description": "Output", "required": True}
                    },
                    "dependencies": [],
                    "reviews": [],
                }
            ],
        }

        # Should not raise
        validate_against_schema(job_data, JOB_SCHEMA)

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-010.10.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_validates_job_with_user_inputs(self) -> None:
        """Test validation of job with user input parameters."""
        job_data = {
            "name": "job_with_inputs",
            "version": "1.0.0",
            "summary": "Job with user inputs",
            "common_job_info_provided_to_all_steps_at_runtime": "Job with inputs",
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
                    "outputs": {
                        "output.md": {"type": "file", "description": "Output", "required": True}
                    },
                    "dependencies": [],
                    "reviews": [],
                }
            ],
        }

        validate_against_schema(job_data, JOB_SCHEMA)

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-010.10.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_validates_job_with_file_inputs(self) -> None:
        """Test validation of job with file inputs from previous steps."""
        job_data = {
            "name": "job_with_deps",
            "version": "1.0.0",
            "summary": "Job with dependencies",
            "common_job_info_provided_to_all_steps_at_runtime": "Job with dependencies",
            "steps": [
                {
                    "id": "step1",
                    "name": "Step 1",
                    "description": "First step",
                    "instructions_file": "steps/step1.md",
                    "outputs": {
                        "data.md": {"type": "file", "description": "Data output", "required": True}
                    },
                    "dependencies": [],
                    "reviews": [],
                },
                {
                    "id": "step2",
                    "name": "Step 2",
                    "description": "Second step",
                    "instructions_file": "steps/step2.md",
                    "inputs": [{"file": "data.md", "from_step": "step1"}],
                    "outputs": {
                        "result.md": {
                            "type": "file",
                            "description": "Result output",
                            "required": True,
                        }
                    },
                    "dependencies": ["step1"],
                    "reviews": [],
                },
            ],
        }

        validate_against_schema(job_data, JOB_SCHEMA)

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-010.10.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_raises_for_missing_required_field(self) -> None:
        """Test that validation fails for missing required fields."""
        job_data = {
            "name": "incomplete_job",
            "version": "1.0.0",
            # Missing summary
            # Missing common_job_info_provided_to_all_steps_at_runtime
            "steps": [],
        }

        with pytest.raises(ValidationError, match="'summary' is a required property"):
            validate_against_schema(job_data, JOB_SCHEMA)

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-010.10.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_raises_for_invalid_job_name(self) -> None:
        """Test that validation fails for invalid job name."""
        job_data = {
            "name": "Invalid-Job-Name",  # Dashes not allowed
            "version": "1.0.0",
            "summary": "Invalid name test",
            "common_job_info_provided_to_all_steps_at_runtime": "Invalid name",
            "steps": [
                {
                    "id": "step1",
                    "name": "Step 1",
                    "description": "Step",
                    "instructions_file": "steps/step1.md",
                    "outputs": {
                        "output.md": {"type": "file", "description": "Output", "required": True}
                    },
                    "reviews": [],
                }
            ],
        }

        with pytest.raises(ValidationError, match="does not match"):
            validate_against_schema(job_data, JOB_SCHEMA)

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-010.10.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_raises_for_invalid_version(self) -> None:
        """Test that validation fails for invalid version format."""
        job_data = {
            "name": "job",
            "version": "1.0",  # Not semver
            "summary": "Invalid version test",
            "common_job_info_provided_to_all_steps_at_runtime": "Job",
            "steps": [
                {
                    "id": "step1",
                    "name": "Step 1",
                    "description": "Step",
                    "instructions_file": "steps/step1.md",
                    "outputs": {
                        "output.md": {"type": "file", "description": "Output", "required": True}
                    },
                    "reviews": [],
                }
            ],
        }

        with pytest.raises(ValidationError, match="does not match"):
            validate_against_schema(job_data, JOB_SCHEMA)

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-010.10.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_raises_for_empty_steps(self) -> None:
        """Test that validation fails for empty steps array."""
        job_data = {
            "name": "job",
            "version": "1.0.0",
            "summary": "Empty steps test",
            "common_job_info_provided_to_all_steps_at_runtime": "Job with no steps",
            "steps": [],
        }

        with pytest.raises(ValidationError, match="should be non-empty"):
            validate_against_schema(job_data, JOB_SCHEMA)

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-010.10.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_raises_for_step_missing_outputs(self) -> None:
        """Test that validation fails for step without outputs."""
        job_data = {
            "name": "job",
            "version": "1.0.0",
            "summary": "Missing outputs test",
            "common_job_info_provided_to_all_steps_at_runtime": "Job",
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

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-010.10.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_raises_for_invalid_input_format(self) -> None:
        """Test that validation fails for invalid input format."""
        job_data = {
            "name": "job",
            "version": "1.0.0",
            "summary": "Invalid input format test",
            "common_job_info_provided_to_all_steps_at_runtime": "Job",
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
                    "outputs": {
                        "output.md": {"type": "file", "description": "Output", "required": True}
                    },
                    "reviews": [],
                }
            ],
        }

        with pytest.raises(ValidationError):
            validate_against_schema(job_data, JOB_SCHEMA)

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-010.10.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_validates_complex_job(self, fixtures_dir) -> None:
        """Test validation of complex job fixture."""
        from deepwork.utils.yaml_utils import load_yaml

        complex_job_path = fixtures_dir / "jobs" / "complex_job" / "job.yml"
        job_data = load_yaml(complex_job_path)

        assert job_data is not None
        validate_against_schema(job_data, JOB_SCHEMA)

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-010.10.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_raises_for_step_missing_reviews(self) -> None:
        """Test that validation fails for step without reviews field."""
        job_data = {
            "name": "job",
            "version": "1.0.0",
            "summary": "Missing reviews test",
            "common_job_info_provided_to_all_steps_at_runtime": "Job",
            "steps": [
                {
                    "id": "step1",
                    "name": "Step 1",
                    "description": "Step",
                    "instructions_file": "steps/step1.md",
                    "outputs": {
                        "output.md": {"type": "file", "description": "Output", "required": True}
                    },
                    # Missing reviews - now required
                }
            ],
        }

        with pytest.raises(ValidationError, match="'reviews' is a required property"):
            validate_against_schema(job_data, JOB_SCHEMA)

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-010.10.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_validates_job_with_reviews(self) -> None:
        """Test validation of job with reviews."""
        job_data = {
            "name": "job_with_reviews",
            "version": "1.0.0",
            "summary": "Job with reviews",
            "common_job_info_provided_to_all_steps_at_runtime": "Job",
            "steps": [
                {
                    "id": "step1",
                    "name": "Step 1",
                    "description": "Step",
                    "instructions_file": "steps/step1.md",
                    "outputs": {
                        "report.md": {"type": "file", "description": "Report", "required": True},
                    },
                    "reviews": [
                        {
                            "run_each": "step",
                            "quality_criteria": {
                                "Complete": "Is it complete?",
                                "Valid": "Is it valid?",
                            },
                        },
                        {
                            "run_each": "report.md",
                            "quality_criteria": {
                                "Well Written": "Is it well written?",
                            },
                        },
                    ],
                }
            ],
        }

        validate_against_schema(job_data, JOB_SCHEMA)

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-010.10.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_raises_for_review_missing_run_each(self) -> None:
        """Test validation fails for review without run_each."""
        job_data = {
            "name": "job",
            "version": "1.0.0",
            "summary": "Test",
            "common_job_info_provided_to_all_steps_at_runtime": "Job",
            "steps": [
                {
                    "id": "step1",
                    "name": "Step 1",
                    "description": "Step",
                    "instructions_file": "steps/step1.md",
                    "outputs": {
                        "output.md": {"type": "file", "description": "Output", "required": True}
                    },
                    "reviews": [
                        {
                            # Missing run_each
                            "quality_criteria": {"Test": "Is it tested?"},
                        }
                    ],
                }
            ],
        }

        with pytest.raises(ValidationError):
            validate_against_schema(job_data, JOB_SCHEMA)

    # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-010.10.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_raises_for_review_empty_criteria(self) -> None:
        """Test validation fails for review with empty quality_criteria."""
        job_data = {
            "name": "job",
            "version": "1.0.0",
            "summary": "Test",
            "common_job_info_provided_to_all_steps_at_runtime": "Job",
            "steps": [
                {
                    "id": "step1",
                    "name": "Step 1",
                    "description": "Step",
                    "instructions_file": "steps/step1.md",
                    "outputs": {
                        "output.md": {"type": "file", "description": "Output", "required": True}
                    },
                    "reviews": [
                        {
                            "run_each": "step",
                            "quality_criteria": {},  # Empty - minProperties: 1
                        }
                    ],
                }
            ],
        }

        with pytest.raises(ValidationError):
            validate_against_schema(job_data, JOB_SCHEMA)
