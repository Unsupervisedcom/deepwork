"""Job definition parser."""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from deepwork.jobs.schema import JOB_SCHEMA
from deepwork.utils.validation import ValidationError, validate_against_schema
from deepwork.utils.yaml_utils import YAMLError, load_yaml

logger = logging.getLogger("deepwork.parser")


class ParseError(Exception):
    """Exception raised for job parsing errors."""

    pass


@dataclass
class ReviewBlock:
    """A review rule for an output, matching .deepreview review block shape."""

    strategy: str  # "individual" | "matches_together"
    instructions: str
    agent: dict[str, str] | None = None
    additional_context: dict[str, bool] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReviewBlock":
        """Create ReviewBlock from dictionary."""
        return cls(
            strategy=data["strategy"],
            instructions=data["instructions"],
            agent=data.get("agent"),
            additional_context=data.get("additional_context"),
        )


@dataclass
class StepArgument:
    """A shared input/output definition referenced by steps."""

    name: str
    description: str
    type: str  # "string" | "file_path"
    review: ReviewBlock | None = None
    json_schema: dict[str, Any] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StepArgument":
        """Create StepArgument from dictionary."""
        return cls(
            name=data["name"],
            description=data["description"],
            type=data["type"],
            review=ReviewBlock.from_dict(data["review"]) if "review" in data else None,
            json_schema=data.get("json_schema"),
        )


@dataclass
class StepInputRef:
    """Reference to a step_argument used as input."""

    argument_name: str
    required: bool = True

    @classmethod
    def from_dict(cls, name: str, data: dict[str, Any]) -> "StepInputRef":
        """Create StepInputRef from argument name and config."""
        return cls(
            argument_name=name,
            required=data.get("required", True),
        )


@dataclass
class StepOutputRef:
    """Reference to a step_argument used as output."""

    argument_name: str
    required: bool = True
    review: ReviewBlock | None = None

    @classmethod
    def from_dict(cls, name: str, data: dict[str, Any]) -> "StepOutputRef":
        """Create StepOutputRef from argument name and config."""
        return cls(
            argument_name=name,
            required=data.get("required", True),
            review=ReviewBlock.from_dict(data["review"]) if "review" in data else None,
        )


@dataclass
class SubWorkflowRef:
    """Reference to another workflow (same job or cross-job)."""

    workflow_name: str
    workflow_job: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SubWorkflowRef":
        """Create SubWorkflowRef from dictionary."""
        return cls(
            workflow_name=data["workflow_name"],
            workflow_job=data.get("workflow_job"),
        )


@dataclass
class WorkflowStep:
    """A single step within a workflow."""

    name: str
    instructions: str | None = None
    sub_workflow: SubWorkflowRef | None = None
    inputs: dict[str, StepInputRef] = field(default_factory=dict)
    outputs: dict[str, StepOutputRef] = field(default_factory=dict)
    process_requirements: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkflowStep":
        """Create WorkflowStep from dictionary."""
        inputs = {
            name: StepInputRef.from_dict(name, ref_data)
            for name, ref_data in data.get("inputs", {}).items()
        }
        outputs = {
            name: StepOutputRef.from_dict(name, ref_data)
            for name, ref_data in data.get("outputs", {}).items()
        }
        return cls(
            name=data["name"],
            instructions=data.get("instructions"),
            sub_workflow=(
                SubWorkflowRef.from_dict(data["sub_workflow"]) if "sub_workflow" in data else None
            ),
            inputs=inputs,
            outputs=outputs,
            process_requirements=data.get("process_requirements", {}),
        )


@dataclass
class Workflow:
    """A named workflow containing a sequence of steps."""

    name: str
    summary: str
    steps: list[WorkflowStep]
    agent: str | None = None
    common_job_info: str | None = None
    post_workflow_instructions: str | None = None

    @property
    def step_names(self) -> list[str]:
        """Get list of step names in order."""
        return [s.name for s in self.steps]

    def get_step(self, step_name: str) -> WorkflowStep | None:
        """Get step by name."""
        for step in self.steps:
            if step.name == step_name:
                return step
        return None

    def get_step_index(self, step_name: str) -> int | None:
        """Get index of step by name."""
        for i, step in enumerate(self.steps):
            if step.name == step_name:
                return i
        return None

    @classmethod
    def from_dict(cls, name: str, data: dict[str, Any]) -> "Workflow":
        """Create Workflow from workflow name and dictionary."""
        return cls(
            name=name,
            summary=data["summary"],
            steps=[WorkflowStep.from_dict(s) for s in data["steps"]],
            agent=data.get("agent"),
            common_job_info=data.get("common_job_info_provided_to_all_steps_at_runtime"),
            post_workflow_instructions=data.get("post_workflow_instructions"),
        )


