"""Expert and workflow definition parser."""

import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from deepwork.schemas.expert_schema import (
    EXPERT_SCHEMA,
    LEARNING_FRONTMATTER_SCHEMA,
    TOPIC_FRONTMATTER_SCHEMA,
)
from deepwork.schemas.workflow_schema import LIFECYCLE_HOOK_EVENTS, WORKFLOW_SCHEMA
from deepwork.utils.validation import ValidationError, validate_against_schema
from deepwork.utils.yaml_utils import YAMLError, load_yaml, load_yaml_from_string


class ExpertParseError(Exception):
    """Exception raised for expert parsing errors."""


class WorkflowParseError(Exception):
    """Exception raised for workflow parsing errors."""


def _folder_name_to_expert_name(folder_name: str) -> str:
    """
    Convert folder name to expert name.

    Spaces and underscores become dashes.
    Example: rails_activejob -> rails-activejob

    Args:
        folder_name: The folder name to convert

    Returns:
        The expert name
    """
    return folder_name.replace("_", "-").replace(" ", "-")


def _parse_frontmatter_markdown(content: str, file_type: str) -> tuple[dict[str, Any], str]:
    """
    Parse frontmatter from markdown content.

    Expects format:
    ---
    key: value
    ---
    markdown body

    Args:
        content: Full file content
        file_type: Type of file for error messages (e.g., "topic", "learning")

    Returns:
        Tuple of (frontmatter dict, body content)

    Raises:
        ExpertParseError: If frontmatter is missing or invalid
    """
    # Match frontmatter pattern: starts with ---, ends with ---
    pattern = r"^---[ \t]*\n(.*?)^---[ \t]*\n?(.*)"
    match = re.match(pattern, content.strip(), re.DOTALL | re.MULTILINE)

    if not match:
        raise ExpertParseError(
            f"{file_type.capitalize()} file must have YAML frontmatter (content between --- markers)"
        )

    frontmatter_yaml = match.group(1)
    body = match.group(2).strip() if match.group(2) else ""

    try:
        frontmatter = load_yaml_from_string(frontmatter_yaml)
    except YAMLError as e:
        raise ExpertParseError(f"Failed to parse {file_type} frontmatter: {e}") from e

    if frontmatter is None:
        frontmatter = {}

    return frontmatter, body


def _normalize_frontmatter_for_validation(frontmatter: dict[str, Any]) -> dict[str, Any]:
    """
    Normalize frontmatter data for schema validation.

    PyYAML auto-parses dates as datetime.date objects, but our schema
    expects strings. This function converts them back to strings.

    Args:
        frontmatter: Parsed frontmatter data

    Returns:
        Normalized frontmatter with dates as strings
    """
    result = frontmatter.copy()
    if "last_updated" in result and isinstance(result["last_updated"], date):
        result["last_updated"] = result["last_updated"].isoformat()
    return result


def _parse_date(date_value: str | date | None) -> date | None:
    """
    Parse a date value.

    Handles both string (YYYY-MM-DD) and datetime.date objects
    (which PyYAML may auto-parse).

    Args:
        date_value: Date string, date object, or None

    Returns:
        Parsed date or None
    """
    if date_value is None:
        return None
    if isinstance(date_value, date):
        return date_value
    try:
        return date.fromisoformat(date_value)
    except (ValueError, TypeError):
        return None


# =============================================================================
# Topic and Learning dataclasses
# =============================================================================


@dataclass
class Topic:
    """Represents a topic within an expert domain."""

    name: str
    keywords: list[str] = field(default_factory=list)
    last_updated: date | None = None
    body: str = ""
    source_file: Path | None = None

    @property
    def relative_path(self) -> str | None:
        """Get relative path for display (topics/filename.md)."""
        if self.source_file is None:
            return None
        return f"topics/{self.source_file.name}"

    @classmethod
    def from_dict(
        cls, data: dict[str, Any], body: str = "", source_file: Path | None = None
    ) -> "Topic":
        """Create Topic from dictionary."""
        return cls(
            name=data["name"],
            keywords=data.get("keywords", []),
            last_updated=_parse_date(data.get("last_updated")),
            body=body,
            source_file=source_file,
        )


