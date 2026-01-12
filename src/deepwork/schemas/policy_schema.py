"""JSON Schema definition for policy definitions."""

from typing import Any

# JSON Schema for .deepwork.policy.yml files
# Policies are defined as an array of policy objects
POLICY_SCHEMA: dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "array",
    "description": "List of policies that trigger based on file changes",
    "items": {
        "type": "object",
        "required": ["name", "trigger"],
        "properties": {
            "name": {
                "type": "string",
                "minLength": 1,
                "description": "Friendly name for the policy",
            },
            "trigger": {
                "oneOf": [
                    {
                        "type": "string",
                        "minLength": 1,
                        "description": "Glob pattern for files that trigger this policy",
                    },
                    {
                        "type": "array",
                        "items": {"type": "string", "minLength": 1},
                        "minItems": 1,
                        "description": "List of glob patterns for files that trigger this policy",
                    },
                ],
                "description": "Glob pattern(s) for files that, if changed, should trigger this policy",
            },
            "safety": {
                "oneOf": [
                    {
                        "type": "string",
                        "minLength": 1,
                        "description": "Glob pattern for safety files",
                    },
                    {
                        "type": "array",
                        "items": {"type": "string", "minLength": 1},
                        "description": "List of glob patterns for safety files",
                    },
                ],
                "description": "Glob pattern(s) for files that, if also changed, mean the policy doesn't need to trigger",
            },
            "instructions": {
                "type": "string",
                "minLength": 1,
                "description": "Instructions to give the agent when this policy triggers",
            },
            "instructions_file": {
                "type": "string",
                "minLength": 1,
                "description": "Path to a file containing instructions (alternative to inline instructions)",
            },
        },
        "oneOf": [
            {"required": ["instructions"]},
            {"required": ["instructions_file"]},
        ],
        "additionalProperties": False,
    },
}
