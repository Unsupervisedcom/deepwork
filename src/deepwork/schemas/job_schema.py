"""JSON Schema definition for job definitions.

The schema is loaded from the JSON Schema file job.schema.json.
This module provides backward-compatible access to the schema and related constants.
"""

from typing import Any

from deepwork.utils.validation import load_schema

# Supported lifecycle hook events (generic names, mapped to platform-specific by adapters)
# These values must match CommandLifecycleHook enum in adapters.py
LIFECYCLE_HOOK_EVENTS = ["after_agent", "before_tool", "before_prompt"]

# Schema name for loading (corresponds to job.schema.json)
JOB_SCHEMA_NAME = "job.schema"


def get_job_schema() -> dict[str, Any]:
    """
    Load and return the job schema from the JSON Schema file.

    Returns:
        The job JSON Schema as a dictionary
    """
    return load_schema(JOB_SCHEMA_NAME)


# For backward compatibility, expose JOB_SCHEMA as a module-level variable
# This is loaded lazily to avoid circular imports at module load time
def __getattr__(name: str) -> Any:
    if name == "JOB_SCHEMA":
        return get_job_schema()
    if name == "HOOK_ACTION_SCHEMA":
        # Return the hookAction definition from the schema
        schema = get_job_schema()
        return schema.get("$defs", {}).get("hookAction", {})
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