@dataclass
class Learning:
    """Represents a learning within an expert domain."""

    name: str
    last_updated: date | None = None
    summarized_result: str | None = None
    body: str = ""
    source_file: Path | None = None

    @property
    def relative_path(self) -> str | None:
        """Get relative path for display (learnings/filename.md)."""
        if self.source_file is None:
            return None
        return f"learnings/{self.source_file.name}"

    @classmethod
    def from_dict(
        cls, data: dict[str, Any], body: str = "", source_file: Path | None = None
    ) -> "Learning":
        """Create Learning from dictionary."""
        return cls(
            name=data["name"],
            last_updated=_parse_date(data.get("last_updated")),
            summarized_result=data.get("summarized_result"),
            body=body,
            source_file=source_file,
        )


# =============================================================================
# Workflow-related dataclasses
# =============================================================================


@dataclass
class WorkflowStepInput:
    """Represents a workflow step input (either user parameter or file from previous step)."""

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
    def from_dict(cls, data: dict[str, Any]) -> "WorkflowStepInput":
        """Create WorkflowStepInput from dictionary."""
        return cls(
            name=data.get("name"),
            description=data.get("description"),
            file=data.get("file"),
            from_step=data.get("from_step"),
        )


@dataclass
class WorkflowOutputSpec:
    """Represents a workflow step output specification."""

    file: str
    doc_spec: str | None = None

    def has_doc_spec(self) -> bool:
        """Check if this output has a doc spec reference."""
        return self.doc_spec is not None

    @classmethod
    def from_dict(cls, data: dict[str, Any] | str) -> "WorkflowOutputSpec":
        """Create WorkflowOutputSpec from dictionary or string."""
        if isinstance(data, str):
            return cls(file=data)
        return cls(
            file=data["file"],
            doc_spec=data.get("doc_spec"),
        )


@dataclass
class WorkflowHookAction:
    """Represents a workflow hook action configuration."""

    # Inline prompt
    prompt: str | None = None

    # Prompt file reference (relative to workflow directory)
    prompt_file: str | None = None

    # Shell script reference (relative to workflow directory)
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
    def from_dict(cls, data: dict[str, Any]) -> "WorkflowHookAction":
        """Create WorkflowHookAction from dictionary."""
        return cls(
            prompt=data.get("prompt"),
            prompt_file=data.get("prompt_file"),
            script=data.get("script"),
        )


@dataclass
class WorkflowStep:
    """Represents a single step in a workflow."""

    id: str
    name: str
    description: str
    instructions_file: str
    inputs: list[WorkflowStepInput] = field(default_factory=list)
    outputs: list[WorkflowOutputSpec] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)

    # Hooks dict mapping lifecycle event names to HookAction lists
    hooks: dict[str, list[WorkflowHookAction]] = field(default_factory=dict)

    # If true, skill is user-invocable in menus
    exposed: bool = False

    # Declarative quality criteria
    quality_criteria: list[str] = field(default_factory=list)

    # Agent type for this step (e.g., "general-purpose")
    agent: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkflowStep":
        """Create WorkflowStep from dictionary."""
        # Parse hooks structure
        hooks: dict[str, list[WorkflowHookAction]] = {}
        if "hooks" in data:
            hooks_data = data["hooks"]
            for event in LIFECYCLE_HOOK_EVENTS:
                if event in hooks_data:
                    hooks[event] = [WorkflowHookAction.from_dict(h) for h in hooks_data[event]]

        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            instructions_file=data["instructions_file"],
            inputs=[WorkflowStepInput.from_dict(inp) for inp in data.get("inputs", [])],
            outputs=[WorkflowOutputSpec.from_dict(out) for out in data["outputs"]],
            dependencies=data.get("dependencies", []),
            hooks=hooks,
            exposed=data.get("exposed", False),
            quality_criteria=data.get("quality_criteria", []),
            agent=data.get("agent"),
        )


@dataclass
class ExecutionOrderEntry:
    """Represents an entry in the execution order (single step or concurrent group)."""

    step_ids: list[str]
    is_concurrent: bool = False

    @property
    def first_step(self) -> str:
        """Get the first step ID in this entry."""
        return self.step_ids[0] if self.step_ids else ""

    @classmethod
    def from_data(cls, data: str | list[str]) -> "ExecutionOrderEntry":
        """Create ExecutionOrderEntry from YAML data."""
        if isinstance(data, str):
            return cls(step_ids=[data], is_concurrent=False)
        else:
            return cls(step_ids=list(data), is_concurrent=len(data) > 1)


