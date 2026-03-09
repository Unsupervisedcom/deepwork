"""Tests for validation utilities."""

from pathlib import Path

import pytest

from deepwork.jobs.schema import JOB_SCHEMA
from deepwork.utils.validation import ValidationError, validate_against_schema


class TestValidateAgainstSchema:
    """Tests for validate_against_schema function."""

    def test_validates_simple_job(self) -> None:
        """Test that validate_against_schema accepts valid simple job."""
        job_data = {
            "name": "simple_job",
            "summary": "A simple job for testing",
            "step_arguments": [
                {
                    "name": "output",
                    "description": "Output file",
                    "type": "file_path",
                }
            ],
            "workflows": {
                "main": {
                    "summary": "Main workflow",
                    "steps": [
                        {
                            "name": "step1",
                            "instructions": "Do step 1.",
                            "outputs": {"output": {"required": True}},
                        }
                    ],
                }
            },
        }

        # Should not raise
        validate_against_schema(job_data, JOB_SCHEMA)

    def test_validates_job_with_inputs(self) -> None:
        """Test validation of job with step inputs."""
        job_data = {
            "name": "job_with_inputs",
            "summary": "Job with inputs",
            "step_arguments": [
                {"name": "param1", "description": "First parameter", "type": "string"},
                {"name": "output", "description": "Output file", "type": "file_path"},
            ],
            "workflows": {
                "main": {
                    "summary": "Main workflow",
                    "steps": [
                        {
                            "name": "step1",
                            "instructions": "Do step 1.",
                            "inputs": {"param1": {"required": True}},
                            "outputs": {"output": {"required": True}},
                        }
                    ],
                }
            },
        }

        validate_against_schema(job_data, JOB_SCHEMA)

    def test_validates_job_with_multiple_steps(self) -> None:
        """Test validation of job with multiple steps passing data."""
        job_data = {
            "name": "job_with_deps",
            "summary": "Job with dependencies",
            "step_arguments": [
                {"name": "data", "description": "Data output", "type": "file_path"},
                {"name": "result", "description": "Result output", "type": "file_path"},
            ],
            "workflows": {
                "main": {
                    "summary": "Main workflow",
                    "steps": [
                        {
                            "name": "step1",
                            "instructions": "Do step 1.",
                            "outputs": {"data": {"required": True}},
                        },
                        {
                            "name": "step2",
                            "instructions": "Do step 2.",
                            "inputs": {"data": {"required": True}},
                            "outputs": {"result": {"required": True}},
                        },
                    ],
                }
            },
        }

        validate_against_schema(job_data, JOB_SCHEMA)

    def test_raises_for_missing_required_field(self) -> None:
        """Test that validation fails for missing required fields."""
        job_data = {
            "name": "incomplete_job",
            # Missing summary, step_arguments, workflows
        }

        with pytest.raises(ValidationError, match="'summary' is a required property"):
            validate_against_schema(job_data, JOB_SCHEMA)

    def test_raises_for_invalid_job_name(self) -> None:
        """Test that validation fails for invalid job name."""
        job_data = {
            "name": "Invalid-Job-Name",  # Dashes not allowed
            "summary": "Invalid name test",
            "step_arguments": [],
            "workflows": {
                "main": {
                    "summary": "Main",
                    "steps": [{"name": "step1", "instructions": "Do it."}],
                }
            },
        }

        with pytest.raises(ValidationError, match="does not match"):
            validate_against_schema(job_data, JOB_SCHEMA)

    def test_raises_for_missing_workflow_summary(self) -> None:
        """Test that validation fails for workflow without summary."""
        job_data = {
            "name": "job",
            "summary": "Test",
            "step_arguments": [],
            "workflows": {
                "main": {
                    # Missing summary
                    "steps": [{"name": "step1", "instructions": "Do it."}],
                }
            },
        }

        with pytest.raises(ValidationError, match="'summary' is a required property"):
            validate_against_schema(job_data, JOB_SCHEMA)

    def test_validates_complex_job(self, fixtures_dir: Path) -> None:
        """Test validation of complex job fixture."""
        from deepwork.utils.yaml_utils import load_yaml

        complex_job_path = fixtures_dir / "jobs" / "complex_job" / "job.yml"
        job_data = load_yaml(complex_job_path)

        assert job_data is not None
        validate_against_schema(job_data, JOB_SCHEMA)

    def test_validates_workflow_with_agent(self) -> None:
        """Test that optional agent field on workflow passes validation."""
        job_data = {
            "name": "job",
            "summary": "Test",
            "step_arguments": [],
            "workflows": {
                "main": {
                    "summary": "Main workflow",
                    "agent": "general-purpose",
                    "steps": [{"name": "step1", "instructions": "Do it."}],
                }
            },
        }

        validate_against_schema(job_data, JOB_SCHEMA)

    def test_raises_for_workflow_agent_empty_string(self) -> None:
        """Test that empty string agent on workflow fails validation."""
        job_data = {
            "name": "job",
            "summary": "Test",
            "step_arguments": [],
            "workflows": {
                "main": {
                    "summary": "Main workflow",
                    "agent": "",
                    "steps": [{"name": "step1", "instructions": "Do it."}],
                }
            },
        }

        with pytest.raises(ValidationError):
            validate_against_schema(job_data, JOB_SCHEMA)

    def test_validates_step_with_review(self) -> None:
        """Test validation of step output with review block."""
        job_data = {
            "name": "job_with_review",
            "summary": "Job with review",
            "step_arguments": [
                {
                    "name": "report",
                    "description": "Report file",
                    "type": "file_path",
                    "review": {
                        "strategy": "individual",
                        "instructions": "Check the report for completeness.",
                    },
                }
            ],
            "workflows": {
                "main": {
                    "summary": "Main workflow",
                    "steps": [
                        {
                            "name": "write_report",
                            "instructions": "Write a report.",
                            "outputs": {"report": {"required": True}},
                        }
                    ],
                }
            },
        }

        validate_against_schema(job_data, JOB_SCHEMA)

    def test_validates_step_with_process_quality_attributes(self) -> None:
        """Test validation of step with process_quality_attributes."""
        job_data = {
            "name": "job",
            "summary": "Test",
            "step_arguments": [
                {"name": "output", "description": "Output", "type": "file_path"}
            ],
            "workflows": {
                "main": {
                    "summary": "Main",
                    "steps": [
                        {
                            "name": "step1",
                            "instructions": "Do it.",
                            "outputs": {"output": {"required": True}},
                            "process_quality_attributes": {
                                "thorough": "The work was thorough and complete.",
                            },
                        }
                    ],
                }
            },
        }

        validate_against_schema(job_data, JOB_SCHEMA)

    def test_validates_sub_workflow_step(self) -> None:
        """Test validation of step with sub_workflow reference."""
        job_data = {
            "name": "job",
            "summary": "Test",
            "step_arguments": [],
            "workflows": {
                "main": {
                    "summary": "Main",
                    "steps": [
                        {
                            "name": "delegate",
                            "sub_workflow": {"workflow_name": "helper"},
                        }
                    ],
                },
                "helper": {
                    "summary": "Helper workflow",
                    "steps": [{"name": "step1", "instructions": "Do it."}],
                },
            },
        }

        validate_against_schema(job_data, JOB_SCHEMA)
