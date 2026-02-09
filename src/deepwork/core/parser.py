"""Job definition parser."""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from deepwork.schemas.job_schema import JOB_SCHEMA, LIFECYCLE_HOOK_EVENTS
from deepwork.utils.validation import ValidationError, validate_against_schema
from deepwork.utils.yaml_utils import YAMLError, load_yaml

logger = logging.getLogger("deepwork.parser")


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
class OutputSpec:
    """Represents a step output specification with type information."""

    name: str
    type: str  # "file" or "files"
    description: str
    required: bool

    @classmethod
    def from_dict(cls, name: str, data: dict[str, Any]) -> "OutputSpec":
        """Create OutputSpec from output name and its specification dict."""
        return cls(
            name=name,
            type=data["type"],
            description=data["description"],
            required=data["required"],
        )


@dataclass
class HookAction:
    """Represents a hook action configuration.

    Hook actions define what happens when a lifecycle hook is triggered.
    Three types are supported:
    - prompt: Inline prompt text for validation/action
    - prompt_file: Path to a file containing the prompt
    - script: Path to a shell script for custom logic
    """

    # Inline prompt
    prompt: str | None = None

    # Prompt file reference (relative to job directory)
    prompt_file: str | None = None

    # Shell script reference (relative to job directory)
    script: str | None = None

    def is_prompt(self) -> bool:
        """Check if this is an inline prompt hook."""
        return self.prompt is not None

    def is_prompt_file(self) -> bool:
        """Check if this is a prompt file reference hook."""
        return self.prompt_file is not None

    def is_script(self) -> bool:
        """Check if this is a shell script hook."""
        return self.script is not None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HookAction":
        """Create HookAction from dictionary."""
        return cls(
            prompt=data.get("prompt"),
            prompt_file=data.get("prompt_file"),
            script=data.get("script"),
        )


# Backward compatibility alias
StopHook = HookAction


@dataclass
class Review:
    """Represents a quality review for step outputs."""

    run_each: str  # "step" or output name
    quality_criteria: dict[str, str]  # name → question
    additional_review_guidance: str | None = None  # optional guidance for reviewer

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Review":
        """Create Review from dictionary."""
        return cls(
            run_each=data["run_each"],
            quality_criteria=data.get("quality_criteria", {}),
            additional_review_guidance=data.get("additional_review_guidance"),
        )


@dataclass
class Step:
    """Represents a single step in a job."""

    id: str
    name: str
    description: str
    instructions_file: str
    inputs: list[StepInput] = field(default_factory=list)
    outputs: list[OutputSpec] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)

    # New: hooks dict mapping lifecycle event names to HookAction lists
    # Event names: after_agent, before_tool, before_prompt
    hooks: dict[str, list[HookAction]] = field(default_factory=dict)

    # If true, skill is user-invocable in menus. Default: false (hidden from menus).
    exposed: bool = False

    # Quality reviews to run when step completes
    reviews: list[Review] = field(default_factory=list)

    # Agent type for this step (e.g., "general-purpose"). When set, skill uses context: fork
    agent: str | None = None

    @property
    def stop_hooks(self) -> list[HookAction]:
        """
        Backward compatibility property for stop_hooks.

        Returns hooks for after_agent event.
        """
        return self.hooks.get("after_agent", [])

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Step":
        """Create Step from dictionary."""
        # Parse new hooks structure
        hooks: dict[str, list[HookAction]] = {}
        if "hooks" in data:
            hooks_data = data["hooks"]
            for event in LIFECYCLE_HOOK_EVENTS:
                if event in hooks_data:
                    hooks[event] = [HookAction.from_dict(h) for h in hooks_data[event]]

        # Handle deprecated stop_hooks -> after_agent
        if "stop_hooks" in data and data["stop_hooks"]:
            # Merge with any existing after_agent hooks
            after_agent_hooks = hooks.get("after_agent", [])
            after_agent_hooks.extend([HookAction.from_dict(h) for h in data["stop_hooks"]])
            hooks["after_agent"] = after_agent_hooks

        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            instructions_file=data["instructions_file"],
            inputs=[StepInput.from_dict(inp) for inp in data.get("inputs", [])],
            outputs=[
                OutputSpec.from_dict(name, spec) for name, spec in data.get("outputs", {}).items()
            ],
            dependencies=data.get("dependencies", []),
            hooks=hooks,
            exposed=data.get("exposed", False),
            reviews=[Review.from_dict(r) for r in data.get("reviews", [])],
            agent=data.get("agent"),
        )