@dataclass
class WorkflowDefinition:
    """Represents a complete workflow definition."""

    name: str
    version: str
    summary: str
    description: str | None
    steps: list[WorkflowStep]
    workflow_dir: Path
    execution_order: list[ExecutionOrderEntry] = field(default_factory=list)

    # Reference to parent expert (set after parsing)
    expert_name: str | None = None

    def get_step(self, step_id: str) -> WorkflowStep | None:
        """Get step by ID."""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None

    def get_step_ids(self) -> list[str]:
        """Get all step IDs in this workflow."""
        return [step.id for step in self.steps]

    def get_execution_order_steps(self) -> list[str]:
        """Get flattened list of step IDs from execution order."""
        if not self.execution_order:
            # Default: steps in definition order
            return self.get_step_ids()
        result: list[str] = []
        for entry in self.execution_order:
            result.extend(entry.step_ids)
        return result

    def get_step_position(self, step_id: str) -> tuple[int, int] | None:
        """
        Get the position of a step within the workflow.

        Returns:
            Tuple of (1-based position, total steps), or None if not found
        """
        step_ids = self.get_execution_order_steps()
        try:
            index = step_ids.index(step_id)
            return (index + 1, len(step_ids))
        except ValueError:
            return None

    def get_next_step(self, step_id: str) -> str | None:
        """Get the next step ID after the given step."""
        step_ids = self.get_execution_order_steps()
        try:
            index = step_ids.index(step_id)
            if index < len(step_ids) - 1:
                return step_ids[index + 1]
        except ValueError:
            pass
        return None

    def get_prev_step(self, step_id: str) -> str | None:
        """Get the previous step ID before the given step."""
        step_ids = self.get_execution_order_steps()
        try:
            index = step_ids.index(step_id)
            if index > 0:
                return step_ids[index - 1]
        except ValueError:
            pass
        return None

    def validate_dependencies(self) -> None:
        """Validate step dependencies."""
        step_ids = {step.id for step in self.steps}

        # Check all dependencies reference existing steps
        for step in self.steps:
            for dep_id in step.dependencies:
                if dep_id not in step_ids:
                    raise WorkflowParseError(
                        f"Step '{step.id}' depends on non-existent step '{dep_id}'"
                    )

        # Check for circular dependencies
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
                    raise WorkflowParseError(
                        f"Circular dependency detected involving step '{step.id}'"
                    )

    def validate_file_inputs(self) -> None:
        """Validate that file inputs reference valid steps and dependencies."""
        for step in self.steps:
            for inp in step.inputs:
                if inp.is_file_input():
                    # Check that from_step exists
                    from_step = self.get_step(inp.from_step)  # type: ignore
                    if from_step is None:
                        raise WorkflowParseError(
                            f"Step '{step.id}' references non-existent step "
                            f"'{inp.from_step}' in file input"
                        )

                    # Check that from_step is in dependencies
                    if inp.from_step not in step.dependencies:
                        raise WorkflowParseError(
                            f"Step '{step.id}' has file input from '{inp.from_step}' "
                            f"but '{inp.from_step}' is not in dependencies"
                        )

    def validate_execution_order(self) -> None:
        """Validate execution order references valid steps."""
        if not self.execution_order:
            return

        step_ids = {step.id for step in self.steps}
        seen_in_order = set()

        for entry in self.execution_order:
            for step_id in entry.step_ids:
                if step_id not in step_ids:
                    raise WorkflowParseError(
                        f"Execution order references non-existent step '{step_id}'"
                    )
                if step_id in seen_in_order:
                    raise WorkflowParseError(
                        f"Step '{step_id}' appears multiple times in execution_order"
                    )
                seen_in_order.add(step_id)

    @classmethod
    def from_dict(cls, data: dict[str, Any], workflow_dir: Path) -> "WorkflowDefinition":
        """Create WorkflowDefinition from dictionary."""
        execution_order = [
            ExecutionOrderEntry.from_data(entry) for entry in data.get("execution_order", [])
        ]

        return cls(
            name=data["name"],
            version=data["version"],
            summary=data["summary"],
            description=data.get("description"),
            steps=[WorkflowStep.from_dict(step_data) for step_data in data["steps"]],
            workflow_dir=workflow_dir,
            execution_order=execution_order,
        )


