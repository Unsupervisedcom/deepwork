"""JSON Schema loader for job definitions.

This module loads the job.schema.json file and provides it as a Python dict
for use with jsonschema validation.
"""

import json
from pathlib import Path
from typing import Any

# Supported lifecycle hook events (generic names, mapped to platform-specific by adapters)
# These values must match SkillLifecycleHook enum in adapters.py
LIFECYCLE_HOOK_EVENTS = ["after_agent", "before_tool", "before_prompt"]

# Path to the JSON schema file
_SCHEMA_FILE = Path(__file__).parent / "job.schema.json"


def _load_schema() -> dict[str, Any]:
    """Load the JSON schema from file."""
    with open(_SCHEMA_FILE) as f:
        return json.load(f)


# Load the schema at module import time
JOB_SCHEMA: dict[str, Any] = _load_schema()


def get_schema_path() -> Path:
    """Get the path to the JSON schema file.

    Returns:
        Path to job.schema.json
    """
    return _SCHEMA_FILE