@dataclass
class WorkflowStepEntry:
    """Represents a single entry in a workflow's step list.

    Each entry can be either:
    - A single step (sequential execution)
    - A list of steps (concurrent execution)
    """

    step_ids: list[str]  # Single step has one ID, concurrent group has multiple
    is_concurrent: bool = False

    @property
    def first_step(self) -> str:
        """Get the first step ID in this entry."""
        return self.step_ids[0] if self.step_ids else ""

    def all_step_ids(self) -> list[str]:
        """Get all step IDs in this entry."""
        return self.step_ids

    @classmethod
    def from_data(cls, data: str | list[str]) -> "WorkflowStepEntry":
        """Create WorkflowStepEntry from YAML data (string or list)."""
        if isinstance(data, str):
            return cls(step_ids=[data], is_concurrent=False)
        else:
            return cls(step_ids=list(data), is_concurrent=True)


@dataclass
class Workflow:
    """Represents a named workflow grouping steps into a multi-step sequence."""

    name: str
    summary: str
    step_entries: list[WorkflowStepEntry]  # List of step entries (sequential or concurrent)

    @property
    def steps(self) -> list[str]:
        """Get flattened list of all step IDs for backward compatibility."""
        result: list[str] = []
        for entry in self.step_entries:
            result.extend(entry.step_ids)
        return result

    def get_step_entry_for_step(self, step_id: str) -> WorkflowStepEntry | None:
        """Get the workflow step entry containing the given step ID."""
        for entry in self.step_entries:
            if step_id in entry.step_ids:
                return entry
        return None

    def get_entry_index_for_step(self, step_id: str) -> int | None:
        """Get the index of the entry containing the given step ID."""
        for i, entry in enumerate(self.step_entries):
            if step_id in entry.step_ids:
                return i
        return None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Workflow":
        """Create Workflow from dictionary."""
        step_entries = [WorkflowStepEntry.from_data(s) for s in data["steps"]]
        return cls(
            name=data["name"],
            summary=data["summary"],
            step_entries=step_entries,
        )