# =============================================================================
# Expert definition dataclass
# =============================================================================


@dataclass
class ExpertDefinition:
    """Represents a complete expert definition."""

    name: str  # Derived from folder name
    discovery_description: str
    full_expertise: str
    expert_dir: Path
    topics: list[Topic] = field(default_factory=list)
    learnings: list[Learning] = field(default_factory=list)
    workflows: list[WorkflowDefinition] = field(default_factory=list)

    def get_topics_sorted(self) -> list[Topic]:
        """
        Get topics sorted by most-recently-updated.

        Topics without last_updated are sorted last.
        """
        return sorted(
            self.topics,
            key=lambda t: (t.last_updated is not None, t.last_updated),
            reverse=True,
        )

    def get_learnings_sorted(self) -> list[Learning]:
        """
        Get learnings sorted by most-recently-updated.

        Learnings without last_updated are sorted last.
        """
        return sorted(
            self.learnings,
            key=lambda learning: (learning.last_updated is not None, learning.last_updated),
            reverse=True,
        )

    def get_workflow(self, workflow_name: str) -> WorkflowDefinition | None:
        """Get a workflow by name."""
        for workflow in self.workflows:
            if workflow.name == workflow_name:
                return workflow
        return None

    def get_all_step_ids(self) -> set[str]:
        """Get all step IDs across all workflows in this expert."""
        step_ids: set[str] = set()
        for workflow in self.workflows:
            for step in workflow.steps:
                step_ids.add(step.id)
        return step_ids

    def validate_unique_step_ids(self) -> None:
        """Validate that step IDs are unique within the expert."""
        seen_ids: dict[str, str] = {}  # step_id -> workflow_name
        for workflow in self.workflows:
            for step in workflow.steps:
                if step.id in seen_ids:
                    raise ExpertParseError(
                        f"Step ID '{step.id}' is duplicated in workflows "
                        f"'{seen_ids[step.id]}' and '{workflow.name}'"
                    )
                seen_ids[step.id] = workflow.name

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        expert_dir: Path,
        topics: list[Topic] | None = None,
        learnings: list[Learning] | None = None,
        workflows: list[WorkflowDefinition] | None = None,
    ) -> "ExpertDefinition":
        """
        Create ExpertDefinition from dictionary.

        Args:
            data: Parsed YAML data from expert.yml
            expert_dir: Directory containing expert definition
            topics: List of parsed topics
            learnings: List of parsed learnings
            workflows: List of parsed workflows

        Returns:
            ExpertDefinition instance
        """
        name = _folder_name_to_expert_name(expert_dir.name)
        return cls(
            name=name,
            discovery_description=data["discovery_description"].strip(),
            full_expertise=data["full_expertise"].strip(),
            expert_dir=expert_dir,
            topics=topics or [],
            learnings=learnings or [],
            workflows=workflows or [],
        )


# =============================================================================
# Parsing functions
# =============================================================================


def parse_topic_file(filepath: Path | str) -> Topic:
    """
    Parse a topic file.

    Args:
        filepath: Path to the topic file (markdown with YAML frontmatter)

    Returns:
        Parsed Topic

    Raises:
        ExpertParseError: If parsing fails or validation errors occur
    """
    filepath = Path(filepath)

    if not filepath.exists():
        raise ExpertParseError(f"Topic file does not exist: {filepath}")

    if not filepath.is_file():
        raise ExpertParseError(f"Topic path is not a file: {filepath}")

    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception as e:
        raise ExpertParseError(f"Failed to read topic file: {e}") from e

    frontmatter, body = _parse_frontmatter_markdown(content, "topic")

    try:
        # Normalize frontmatter for validation (converts date objects to strings)
        normalized = _normalize_frontmatter_for_validation(frontmatter)
        validate_against_schema(normalized, TOPIC_FRONTMATTER_SCHEMA)
    except ValidationError as e:
        raise ExpertParseError(f"Topic validation failed in {filepath.name}: {e}") from e

    return Topic.from_dict(frontmatter, body, filepath)


