"""JSON Schema definition for rule definitions (v2 - frontmatter format)."""

from typing import Any

# Pattern for string or array of strings
STRING_OR_ARRAY: dict[str, Any] = {
    "oneOf": [
        {"type": "string", "minLength": 1},
        {"type": "array", "items": {"type": "string", "minLength": 1}, "minItems": 1},
    ]
}

# JSON Schema for rule frontmatter (YAML between --- delimiters)
# Rules are stored as individual .md files in .deepwork/rules/
RULES_FRONTMATTER_SCHEMA: dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["name", "compare_to"],
    "properties": {
        "name": {
            "type": "string",
            "minLength": 1,
            "description": "Human-friendly name for the rule (displayed in promise tags)",
        },
        # Detection mode: trigger/safety (mutually exclusive with set/pair)
        "trigger": {
            **STRING_OR_ARRAY,
            "description": "Glob pattern(s) for files that trigger this rule",
        },
        "safety": {
            **STRING_OR_ARRAY,
            "description": "Glob pattern(s) that suppress the rule if changed",
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
                    "description": "Pattern that triggers the rule",
                },
                "expects": {
                    **STRING_OR_ARRAY,
                    "description": "Pattern(s) for expected corresponding files",
                },
            },
            "additionalProperties": False,
            "description": "Directional file correspondence (trigger -> expects)",
        },
        # Detection mode: created (fire when files are created matching patterns)
        "created": {
            **STRING_OR_ARRAY,
            "description": "Glob pattern(s) for newly created files that trigger this rule",
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
            "description": "Baseline for detecting file changes",
        },
        "prompt_runtime": {
            "type": "string",
            "enum": ["send_to_stopping_agent", "claude"],
            "default": "send_to_stopping_agent",
            "description": "Runtime for prompt action: 'send_to_stopping_agent' returns prompt to the agent that triggered the rule, 'claude' invokes Claude Code in headless mode",
        },
    },
    "additionalProperties": False,
    # Detection mode must be exactly one of: trigger, set, pair, or created
    "oneOf": [
        {
            "required": ["trigger"],
            "not": {
                "anyOf": [
                    {"required": ["set"]},
                    {"required": ["pair"]},
                    {"required": ["created"]},
                ]
            },
        },
        {
            "required": ["set"],
            "not": {
                "anyOf": [
                    {"required": ["trigger"]},
                    {"required": ["pair"]},
                    {"required": ["created"]},
                ]
            },
        },
        {
            "required": ["pair"],
            "not": {
                "anyOf": [
                    {"required": ["trigger"]},
                    {"required": ["set"]},
                    {"required": ["created"]},
                ]
            },
        },
        {
            "required": ["created"],
            "not": {
                "anyOf": [
                    {"required": ["trigger"]},
                    {"required": ["set"]},
                    {"required": ["pair"]},
                ]
            },
        },
    ],
}
