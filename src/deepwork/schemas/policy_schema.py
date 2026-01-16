"""JSON Schema definition for policy definitions (v2 - frontmatter format)."""

from typing import Any

# Pattern for string or array of strings
STRING_OR_ARRAY: dict[str, Any] = {
    "oneOf": [
        {"type": "string", "minLength": 1},
        {"type": "array", "items": {"type": "string", "minLength": 1}, "minItems": 1},
    ]
}

# JSON Schema for policy frontmatter (YAML between --- delimiters)
# Policies are stored as individual .md files in .deepwork/policies/
POLICY_FRONTMATTER_SCHEMA: dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {
            "type": "string",
            "minLength": 1,
            "description": "Human-friendly name for the policy (displayed in promise tags)",
        },
        # Detection mode: trigger/safety (mutually exclusive with set/pair)
        "trigger": {
            **STRING_OR_ARRAY,
            "description": "Glob pattern(s) for files that trigger this policy",
        },
        "safety": {
            **STRING_OR_ARRAY,
            "description": "Glob pattern(s) that suppress the policy if changed",
        },
        # Detection mode: set (bidirectional correspondence)
        "set": {
            "type": "array",
            "items": {"type": "string", "minLength": 1},
            "minItems": 2,
            "description": "Patterns defining bidirectional file correspondence",
        },
        # Detection mode: pair (directional correspondence)
        "pair": {
            "type": "object",
            "required": ["trigger", "expects"],
            "properties": {
                "trigger": {
                    "type": "string",
                    "minLength": 1,
                    "description": "Pattern that triggers the policy",
                },
                "expects": {
                    **STRING_OR_ARRAY,
                    "description": "Pattern(s) for expected corresponding files",
                },
            },
            "additionalProperties": False,
            "description": "Directional file correspondence (trigger -> expects)",
        },
        # Action type: command (default is prompt using markdown body)
        "action": {
            "type": "object",
            "required": ["command"],
            "properties": {
                "command": {
                    "type": "string",
                    "minLength": 1,
                    "description": "Command to run (supports {file}, {files}, {repo_root})",
                },
                "run_for": {
                    "type": "string",
                    "enum": ["each_match", "all_matches"],
                    "default": "each_match",
                    "description": "Run command for each file or all files at once",
                },
            },
            "additionalProperties": False,
            "description": "Command action to run instead of prompting",
        },
        # Common options
        "compare_to": {
            "type": "string",
            "enum": ["base", "default_tip", "prompt"],
            "default": "base",
            "description": "Baseline for detecting file changes",
        },
    },
    "additionalProperties": False,
    # Detection mode must be exactly one of: trigger, set, or pair
    "oneOf": [
        {
            "required": ["trigger"],
            "not": {"anyOf": [{"required": ["set"]}, {"required": ["pair"]}]},
        },
        {
            "required": ["set"],
            "not": {"anyOf": [{"required": ["trigger"]}, {"required": ["pair"]}]},
        },
        {
            "required": ["pair"],
            "not": {"anyOf": [{"required": ["trigger"]}, {"required": ["set"]}]},
        },
    ],
}


# Legacy schema for .deepwork.policy.yml (v1 format)
# Kept for reference but not used in v2
POLICY_SCHEMA_V1: dict[str, Any] = {
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
            "compare_to": {
                "type": "string",
                "enum": ["base", "default_tip", "prompt"],
                "description": (
                    "What to compare against when detecting changed files. "
                    "'base' (default) compares to the base of the current branch. "
                    "'default_tip' compares to the tip of the default branch. "
                    "'prompt' compares to the state at the start of the prompt."
                ),
            },
        },
        "oneOf": [
            {"required": ["instructions"]},
            {"required": ["instructions_file"]},
        ],
        "additionalProperties": False,
    },
}

# Alias for backwards compatibility
POLICY_SCHEMA = POLICY_SCHEMA_V1