def parse_learning_file(filepath: Path | str) -> Learning:
    """
    Parse a learning file.

    Args:
        filepath: Path to the learning file (markdown with YAML frontmatter)

    Returns:
        Parsed Learning

    Raises:
        ExpertParseError: If parsing fails or validation errors occur
    """
    filepath = Path(filepath)

    if not filepath.exists():
        raise ExpertParseError(f"Learning file does not exist: {filepath}")

    if not filepath.is_file():
        raise ExpertParseError(f"Learning path is not a file: {filepath}")

    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception as e:
        raise ExpertParseError(f"Failed to read learning file: {e}") from e

    frontmatter, body = _parse_frontmatter_markdown(content, "learning")

    try:
        # Normalize frontmatter for validation (converts date objects to strings)
        normalized = _normalize_frontmatter_for_validation(frontmatter)
        validate_against_schema(normalized, LEARNING_FRONTMATTER_SCHEMA)
    except ValidationError as e:
        raise ExpertParseError(f"Learning validation failed in {filepath.name}: {e}") from e

    return Learning.from_dict(frontmatter, body, filepath)


def parse_workflow_definition(workflow_dir: Path | str) -> WorkflowDefinition:
    """
    Parse workflow definition from directory.

    Args:
        workflow_dir: Directory containing workflow.yml

    Returns:
        Parsed WorkflowDefinition

    Raises:
        WorkflowParseError: If parsing fails or validation errors occur
    """
    workflow_dir_path = Path(workflow_dir)

    if not workflow_dir_path.exists():
        raise WorkflowParseError(f"Workflow directory does not exist: {workflow_dir_path}")

    if not workflow_dir_path.is_dir():
        raise WorkflowParseError(f"Workflow path is not a directory: {workflow_dir_path}")

    workflow_file = workflow_dir_path / "workflow.yml"
    if not workflow_file.exists():
        raise WorkflowParseError(f"workflow.yml not found in {workflow_dir_path}")

    # Load YAML
    try:
        workflow_data = load_yaml(workflow_file)
    except YAMLError as e:
        raise WorkflowParseError(f"Failed to load workflow.yml: {e}") from e

    if workflow_data is None:
        raise WorkflowParseError("workflow.yml is empty")

    # Validate against schema
    try:
        validate_against_schema(workflow_data, WORKFLOW_SCHEMA)
    except ValidationError as e:
        raise WorkflowParseError(f"Workflow definition validation failed: {e}") from e

    # Parse into dataclass
    workflow_def = WorkflowDefinition.from_dict(workflow_data, workflow_dir_path)

    # Validate dependencies, file inputs, and execution order
    workflow_def.validate_dependencies()
    workflow_def.validate_file_inputs()
    workflow_def.validate_execution_order()

    return workflow_def


def discover_expert_workflows(expert_dir: Path | str) -> list[Path]:
    """
    Discover all workflow directories in an expert.

    A workflow directory is one that contains a workflow.yml file.

    Args:
        expert_dir: Directory containing the expert

    Returns:
        List of paths to workflow directories
    """
    expert_dir_path = Path(expert_dir)
    workflows_dir = expert_dir_path / "workflows"

    if not workflows_dir.exists():
        return []

    if not workflows_dir.is_dir():
        return []

    workflow_dirs: list[Path] = []
    for subdir in workflows_dir.iterdir():
        if subdir.is_dir() and (subdir / "workflow.yml").exists():
            workflow_dirs.append(subdir)

    return workflow_dirs


