"""JSON Schema loader for DeepSchema definition files."""

import json
from pathlib import Path
from typing import Any

_SCHEMA_FILE = Path(__file__).parent.parent / "schemas" / "deepschema_schema.json"


def _load_schema() -> dict[str, Any]:
    """Load the JSON schema from file."""
    with open(_SCHEMA_FILE) as f:
        result: dict[str, Any] = json.load(f)
        return result


DEEPSCHEMA_SCHEMA: dict[str, Any] = _load_schema()
