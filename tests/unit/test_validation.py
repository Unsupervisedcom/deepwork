"""Tests for validation utilities."""

import pytest

from deepwork.schemas.workflow_schema import WORKFLOW_SCHEMA
from deepwork.utils.validation import ValidationError, validate_against_schema


class TestValidateAgainstSchema:
    """Tests for validate_against_schema function using workflow schema."""

    def test_validates_simple_workflow(self) -> None:
        """Test that validate_against_schema accepts valid simple workflow."""
        workflow_data = {
            "name": "simple_workflow",
            "version": "1.0.0",
            "summary": "A simple workflow for testing",
            "steps": [
                {
                    "id": "step1",
                    "name": "Step 1",
                    "description": "First step",
                    "instructions_file": "steps/step1.md",
                    "outputs": ["output.md"],
                }
            ],
        }

        # Should not raise
        validate_against_schema(workflow_data, WORKFLOW_SCHEMA)

    def test_validates_workflow_with_user_inputs(self) -> None:
        """Test validation of workflow with user input parameters."""
        workflow_data = {
            "name": "workflow_with_inputs",
            "version": "1.0.0",
            "summary": "Workflow with user inputs",
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
                }
            ],
        }

        validate_against_schema(workflow_data, WORKFLOW_SCHEMA)

    def test_validates_workflow_with_file_inputs(self) -> None:
        """Test validation of workflow with file inputs from previous steps."""
        workflow_data = {
            "name": "workflow_with_deps",
            "version": "1.0.0",
            "summary": "Workflow with dependencies",
            "steps": [
                {
                    "id": "step1",
                    "name": "Step 1",
                    "description": "First step",
                    "instructions_file": "steps/step1.md",
                    "outputs": ["data.md"],
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

        validate_against_schema(workflow_data, WORKFLOW_SCHEMA)

    def test_raises_for_missing_required_field(self) -> None:
        """Test that validation fails for missing required fields."""
        workflow_data = {
            "name": "incomplete_workflow",
            "version": "1.0.0",
            # Missing summary
            "steps": [],
        }

        with pytest.raises(ValidationError, match="'summary' is a required property"):
            validate_against_schema(workflow_data, WORKFLOW_SCHEMA)

    def test_raises_for_invalid_workflow_name(self) -> None:
        """Test that validation fails for invalid workflow name."""
        workflow_data = {
            "name": "Invalid-Workflow-Name",  # Dashes not allowed
            "version": "1.0.0",
            "summary": "Invalid name test",
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
            validate_against_schema(workflow_data, WORKFLOW_SCHEMA)

    def test_raises_for_invalid_version(self) -> None:
        """Test that validation fails for invalid version format."""
        workflow_data = {
            "name": "workflow",
            "version": "1.0",  # Not semver
            "summary": "Invalid version test",
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
            validate_against_schema(workflow_data, WORKFLOW_SCHEMA)

    def test_raises_for_empty_steps(self) -> None:
        """Test that validation fails for empty steps array."""
        workflow_data = {
            "name": "workflow",
            "version": "1.0.0",
            "summary": "Empty steps test",
            "steps": [],
        }

        with pytest.raises(ValidationError, match="should be non-empty"):
            validate_against_schema(workflow_data, WORKFLOW_SCHEMA)

    def test_raises_for_step_missing_outputs(self) -> None:
        """Test that validation fails for step without outputs."""
        workflow_data = {
            "name": "workflow",
            "version": "1.0.0",
            "summary": "Missing outputs test",
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
            validate_against_schema(workflow_data, WORKFLOW_SCHEMA)

    def test_raises_for_invalid_input_format(self) -> None:
        """Test that validation fails for invalid input format."""
        workflow_data = {
            "name": "workflow",
            "version": "1.0.0",
            "summary": "Invalid input format test",
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
            validate_against_schema(workflow_data, WORKFLOW_SCHEMA)

    def test_validates_workflow_with_hooks(self) -> None:
        """Test validation of workflow with hooks."""
        workflow_data = {
            "name": "workflow_with_hooks",
            "version": "1.0.0",
            "summary": "Workflow with hooks",
            "steps": [
                {
                    "id": "step1",
                    "name": "Step 1",
                    "description": "Step with hooks",
                    "instructions_file": "steps/step1.md",
                    "outputs": ["output.md"],
                    "hooks": {
                        "after_agent": [{"script": "validate.sh"}],
                    },
                }
            ],
        }

        validate_against_schema(workflow_data, WORKFLOW_SCHEMA)

    def test_validates_workflow_with_execution_order(self) -> None:
        """Test validation of workflow with execution order including concurrent steps."""
        workflow_data = {
            "name": "concurrent_workflow",
            "version": "1.0.0",
            "summary": "Workflow with concurrent steps",
            "steps": [
                {
                    "id": "step1",
                    "name": "Step 1",
                    "description": "First step",
                    "instructions_file": "steps/step1.md",
                    "outputs": ["output1.md"],
                },
                {
                    "id": "step2",
                    "name": "Step 2",
                    "description": "Second step (parallel)",
                    "instructions_file": "steps/step2.md",
                    "outputs": ["output2.md"],
                },
                {
                    "id": "step3",
                    "name": "Step 3",
                    "description": "Third step (parallel)",
                    "instructions_file": "steps/step3.md",
                    "outputs": ["output3.md"],
                },
                {
                    "id": "step4",
                    "name": "Step 4",
                    "description": "Final step",
                    "instructions_file": "steps/step4.md",
                    "outputs": ["output4.md"],
                },
            ],
            "execution_order": [
                "step1",
                ["step2", "step3"],  # Concurrent
                "step4",
            ],
        }

        validate_against_schema(workflow_data, WORKFLOW_SCHEMA)