def parse_expert_definition(expert_dir: Path | str) -> ExpertDefinition:
    """
    Parse expert definition from directory.

    Args:
        expert_dir: Directory containing expert.yml

    Returns:
        Parsed ExpertDefinition

    Raises:
        ExpertParseError: If parsing fails or validation errors occur
    """
    expert_dir_path = Path(expert_dir)

    if not expert_dir_path.exists():
        raise ExpertParseError(f"Expert directory does not exist: {expert_dir_path}")

    if not expert_dir_path.is_dir():
        raise ExpertParseError(f"Expert path is not a directory: {expert_dir_path}")

    expert_file = expert_dir_path / "expert.yml"
    if not expert_file.exists():
        raise ExpertParseError(f"expert.yml not found in {expert_dir_path}")

    # Load YAML
    try:
        expert_data = load_yaml(expert_file)
    except YAMLError as e:
        raise ExpertParseError(f"Failed to load expert.yml: {e}") from e

    if expert_data is None:
        raise ExpertParseError("expert.yml is empty")

    # Validate against schema
    try:
        validate_against_schema(expert_data, EXPERT_SCHEMA)
    except ValidationError as e:
        raise ExpertParseError(f"Expert definition validation failed: {e}") from e

    # Parse topics
    topics: list[Topic] = []
    topics_dir = expert_dir_path / "topics"
    if topics_dir.exists() and topics_dir.is_dir():
        for topic_file in topics_dir.glob("*.md"):
            topic = parse_topic_file(topic_file)
            topics.append(topic)

    # Parse learnings
    learnings: list[Learning] = []
    learnings_dir = expert_dir_path / "learnings"
    if learnings_dir.exists() and learnings_dir.is_dir():
        for learning_file in learnings_dir.glob("*.md"):
            learning = parse_learning_file(learning_file)
            learnings.append(learning)

    # Parse workflows
    workflows: list[WorkflowDefinition] = []
    workflow_dirs = discover_expert_workflows(expert_dir_path)
    expert_name = _folder_name_to_expert_name(expert_dir_path.name)
    for workflow_dir in workflow_dirs:
        try:
            workflow = parse_workflow_definition(workflow_dir)
            workflow.expert_name = expert_name
            workflows.append(workflow)
        except WorkflowParseError as e:
            # Re-raise with expert context
            raise ExpertParseError(
                f"Failed to parse workflow '{workflow_dir.name}' in expert '{expert_name}': {e}"
            ) from e

    expert = ExpertDefinition.from_dict(expert_data, expert_dir_path, topics, learnings, workflows)

    # Validate unique step IDs across all workflows in this expert
    expert.validate_unique_step_ids()

    return expert


def discover_experts(experts_dir: Path | str) -> list[Path]:
    """
    Discover all expert directories in a given directory.

    An expert directory is one that contains an expert.yml file.

    Args:
        experts_dir: Directory containing expert subdirectories

    Returns:
        List of paths to expert directories
    """
    experts_dir_path = Path(experts_dir)

    if not experts_dir_path.exists():
        return []

    if not experts_dir_path.is_dir():
        return []

    expert_dirs: list[Path] = []
    for subdir in experts_dir_path.iterdir():
        if subdir.is_dir() and (subdir / "expert.yml").exists():
            expert_dirs.append(subdir)

    return expert_dirs


# =============================================================================
# Formatting functions
# =============================================================================


def format_topics_markdown(expert: ExpertDefinition) -> str:
    """
    Format topics as a markdown list for CLI output.

    Returns name and relative file path as a markdown link,
    followed by keywords, sorted by most-recently-updated.

    Args:
        expert: Expert definition

    Returns:
        Markdown formatted list of topics
    """
    topics = expert.get_topics_sorted()
    if not topics:
        return "_No topics yet._"

    lines = []
    for topic in topics:
        # Format: [Topic Name](topics/filename.md)
        rel_path = topic.relative_path or "topics/unknown.md"
        line = f"- [{topic.name}]({rel_path})"
        if topic.keywords:
            line += f"\n  Keywords: {', '.join(topic.keywords)}"
        lines.append(line)

    return "\n".join(lines)


def format_learnings_markdown(expert: ExpertDefinition) -> str:
    """
    Format learnings as a markdown list for CLI output.

    Returns name and relative file path as a markdown link,
    followed by the summarized result, sorted by most-recently-updated.

    Args:
        expert: Expert definition

    Returns:
        Markdown formatted list of learnings
    """
    learnings = expert.get_learnings_sorted()
    if not learnings:
        return "_No learnings yet._"

    lines = []
    for learning in learnings:
        # Format: [Learning Name](learnings/filename.md)
        rel_path = learning.relative_path or "learnings/unknown.md"
        line = f"- [{learning.name}]({rel_path})"
        if learning.summarized_result:
            # Add indented summary
            summary_lines = learning.summarized_result.strip().split("\n")
            for summary_line in summary_lines:
                line += f"\n  {summary_line}"
        lines.append(line)

    return "\n".join(lines)
