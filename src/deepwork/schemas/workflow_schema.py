"""JSON Schema definitions for workflow definitions.

Workflows are expert-owned multi-step sequences that live inside experts.
Each expert can have zero or more workflows in their workflows/ subdirectory.
"""

from typing import Any

# Supported lifecycle hook events (generic names, mapped to platform-specific by adapters)
# These values must match SkillLifecycleHook enum in adapters.py
LIFECYCLE_HOOK_EVENTS = ["after_agent", "before_tool", "before_prompt"]

# Schema definition for a single hook action (prompt, prompt_file, or script)
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
                    "pattern": "^[a-zA-Z0-9_][a-zA-Z0-9_./-]*$",
                    "not": {"pattern": r"\.\."},
                    "description": "Path to prompt file (relative to workflow directory). Cannot contain '..' for security.",
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
                    "pattern": "^[a-zA-Z0-9_][a-zA-Z0-9_./-]*$",
                    "not": {"pattern": r"\.\."},
                    "description": "Path to shell script (relative to workflow directory). Cannot contain '..' for security.",
                },
            },
            "additionalProperties": False,
        },
    ],
}

# Schema for a single step reference (step ID)
STEP_ID_SCHEMA: dict[str, Any] = {
    "type": "string",
    "pattern": "^[a-z][a-z0-9_]*$",
}

# Schema for a concurrent step group (array of step IDs that can run in parallel)
CONCURRENT_STEPS_SCHEMA: dict[str, Any] = {
    "type": "array",
    "minItems": 1,
    "description": "Array of step IDs that can be executed concurrently",
    "items": STEP_ID_SCHEMA,
}

# Schema for an execution order entry (either single step or concurrent group)
EXECUTION_ORDER_ENTRY_SCHEMA: dict[str, Any] = {
    "oneOf": [
        STEP_ID_SCHEMA,
        CONCURRENT_STEPS_SCHEMA,
    ],
}

# JSON Schema for workflow.yml files
WORKFLOW_SCHEMA: dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["name", "version", "summary", "steps"],
    "properties": {
        "name": {
            "type": "string",
            "pattern": "^[a-z][a-z0-9_]*$",
            "description": "Workflow name, must match folder name (lowercase letters, numbers, underscores)",
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
            "description": "Brief one-line summary of what this workflow accomplishes",
        },
        "description": {
            "type": "string",
            "minLength": 1,
            "description": "Detailed multi-line description of the workflow's purpose, process, and goals",
        },
        "steps": {
            "type": "array",
            "minItems": 1,
            "description": "List of steps in the workflow",
            "items": {
                "type": "object",
                "required": ["id", "name", "description", "instructions_file", "outputs"],
                "properties": {
                    "id": {
                        "type": "string",
                        "pattern": "^[a-z][a-z0-9_]*$",
                        "description": "Step ID (unique within expert)",
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
                        "description": "Path to instructions file (relative to workflow directory)",
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
                        "description": "List of output files/directories, optionally with document type references",
                        "items": {
                            "oneOf": [
                                {
                                    "type": "string",
                                    "minLength": 1,
                                    "description": "Simple output file path",
                                },
                                {
                                    "type": "object",
                                    "required": ["file"],
                                    "properties": {
                                        "file": {
                                            "type": "string",
                                            "minLength": 1,
                                            "description": "Output file path",
                                        },
                                        "doc_spec": {
                                            "type": "string",
                                            "pattern": r"^\.deepwork/doc_specs/[a-z][a-z0-9_-]*\.md$",
                                            "description": "Path to doc spec file",
                                        },
                                    },
                                    "additionalProperties": False,
                                },
                            ],
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
                        "description": "Lifecycle hooks for this step, keyed by event type",
                        "properties": {
                            "after_agent": {
                                "type": "array",
                                "description": "Hooks triggered after the agent finishes",
                                "items": HOOK_ACTION_SCHEMA,
                            },
                            "before_tool": {
                                "type": "array",
                                "description": "Hooks triggered before a tool is used",
                                "items": HOOK_ACTION_SCHEMA,
                            },
                            "before_prompt": {
                                "type": "array",
                                "description": "Hooks triggered when user submits a prompt",
                                "items": HOOK_ACTION_SCHEMA,
                            },
                        },
                        "additionalProperties": False,
                    },
                    "exposed": {
                        "type": "boolean",
                        "description": "If true, skill is user-invocable in menus. Default: false",
                        "default": False,
                    },
                    "quality_criteria": {
                        "type": "array",
                        "description": "Declarative quality criteria for validation",
                        "items": {
                            "type": "string",
                            "minLength": 1,
                        },
                    },
                    "agent": {
                        "type": "string",
                        "description": "Agent type for this step (e.g., 'general-purpose'). Enables context: fork.",
                        "minLength": 1,
                    },
                },
                "additionalProperties": False,
            },
        },
        "execution_order": {
            "type": "array",
            "description": "Explicit execution order with concurrent step support",
            "items": EXECUTION_ORDER_ENTRY_SCHEMA,
        },
        "changelog": {
            "type": "array",
            "description": "Version history and changes to the workflow",
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
    },
    "additionalProperties": False,
}
