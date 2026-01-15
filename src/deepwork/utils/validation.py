"""Validation utilities using JSON Schema."""

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator, validate
from jsonschema import ValidationError as JSONSchemaValidationError
from jsonschema.validators import extend


class ValidationError(Exception):
    """Exception raised for validation errors."""

    pass


# Cache for loaded schemas
_schema_cache: dict[str, dict[str, Any]] = {}

# Directory where schema files are stored
SCHEMAS_DIR = Path(__file__).parent.parent / "schemas"


def load_schema(schema_name: str) -> dict[str, Any]:
    """
    Load a JSON Schema from file.

    Args:
        schema_name: Name of the schema file (without .json extension)
                     e.g., "job.schema" or "policy.schema"

    Returns:
        Parsed JSON Schema as a dictionary

    Raises:
        FileNotFoundError: If schema file doesn't exist
        json.JSONDecodeError: If schema file is invalid JSON
    """
    if schema_name in _schema_cache:
        return _schema_cache[schema_name]

    schema_path = SCHEMAS_DIR / f"{schema_name}.json"
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(schema_path, encoding="utf-8") as f:
        schema = json.load(f)

    _schema_cache[schema_name] = schema
    return dict(schema)


def _set_defaults(validator_class: type) -> type:
    """
    Create a validator class that sets default values during validation.

    This extends a jsonschema validator to fill in default values from the schema
    when they are not present in the data.

    Args:
        validator_class: The base validator class to extend

    Returns:
        Extended validator class that sets defaults
    """
    validate_properties = validator_class.VALIDATORS["properties"]  # type: ignore[attr-defined]

    def set_defaults_in_properties(
        validator: Any, properties: dict[str, Any], instance: Any, schema: dict[str, Any]
    ) -> Any:
        """Validator that sets defaults before validating properties."""
        # Only process dicts
        if not isinstance(instance, dict):
            yield from validate_properties(validator, properties, instance, schema)
            return

        # Set defaults for missing properties
        for prop, subschema in properties.items():
            if prop not in instance and "default" in subschema:
                instance[prop] = _deep_copy_default(subschema["default"])

        # Continue with normal validation
        yield from validate_properties(validator, properties, instance, schema)

    def set_defaults_in_items(
        validator: Any, items: dict[str, Any], instance: Any, schema: dict[str, Any]
    ) -> Any:
        """Validator that processes defaults in array items."""
        # Only process lists
        if not isinstance(instance, list):
            yield from validator_class.VALIDATORS["items"](  # type: ignore[attr-defined]
                validator, items, instance, schema
            )
            return

        # For each item in the array, if it's a dict and items schema has properties,
        # apply defaults recursively
        if isinstance(items, dict) and "properties" in items:
            for item in instance:
                if isinstance(item, dict):
                    for prop, subschema in items["properties"].items():
                        if prop not in item and "default" in subschema:
                            item[prop] = _deep_copy_default(subschema["default"])

        # Continue with normal validation
        yield from validator_class.VALIDATORS["items"](  # type: ignore[attr-defined]
            validator, items, instance, schema
        )

    return extend(  # type: ignore[no-any-return]
        validator_class,
        {"properties": set_defaults_in_properties, "items": set_defaults_in_items},
    )


def _deep_copy_default(value: Any) -> Any:
    """
    Create a deep copy of a default value.

    This ensures that mutable defaults (lists, dicts) don't get shared
    between different instances.
    """
    if isinstance(value, dict):
        return {k: _deep_copy_default(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [_deep_copy_default(item) for item in value]
    else:
        return value


# Create the default-setting validator
DefaultSettingValidator = _set_defaults(Draft7Validator)


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


def validate_and_set_defaults(data: Any, schema: dict[str, Any]) -> Any:
    """
    Validate data against JSON Schema and apply default values.

    This function mutates the input data in-place, adding default values
    for any missing properties that have defaults defined in the schema.

    Args:
        data: Data to validate (will be mutated in-place)
        schema: JSON Schema to validate against

    Returns:
        The input data with defaults applied (same object, mutated)

    Raises:
        ValidationError: If validation fails
    """
    try:
        # The DefaultSettingValidator sets defaults as it validates
        validator = DefaultSettingValidator(schema)
        errors = list(validator.iter_errors(data))
        if errors:
            # Report the first error
            e = errors[0]
            path = " -> ".join(str(p) for p in e.path) if e.path else "root"
            raise ValidationError(f"Validation error at {path}: {e.message}")
    except JSONSchemaValidationError as e:
        path = " -> ".join(str(p) for p in e.path) if e.path else "root"
        raise ValidationError(f"Validation error at {path}: {e.message}") from e

    return data


def validate_and_set_defaults_from_schema(data: Any, schema_name: str) -> Any:
    """
    Load a schema by name and validate data with defaults.

    Args:
        data: Data to validate (will be mutated in-place)
        schema_name: Name of the schema file (e.g., "job.schema", "policy.schema")

    Returns:
        The input data with defaults applied

    Raises:
        ValidationError: If validation fails
        FileNotFoundError: If schema file doesn't exist
    """
    schema = load_schema(schema_name)
    return validate_and_set_defaults(data, schema)
