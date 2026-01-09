"""Validation utilities using JSON Schema."""

from typing import Any

from jsonschema import ValidationError as JSONSchemaValidationError
from jsonschema import validate


class ValidationError(Exception):
    """Exception raised for validation errors."""

    pass


def validate_against_schema(data: dict[str, Any], schema: dict[str, Any]) -> None:
    """
    Validate data against JSON Schema.

    Args:
        data: Data to validate
        schema: JSON Schema to validate against

    Raises:
        ValidationError: If validation fails
    """
    try:
        validate(instance=data, schema=schema)
    except JSONSchemaValidationError as e:
        # Extract meaningful error message
        path = " -> ".join(str(p) for p in e.path) if e.path else "root"
        raise ValidationError(f"Validation error at {path}: {e.message}") from e
