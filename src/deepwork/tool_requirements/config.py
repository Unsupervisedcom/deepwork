"""Configuration parsing for tool requirements policy files.

Parses .deepwork/tool_requirements/*.yml files into ToolPolicy dataclasses,
validating against the JSON schema.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from deepwork.utils.validation import ValidationError, validate_against_schema
from deepwork.utils.yaml_utils import YAMLError, load_yaml

# Load the JSON schema once at module level
_SCHEMA_PATH = Path(__file__).parent.parent / "schemas" / "tool_requirements_schema.json"
_SCHEMA: dict[str, Any] | None = None


def _get_schema() -> dict[str, Any]:
    global _SCHEMA
    if _SCHEMA is None:
        _SCHEMA = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    return _SCHEMA


class ToolRequirementsError(Exception):
    """Exception raised for tool requirements configuration errors."""

    pass


@dataclass
class Requirement:
    """A single RFC 2119 requirement within a policy."""

    rule: str
    no_exception: bool = False


@dataclass
class ToolPolicy:
    """A parsed tool requirements policy definition."""

    name: str
    source_path: Path
    summary: str = ""
    tools: list[str] = field(default_factory=list)
    match: dict[str, str] = field(default_factory=dict)
    requirements: dict[str, Requirement] = field(default_factory=dict)
    extends: list[str] = field(default_factory=list)


def parse_policy_file(filepath: Path) -> ToolPolicy:
    """Parse a tool requirements YAML file into a ToolPolicy.

    Args:
        filepath: Path to the YAML file.

    Returns:
        A ToolPolicy object.

    Raises:
        ToolRequirementsError: If the file cannot be parsed or fails validation.
    """
    try:
        data = load_yaml(filepath)
    except YAMLError as e:
        raise ToolRequirementsError(f"Failed to parse {filepath}: {e}") from e

    if data is None:
        raise ToolRequirementsError(f"File not found: {filepath}")

    if not data:
        raise ToolRequirementsError(f"Empty policy file: {filepath}")

    try:
        validate_against_schema(data, _get_schema())
    except ValidationError as e:
        raise ToolRequirementsError(f"Schema validation failed for {filepath}: {e}") from e

    return _build_policy(data, filepath)


def _build_policy(data: dict[str, Any], filepath: Path) -> ToolPolicy:
    """Build a ToolPolicy from validated YAML data."""
    name = filepath.stem

    requirements: dict[str, Requirement] = {}
    for req_id, req_data in data.get("requirements", {}).items():
        requirements[req_id] = Requirement(
            rule=req_data["rule"],
            no_exception=req_data.get("no_exception", False),
        )

    return ToolPolicy(
        name=name,
        source_path=filepath,
        summary=data.get("summary", ""),
        tools=data.get("tools", []),
        match=data.get("match", {}),
        requirements=requirements,
        extends=data.get("extends", []),
    )