@dataclass
class JobDefinition:
    """Represents a complete job definition."""

    name: str
    version: str
    summary: str
    description: str | None
    steps: list[Step]
    job_dir: Path
    workflows: list[Workflow] = field(default_factory=list)

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
                    raise ParseError(f"Step '{step.id}' depends on non-existent step '{dep_id}'")

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

    def validate_reviews(self) -> None:
        """
        Validate that review run_each values reference valid output names or 'step'.

        Raises:
            ParseError: If run_each references an invalid output name
        """
        for step in self.steps:
            output_names = {out.name for out in step.outputs}
            for review in step.reviews:
                if review.run_each != "step" and review.run_each not in output_names:
                    raise ParseError(
                        f"Step '{step.id}' has review with run_each='{review.run_each}' "
                        f"but no output with that name. "
                        f"Valid values: 'step', {', '.join(sorted(output_names)) or '(no outputs)'}"
                    )

    def get_workflow_for_step(self, step_id: str) -> Workflow | None:
        """
        Get the workflow containing a step.

        Args:
            step_id: Step ID to look up

        Returns:
            Workflow containing the step, or None if step is standalone
        """
        for workflow in self.workflows:
            if step_id in workflow.steps:
                return workflow
        return None

    def get_next_step_in_workflow(self, step_id: str) -> str | None:
        """
        Get the next step in a workflow after the given step.

        Args:
            step_id: Current step ID

        Returns:
            Next step ID, or None if this is the last step or not in a workflow
        """
        workflow = self.get_workflow_for_step(step_id)
        if not workflow:
            return None
        try:
            index = workflow.steps.index(step_id)
            if index < len(workflow.steps) - 1:
                return workflow.steps[index + 1]
        except ValueError:
            pass
        return None

    def get_prev_step_in_workflow(self, step_id: str) -> str | None:
        """
        Get the previous step in a workflow before the given step.

        Args:
            step_id: Current step ID

        Returns:
            Previous step ID, or None if this is the first step or not in a workflow
        """
        workflow = self.get_workflow_for_step(step_id)
        if not workflow:
            return None
        try:
            index = workflow.steps.index(step_id)
            if index > 0:
                return workflow.steps[index - 1]
        except ValueError:
            pass
        return None

    def get_step_position_in_workflow(self, step_id: str) -> tuple[int, int] | None:
        """
        Get the position of a step within its workflow.

        Args:
            step_id: Step ID to look up

        Returns:
            Tuple of (1-based position, total steps in workflow), or None if standalone
        """
        workflow = self.get_workflow_for_step(step_id)
        if not workflow:
            return None
        try:
            index = workflow.steps.index(step_id)
            return (index + 1, len(workflow.steps))
        except ValueError:
            return None

    def get_step_entry_position_in_workflow(
        self, step_id: str
    ) -> tuple[int, int, WorkflowStepEntry] | None:
        """
        Get the entry-based position of a step within its workflow.

        For concurrent step groups, multiple steps share the same entry position.

        Args:
            step_id: Step ID to look up

        Returns:
            Tuple of (1-based entry position, total entries, WorkflowStepEntry),
            or None if standalone
        """
        workflow = self.get_workflow_for_step(step_id)
        if not workflow:
            return None

        entry_index = workflow.get_entry_index_for_step(step_id)
        if entry_index is None:
            return None

        entry = workflow.step_entries[entry_index]
        return (entry_index + 1, len(workflow.step_entries), entry)

    def get_concurrent_step_info(self, step_id: str) -> tuple[int, int] | None:
        """
        Get information about a step's position within a concurrent group.

        Args:
            step_id: Step ID to look up

        Returns:
            Tuple of (1-based position in group, total in group) if step is in
            a concurrent group, None if step is not in a concurrent group
        """
        workflow = self.get_workflow_for_step(step_id)
        if not workflow:
            return None

        entry = workflow.get_step_entry_for_step(step_id)
        if entry is None or not entry.is_concurrent:
            return None

        try:
            index = entry.step_ids.index(step_id)
            return (index + 1, len(entry.step_ids))
        except ValueError:
            return None

    def validate_workflows(self) -> None:
        """
        Validate workflow definitions.

        Raises:
            ParseError: If workflow references non-existent steps or has duplicates
        """
        step_ids = {step.id for step in self.steps}
        workflow_names = set()

        for workflow in self.workflows:
            # Check for duplicate workflow names
            if workflow.name in workflow_names:
                raise ParseError(f"Duplicate workflow name: '{workflow.name}'")
            workflow_names.add(workflow.name)

            # Check all step references exist
            for step_id in workflow.steps:
                if step_id not in step_ids:
                    raise ParseError(
                        f"Workflow '{workflow.name}' references non-existent step '{step_id}'"
                    )

            # Check for duplicate steps within a workflow
            seen_steps = set()
            for step_id in workflow.steps:
                if step_id in seen_steps:
                    raise ParseError(
                        f"Workflow '{workflow.name}' contains duplicate step '{step_id}'"
                    )
                seen_steps.add(step_id)

    def warn_orphaned_steps(self) -> list[str]:
        """
        Check for steps not included in any workflow and emit warnings.

        Returns:
            List of orphaned step IDs
        """
        # Collect all step IDs referenced in workflows
        workflow_step_ids: set[str] = set()
        for workflow in self.workflows:
            workflow_step_ids.update(workflow.steps)

        # Find orphaned steps
        orphaned_steps = [step.id for step in self.steps if step.id not in workflow_step_ids]

        if orphaned_steps:
            logger.warning(
                "Job '%s' has steps not included in any workflow: %s. "
                "These steps are not accessible via the MCP interface.",
                self.name,
                ", ".join(orphaned_steps),
            )

        return orphaned_steps

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
        workflows = [Workflow.from_dict(wf_data) for wf_data in data.get("workflows", [])]
        return cls(
            name=data["name"],
            version=data["version"],
            summary=data["summary"],
            description=data.get("description"),
            steps=[Step.from_dict(step_data) for step_data in data["steps"]],
            job_dir=job_dir,
            workflows=workflows,
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

    # Validate dependencies, file inputs, reviews, and workflows
    job_def.validate_dependencies()
    job_def.validate_file_inputs()
    job_def.validate_reviews()
    job_def.validate_workflows()

    # Warn about orphaned steps (not in any workflow)
    job_def.warn_orphaned_steps()

    return job_def
