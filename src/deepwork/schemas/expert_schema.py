"""JSON Schema definitions for expert definitions."""

from typing import Any

# JSON Schema for expert.yml files
EXPERT_SCHEMA: dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["discovery_description", "full_expertise"],
    "properties": {
        "discovery_description": {
            "type": "string",
            "minLength": 1,
            "description": "Short description used to decide whether to invoke this expert. Keep concise and specific.",
        },
        "full_expertise": {
            "type": "string",
            "minLength": 1,
            "description": "Complete current knowledge of this domain (~5 pages max). This is included in the generated agent.",
        },
    },
    "additionalProperties": False,
}

# JSON Schema for topic frontmatter
TOPIC_FRONTMATTER_SCHEMA: dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {
            "type": "string",
            "minLength": 1,
            "description": "Human-readable topic name (e.g., 'Retry Handling')",
        },
        "keywords": {
            "type": "array",
            "description": "Topic-specific keywords (avoid broad terms like the expert domain)",
            "items": {
                "type": "string",
                "minLength": 1,
            },
        },
        "last_updated": {
            "type": "string",
            "pattern": r"^\d{4}-\d{2}-\d{2}$",
            "description": "Date stamp in YYYY-MM-DD format",
        },
    },
    "additionalProperties": False,
}

# JSON Schema for learning frontmatter
LEARNING_FRONTMATTER_SCHEMA: dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {
            "type": "string",
            "minLength": 1,
            "description": "Human-readable learning name (e.g., 'Job errors not going to Sentry')",
        },
        "last_updated": {
            "type": "string",
            "pattern": r"^\d{4}-\d{2}-\d{2}$",
            "description": "Date stamp in YYYY-MM-DD format",
        },
        "summarized_result": {
            "type": "string",
            "minLength": 1,
            "description": "Brief summary of the key finding (1-3 sentences)",
        },
    },
    "additionalProperties": False,
}
