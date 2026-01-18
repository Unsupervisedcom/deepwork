"""JSON Schema definition for job definitions."""

from typing import Any

# Supported lifecycle hook events (generic names, mapped to platform-specific by adapters)
# These values must match CommandLifecycleHook enum in adapters.py
LIFECYCLE_HOOK_EVENTS = ["after_agent", "before_tool", "before_prompt"]

# Schema definitions for hook actions - each type is separate to enforce no mixing
PROMPT_HOOK_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["prompt"],
    "properties": {
        "prompt": {
            "type": "string",
            "minLength": 1,
            "description": "Inline prompt for validation/action",
        },
    },
    "additionalProperties": False,
}

PROMPT_FILE_HOOK_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["prompt_file"],
    "properties": {
        "prompt_file": {
            "type": "string",
            "minLength": 1,
            "description": "Path to prompt file (relative to job directory)",
        },
    },
    "additionalProperties": False,
}

SCRIPT_HOOK_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["script"],
    "properties": {
        "script": {
            "type": "string",
            "minLength": 1,
            "description": "Path to shell script (relative to job directory)",
        },
    },
    "additionalProperties": False,
}

# Schema for a hook event - must be all one type (no mixing script and prompt hooks)
# Each hook event is an array containing only one type of hook action
HOOK_EVENT_SCHEMA: dict[str, Any] = {
    "oneOf": [
        {
            "type": "array",
            "description": "Array of script hooks only",
            "items": SCRIPT_HOOK_SCHEMA,
        },
        {
            "type": "array",
            "description": "Array of prompt hooks only",
            "items": PROMPT_HOOK_SCHEMA,
        },
        {
            "type": "array",
            "description": "Array of prompt_file hooks only",
            "items": PROMPT_FILE_HOOK_SCHEMA,
        },
    ],
}

# Legacy schema for backward compatibility in stop_hooks (allows mixing)
HOOK_ACTION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "oneOf": [
        {
            "required": ["prompt"],
            "properties": {
                "prompt": {
                    "type": "string",
                    "minLength": 1,
                    "description": "Inline prompt for validation/action",
                },
            },
            "additionalProperties": False,
        },
        {
            "required": ["prompt_file"],
            "properties": {
                "prompt_file": {
                    "type": "string",
                    "minLength": 1,
                    "description": "Path to prompt file (relative to job directory)",
                },
            },
            "additionalProperties": False,
        },
        {
            "required": ["script"],
            "properties": {
                "script": {
                    "type": "string",
                    "minLength": 1,
                    "description": "Path to shell script (relative to job directory)",
                },
            },
            "additionalProperties": False,
        },
    ],
}

# JSON Schema for job.yml files
JOB_SCHEMA: dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["name", "version", "summary", "steps"],
    "properties": {
        "name": {
            "type": "string",
            "pattern": "^[a-z][a-z0-9_]*$",
            "description": "Job name (lowercase letters, numbers, underscores, must start with letter)",
        },
        "version": {
            "type": "string",
            "pattern": r"^\d+\.\d+\.\d+$",
            "description": "Semantic version (e.g., 1.0.0)",
        },
        "summary": {
            "type": "string",
            "minLength": 1,
            "maxLength": 200,
            "description": "Brief one-line summary of what this job accomplishes",
        },
        "description": {
            "type": "string",
            "minLength": 1,
            "description": "Detailed multi-line description of the job's purpose, process, and goals",
        },
        "changelog": {
            "type": "array",
            "description": "Version history and changes to the job",
            "items": {
                "type": "object",
                "required": ["version", "changes"],
                "properties": {
                    "version": {
                        "type": "string",
                        "pattern": r"^\d+\.\d+\.\d+$",
                        "description": "Version number for this change",
                    },
                    "changes": {
                        "type": "string",
                        "minLength": 1,
                        "description": "Description of changes made in this version",
                    },
                },
                "additionalProperties": False,
            },
        },
        "steps": {
            "type": "array",
            "minItems": 1,
            "description": "List of steps in the job",
            "items": {
                "type": "object",
                "required": ["id", "name", "description", "instructions_file", "outputs"],
                "properties": {
                    "id": {
                        "type": "string",
                        "pattern": "^[a-z][a-z0-9_]*$",
                        "description": "Step ID (unique within job)",
                    },
                    "name": {
                        "type": "string",
                        "minLength": 1,
                        "description": "Human-readable step name",
                    },
                    "description": {
                        "type": "string",
                        "minLength": 1,
                        "description": "Step description",
                    },
                    "instructions_file": {
                        "type": "string",
                        "minLength": 1,
                        "description": "Path to instructions file (relative to job directory)",
                    },
                    "inputs": {
                        "type": "array",
                        "description": "List of inputs (user parameters or files from previous steps)",
                        "items": {
                            "type": "object",
                            "oneOf": [
                                {
                                    "required": ["name", "description"],
                                    "properties": {
                                        "name": {
                                            "type": "string",
                                            "description": "Input parameter name",
                                        },
                                        "description": {
                                            "type": "string",
                                            "description": "Input parameter description",
                                        },
                                    },
                                    "additionalProperties": False,
                                },
                                {
                                    "required": ["file", "from_step"],
                                    "properties": {
                                        "file": {
                                            "type": "string",
                                            "description": "File name from previous step",
                                        },
                                        "from_step": {
                                            "type": "string",
                                            "description": "Step ID that produces this file",
                                        },
                                    },
                                    "additionalProperties": False,
                                },
                            ],
                        },
                    },
                    "outputs": {
                        "type": "array",
                        "description": "List of output files/directories",
                        "items": {
                            "type": "string",
                            "minLength": 1,
                        },
                    },
                    "dependencies": {
                        "type": "array",
                        "description": "List of step IDs this step depends on",
                        "items": {
                            "type": "string",
                        },
                        "default": [],
                    },
                    "hooks": {
                        "type": "object",
                        "description": "Lifecycle hooks for this step, keyed by event type. Each event must use only one hook type (script, prompt, or prompt_file) - mixing is not allowed.",
                        "properties": {
                            "after_agent": {
                                **HOOK_EVENT_SCHEMA,
                                "description": "Hooks triggered after the agent finishes (quality validation). Must be all scripts OR all prompts.",
                            },
                            "before_tool": {
                                **HOOK_EVENT_SCHEMA,
                                "description": "Hooks triggered before a tool is used. Must be all scripts OR all prompts.",
                            },
                            "before_prompt": {
                                **HOOK_EVENT_SCHEMA,
                                "description": "Hooks triggered when user submits a prompt. Must be all scripts OR all prompts.",
                            },
                        },
                        "additionalProperties": False,
                    },
                    # DEPRECATED: Use hooks.after_agent instead
                    "stop_hooks": {
                        "type": "array",
                        "description": "DEPRECATED: Use hooks.after_agent instead. Stop hooks for quality validation loops.",
                        "items": HOOK_ACTION_SCHEMA,
                    },
                    "exposed": {
                        "type": "boolean",
                        "description": "If true, step command is visible (no tilde prefix). Default: false (hidden).",
                        "default": False,
                    },
                    "quality_criteria": {
                        "type": "array",
                        "description": "Declarative quality criteria. Rendered with standard evaluation framing.",
                        "items": {
                            "type": "string",
                            "minLength": 1,
                        },
                    },
                },
                "additionalProperties": False,
            },
        },
    },
    "additionalProperties": False,
}
