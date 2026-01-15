"""JSON Schema definition for policy definitions.

The schema is loaded from the JSON Schema file policy.schema.json.
This module provides backward-compatible access to the schema and related constants.
"""

from typing import Any

from deepwork.utils.validation import load_schema

# Valid compare_to values for policies
COMPARE_TO_VALUES = frozenset({"base", "default_tip", "prompt"})
DEFAULT_COMPARE_TO = "base"

# Schema name for loading (corresponds to policy.schema.json)
POLICY_SCHEMA_NAME = "policy.schema"


def get_policy_schema() -> dict[str, Any]:
    """
    Load and return the policy schema from the JSON Schema file.

    Returns:
        The policy JSON Schema as a dictionary
    """
    return load_schema(POLICY_SCHEMA_NAME)


# For backward compatibility, expose POLICY_SCHEMA as a module-level variable
# This is loaded lazily to avoid circular imports at module load time
def __getattr__(name: str) -> Any:
    if name == "POLICY_SCHEMA":
        return get_policy_schema()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
