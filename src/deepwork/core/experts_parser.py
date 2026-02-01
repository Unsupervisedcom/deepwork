"""Expert definition parser."""

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
from deepwork.utils.validation import ValidationError, validate_against_schema
from deepwork.utils.yaml_utils import YAMLError, load_yaml, load_yaml_from_string


class ExpertParseError(Exception):
    """Exception raised for expert parsing errors."""


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


@dataclass
class ExpertDefinition:
    """Represents a complete expert definition."""

    name: str  # Derived from folder name
    discovery_description: str
    full_expertise: str
    expert_dir: Path
    topics: list[Topic] = field(default_factory=list)
    learnings: list[Learning] = field(default_factory=list)

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

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        expert_dir: Path,
        topics: list[Topic] | None = None,
        learnings: list[Learning] | None = None,
    ) -> "ExpertDefinition":
        """
        Create ExpertDefinition from dictionary.

        Args:
            data: Parsed YAML data from expert.yml
            expert_dir: Directory containing expert definition
            topics: List of parsed topics
            learnings: List of parsed learnings

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
        )


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

    return ExpertDefinition.from_dict(expert_data, expert_dir_path, topics, learnings)


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