@dataclass
class JobDefinition:
    """A complete job definition."""

    name: str
    summary: str
    step_arguments: list[StepArgument]
    workflows: dict[str, Workflow]
    job_dir: Path

    def get_argument(self, name: str) -> StepArgument | None:
        """Get step argument by name."""
        for arg in self.step_arguments:
            if arg.name == name:
                return arg
        return None

    def get_workflow(self, name: str) -> Workflow | None:
        """Get workflow by name."""
        return self.workflows.get(name)

    def validate_argument_refs(self) -> None:
        """Validate that all input/output refs point to valid step_arguments.

        Raises:
            ParseError: If refs point to non-existent arguments
        """
        arg_names = {arg.name for arg in self.step_arguments}

        for wf_name, workflow in self.workflows.items():
            for step in workflow.steps:
                for input_name in step.inputs:
                    if input_name not in arg_names:
                        raise ParseError(
                            f"Workflow '{wf_name}' step '{step.name}' references "
                            f"non-existent step_argument '{input_name}' in inputs"
                        )
                for output_name in step.outputs:
                    if output_name not in arg_names:
                        raise ParseError(
                            f"Workflow '{wf_name}' step '{step.name}' references "
                            f"non-existent step_argument '{output_name}' in outputs"
                        )

    def validate_sub_workflows(self) -> None:
        """Validate that sub_workflow refs point to valid workflows.

        Only validates same-job references (cross-job validated at runtime).

        Raises:
            ParseError: If refs point to non-existent workflows in same job
        """
        for wf_name, workflow in self.workflows.items():
            for step in workflow.steps:
                if step.sub_workflow and not step.sub_workflow.workflow_job:
                    if step.sub_workflow.workflow_name not in self.workflows:
                        raise ParseError(
                            f"Workflow '{wf_name}' step '{step.name}' references "
                            f"non-existent workflow '{step.sub_workflow.workflow_name}'"
                        )

    def validate_step_exclusivity(self) -> None:
        """Validate each step has exactly one of instructions or sub_workflow.

        Raises:
            ParseError: If a step has both or neither
        """
        for wf_name, workflow in self.workflows.items():
            for step in workflow.steps:
                has_instructions = step.instructions is not None
                has_sub_workflow = step.sub_workflow is not None
                if has_instructions and has_sub_workflow:
                    raise ParseError(
                        f"Workflow '{wf_name}' step '{step.name}' has both "
                        f"'instructions' and 'sub_workflow' — must have exactly one"
                    )
                if not has_instructions and not has_sub_workflow:
                    raise ParseError(
                        f"Workflow '{wf_name}' step '{step.name}' has neither "
                        f"'instructions' nor 'sub_workflow' — must have exactly one"
                    )

    def validate_unique_step_names(self) -> None:
        """Validate step names are unique within each workflow.

        Raises:
            ParseError: If duplicate step names found
        """
        for wf_name, workflow in self.workflows.items():
            seen: set[str] = set()
            for step in workflow.steps:
                if step.name in seen:
                    raise ParseError(f"Workflow '{wf_name}' has duplicate step name '{step.name}'")
                seen.add(step.name)

    @classmethod
    def from_dict(cls, data: dict[str, Any], job_dir: Path) -> "JobDefinition":
        """Create JobDefinition from dictionary."""
        step_arguments = [
            StepArgument.from_dict(arg_data) for arg_data in data.get("step_arguments", [])
        ]
        workflows = {
            name: Workflow.from_dict(name, wf_data)
            for name, wf_data in data.get("workflows", {}).items()
        }
        return cls(
            name=data["name"],
            summary=data["summary"],
            step_arguments=step_arguments,
            workflows=workflows,
            job_dir=job_dir,
        )


def parse_job_definition(job_dir: Path | str) -> JobDefinition:
    """Parse job definition from directory.

    Args:
        job_dir: Directory containing job.yml

    Returns:
        Parsed JobDefinition

    Raises:
        ParseError: If parsing fails or validation errors occur
    """
    job_dir_path = Path(job_dir)

    if not job_dir_path.exists():
        raise ParseError(f"Job directory does not exist: {job_dir_path}")

    if not job_dir_path.is_dir():
        raise ParseError(f"Job path is not a directory: {job_dir_path}")

    job_file = job_dir_path / "job.yml"
    if not job_file.exists():
        raise ParseError(f"job.yml not found in {job_dir_path}")

    # Load YAML
    try:
        job_data = load_yaml(job_file)
    except YAMLError as e:
        raise ParseError(f"Failed to load job.yml: {e}") from e

    if not job_data:
        raise ParseError("job.yml is empty")

    # Validate against schema
    try:
        validate_against_schema(job_data, JOB_SCHEMA)
    except ValidationError as e:
        raise ParseError(f"Job definition validation failed: {e}") from e

    # Parse into dataclass
    job_def = JobDefinition.from_dict(job_data, job_dir_path)

    # Run validations
    job_def.validate_unique_step_names()
    job_def.validate_argument_refs()
    job_def.validate_sub_workflows()
    job_def.validate_step_exclusivity()

    return job_def
