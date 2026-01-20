"""JSON Schema definition for doc specs (document type definitions)."""

from typing import Any

# Schema for a single quality criterion
QUALITY_CRITERION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["name", "description"],
    "properties": {
        "name": {
            "type": "string",
            "minLength": 1,
            "description": "Short name for the quality criterion",
        },
        "description": {
            "type": "string",
            "minLength": 1,
            "description": "Detailed description of what this criterion requires",
        },
    },
    "additionalProperties": False,
}

# Schema for doc spec frontmatter
DOC_SPEC_FRONTMATTER_SCHEMA: dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["name", "description", "quality_criteria"],
    "properties": {
        "name": {
            "type": "string",
            "minLength": 1,
            "description": "Human-readable name for the document type",
        },
        "description": {
            "type": "string",
            "minLength": 1,
            "description": "Description of this document type's purpose",
        },
        "path_patterns": {
            "type": "array",
            "description": "Glob patterns for where documents of this type should be stored",
            "items": {
                "type": "string",
                "minLength": 1,
            },
        },
        "target_audience": {
            "type": "string",
            "description": "Who this document is written for",
        },
        "frequency": {
            "type": "string",
            "description": "How often this document type is produced (e.g., 'Monthly', 'Per sprint')",
        },
        "quality_criteria": {
            "type": "array",
            "description": "Quality criteria that documents of this type must meet",
            "minItems": 1,
            "items": QUALITY_CRITERION_SCHEMA,
        },
    },
    "additionalProperties": False,
}
