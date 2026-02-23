"""Configuration parsing for .deepreview files.

Parses .deepreview YAML files into ReviewRule dataclasses, validating
against the JSON schema and resolving instruction file references.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from deepwork.review.schema import DEEPREVIEW_SCHEMA
from deepwork.utils.validation import ValidationError, validate_against_schema
from deepwork.utils.yaml_utils import YAMLError, load_yaml


class ConfigError(Exception):
    """Exception raised for .deepreview configuration errors."""

    pass


@dataclass
class ReviewRule:
    """A single named review rule from a .deepreview file."""

    name: str
    description: str
    include_patterns: list[str]
    exclude_patterns: list[str]
    strategy: str  # "individual" | "matches_together" | "all_changed_files"
    instructions: str  # Resolved instruction text
    agent: dict[str, str] | None
    all_changed_filenames: bool
    unchanged_matching_files: bool
    source_dir: Path  # Directory containing the .deepreview file
    source_file: Path  # Path to the .deepreview file
    source_line: int  # Line number of the rule name in the .deepreview file


@dataclass
class ReviewTask:
    """A single review task to be executed by an agent."""

    rule_name: str
    files_to_review: list[str]  # Paths relative to repo root
    instructions: str
    agent_name: str | None  # Agent persona for the target platform
    source_location: str = ""  # e.g. "src/.deepreview:5"
    additional_files: list[str] = field(default_factory=list)  # Unchanged matching files
    all_changed_filenames: list[str] | None = None


def parse_deepreview_file(filepath: Path) -> list[ReviewRule]:
    """Parse a .deepreview YAML file into ReviewRule objects.

    Args:
        filepath: Path to the .deepreview file.

    Returns:
        List of ReviewRule objects parsed from the file.

    Raises:
        ConfigError: If the file cannot be parsed or fails validation.
    """
    try:
        data = load_yaml(filepath)
    except YAMLError as e:
        raise ConfigError(f"Failed to parse {filepath}: {e}") from e

    if data is None:
        raise ConfigError(f"File not found: {filepath}")

    if not data:
        return []

    try:
        validate_against_schema(data, DEEPREVIEW_SCHEMA)
    except ValidationError as e:
        raise ConfigError(f"Schema validation failed for {filepath}: {e}") from e

    source_dir = filepath.parent
    line_numbers = _find_rule_line_numbers(filepath)
    rules: list[ReviewRule] = []

    for rule_name, rule_data in data.items():
        line = line_numbers.get(rule_name, 1)
        rule = _parse_rule(rule_name, rule_data, source_dir, filepath, line)
        rules.append(rule)

    return rules


def _parse_rule(
    name: str,
    data: dict[str, Any],
    source_dir: Path,
    source_file: Path,
    source_line: int,
) -> ReviewRule:
    """Parse a single rule from its YAML data.

    Args:
        name: The rule name (YAML key).
        data: The rule's YAML data.
        source_dir: Directory containing the .deepreview file.
        source_file: Path to the .deepreview file.
        source_line: Line number of the rule name in the file.

    Returns:
        A ReviewRule object.

    Raises:
        ConfigError: If instruction file references cannot be resolved.
    """
    description = data["description"]
    match_data = data["match"]
    review_data = data["review"]

    include_patterns = match_data["include"]
    exclude_patterns = match_data.get("exclude", [])

    strategy = review_data["strategy"]
    instructions = _resolve_instructions(review_data["instructions"], source_dir)
    agent = review_data.get("agent")

    additional_context = review_data.get("additional_context", {})
    all_changed_filenames = additional_context.get("all_changed_filenames", False)
    unchanged_matching_files = additional_context.get("unchanged_matching_files", False)

    return ReviewRule(
        name=name,
        description=description,
        include_patterns=include_patterns,
        exclude_patterns=exclude_patterns,
        strategy=strategy,
        instructions=instructions,
        agent=agent,
        all_changed_filenames=all_changed_filenames,
        unchanged_matching_files=unchanged_matching_files,
        source_dir=source_dir,
        source_file=source_file,
        source_line=source_line,
    )


def _resolve_instructions(instructions: str | dict[str, Any], source_dir: Path) -> str:
    """Resolve instruction text — either inline string or file reference.

    Args:
        instructions: Either a string (inline) or a dict with 'file' key.
        source_dir: Directory for resolving relative file paths.

    Returns:
        The resolved instruction text.

    Raises:
        ConfigError: If the referenced file does not exist or cannot be read.
    """
    if isinstance(instructions, str):
        return instructions

    # Must be a dict with 'file' key (validated by schema)
    file_ref: str = instructions["file"]
    file_path = source_dir / file_ref
    if not file_path.exists():
        raise ConfigError(f"Instructions file not found: {file_path}")

    try:
        return file_path.read_text(encoding="utf-8")
    except OSError as e:
        raise ConfigError(f"Failed to read instructions file {file_path}: {e}") from e


# Matches a top-level YAML key (no leading whitespace, followed by colon)
_RULE_NAME_RE = re.compile(r"^([a-zA-Z0-9_-]+)\s*:", re.MULTILINE)


def _find_rule_line_numbers(filepath: Path) -> dict[str, int]:
    """Scan a .deepreview file to find the line number of each top-level rule key.

    Args:
        filepath: Path to the .deepreview file.

    Returns:
        Dict mapping rule name to its 1-based line number.
    """
    try:
        text = filepath.read_text(encoding="utf-8")
    except OSError:
        return {}

    result: dict[str, int] = {}
    for i, line in enumerate(text.splitlines(), start=1):
        m = _RULE_NAME_RE.match(line)
        if m:
            result[m.group(1)] = i
    return result
