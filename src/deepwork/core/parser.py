"""Job definition parser."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from deepwork.schemas.job_schema import JOB_SCHEMA
from deepwork.utils.validation import ValidationError, validate_against_schema
from deepwork.utils.yaml_utils import YAMLError, load_yaml


class ParseError(Exception):
    """Exception raised for job parsing errors."""

    pass


@dataclass
class StepInput:
    """Represents a step input (either user parameter or file from previous step)."""

    # User parameter input
    name: str | None = None
    description: str | None = None

    # File input from previous step
    file: str | None = None
    from_step: str | None = None

    def is_user_input(self) -> bool:
        """Check if this is a user parameter input."""
        return self.name is not None and self.description is not None

    def is_file_input(self) -> bool:
        """Check if this is a file input from previous step."""
        return self.file is not None and self.from_step is not None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StepInput":
        """Create StepInput from dictionary."""
        return cls(
            name=data.get("name"),
            description=data.get("description"),
            file=data.get("file"),
            from_step=data.get("from_step"),
        )


@dataclass
class Step:
    """Represents a single step in a job."""

    id: str
    name: str
    description: str
    instructions_file: str
    inputs: list[StepInput] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Step":
        """Create Step from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            instructions_file=data["instructions_file"],
            inputs=[StepInput.from_dict(inp) for inp in data.get("inputs", [])],
            outputs=data["outputs"],
            dependencies=data.get("dependencies", []),
        )


@dataclass
class JobDefinition:
    """Represents a complete job definition."""

    name: str
    version: str
    description: str
    steps: list[Step]
    job_dir: Path

    def get_step(self, step_id: str) -> Step | None:
        """
        Get step by ID.

        Args:
            step_id: Step ID to retrieve

        Returns:
            Step if found, None otherwise
        """
        for step in self.steps:
            if step.id == step_id:
                return step
        return None

    def validate_dependencies(self) -> None:
        """
        Validate step dependencies.

        Raises:
            ParseError: If dependencies are invalid (missing steps, circular deps)
        """
        step_ids = {step.id for step in self.steps}

        # Check all dependencies reference existing steps
        for step in self.steps:
            for dep_id in step.dependencies:
                if dep_id not in step_ids:
                    raise ParseError(
                        f"Step '{step.id}' depends on non-existent step '{dep_id}'"
                    )

        # Check for circular dependencies using topological sort
        visited = set()
        rec_stack = set()

        def has_cycle(step_id: str) -> bool:
            visited.add(step_id)
            rec_stack.add(step_id)

            step = self.get_step(step_id)
            if step:
                for dep_id in step.dependencies:
                    if dep_id not in visited:
                        if has_cycle(dep_id):
                            return True
                    elif dep_id in rec_stack:
                        return True

            rec_stack.remove(step_id)
            return False

        for step in self.steps:
            if step.id not in visited:
                if has_cycle(step.id):
                    raise ParseError(f"Circular dependency detected involving step '{step.id}'")

    def validate_file_inputs(self) -> None:
        """
        Validate that file inputs reference valid steps and dependencies.

        Raises:
            ParseError: If file inputs are invalid
        """
        for step in self.steps:
            for inp in step.inputs:
                if inp.is_file_input():
                    # Check that from_step exists
                    from_step = self.get_step(inp.from_step)  # type: ignore
                    if from_step is None:
                        raise ParseError(
                            f"Step '{step.id}' references non-existent step "
                            f"'{inp.from_step}' in file input"
                        )

                    # Check that from_step is in dependencies
                    if inp.from_step not in step.dependencies:
                        raise ParseError(
                            f"Step '{step.id}' has file input from '{inp.from_step}' "
                            f"but '{inp.from_step}' is not in dependencies"
                        )

    @classmethod
    def from_dict(cls, data: dict[str, Any], job_dir: Path) -> "JobDefinition":
        """
        Create JobDefinition from dictionary.

        Args:
            data: Parsed YAML data
            job_dir: Directory containing job definition

        Returns:
            JobDefinition instance
        """
        return cls(
            name=data["name"],
            version=data["version"],
            description=data["description"],
            steps=[Step.from_dict(step_data) for step_data in data["steps"]],
            job_dir=job_dir,
        )


def parse_job_definition(job_dir: Path | str) -> JobDefinition:
    """
    Parse job definition from directory.

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

    if job_data is None:
        raise ParseError("job.yml is empty")

    # Validate against schema
    try:
        validate_against_schema(job_data, JOB_SCHEMA)
    except ValidationError as e:
        raise ParseError(f"Job definition validation failed: {e}") from e

    # Parse into dataclass
    job_def = JobDefinition.from_dict(job_data, job_dir_path)

    # Validate dependencies and file inputs
    job_def.validate_dependencies()
    job_def.validate_file_inputs()

    return job_def
