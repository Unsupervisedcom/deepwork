"""Configuration parsing for DeepSchema files.

Parses deepschema.yml and .deepschema.<filename>.yml files into DeepSchema
dataclasses, validating against the JSON schema.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from deepwork.deepschema.schema import DEEPSCHEMA_SCHEMA
from deepwork.utils.validation import ValidationError, validate_against_schema
from deepwork.utils.yaml_utils import YAMLError, load_yaml


class DeepSchemaError(Exception):
    """Exception raised for DeepSchema configuration errors."""

    pass


@dataclass
class DeepSchema:
    """A single DeepSchema definition, either named or anonymous."""

    name: str
    schema_type: str  # "named" | "anonymous"
    source_path: Path  # Path to deepschema.yml or .deepschema.<file>.yml

    # Common fields
    requirements: dict[str, str] = field(default_factory=dict)
    parent_deep_schemas: list[str] = field(default_factory=list)
    json_schema_path: str | None = None
    verification_bash_command: list[str] = field(default_factory=list)

    # Named-schema-focused fields
    summary: str | None = None
    instructions: str | None = None
    examples: list[dict[str, str]] = field(default_factory=list)
    references: list[dict[str, str]] = field(default_factory=list)
    matchers: list[str] = field(default_factory=list)


def parse_deepschema_file(
    filepath: Path,
    schema_type: str,
    name: str,
) -> DeepSchema:
    """Parse a deepschema.yml or .deepschema.<file>.yml into a DeepSchema.

    Args:
        filepath: Path to the YAML file.
        schema_type: "named" or "anonymous".
        name: Schema name (directory name for named, target filename for anonymous).

    Returns:
        A DeepSchema object.

    Raises:
        DeepSchemaError: If the file cannot be parsed or fails validation.
    """
    try:
        data = load_yaml(filepath)
    except YAMLError as e:
        raise DeepSchemaError(f"Failed to parse {filepath}: {e}") from e

    if data is None:
        raise DeepSchemaError(f"File not found: {filepath}")

    if not data:
        return DeepSchema(name=name, schema_type=schema_type, source_path=filepath)

    try:
        validate_against_schema(data, DEEPSCHEMA_SCHEMA)
    except ValidationError as e:
        raise DeepSchemaError(f"Schema validation failed for {filepath}: {e}") from e

    return _build_deepschema(data, name, schema_type, filepath)


def _build_deepschema(
    data: dict[str, Any],
    name: str,
    schema_type: str,
    source_path: Path,
) -> DeepSchema:
    """Build a DeepSchema from parsed and validated YAML data."""
    return DeepSchema(
        name=name,
        schema_type=schema_type,
        source_path=source_path,
        requirements=data.get("requirements", {}),
        parent_deep_schemas=data.get("parent_deep_schemas", []),
        json_schema_path=data.get("json_schema_path"),
        verification_bash_command=data.get("verification_bash_command", []),
        summary=data.get("summary"),
        instructions=data.get("instructions"),
        examples=data.get("examples", []),
        references=data.get("references", []),
        matchers=data.get("matchers", []),
    )
