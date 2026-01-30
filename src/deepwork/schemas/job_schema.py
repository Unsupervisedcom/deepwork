"""JSON Schema definition for job definitions."""

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

# Schema for a workflow definition
WORKFLOW_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["name", "summary", "steps"],
    "properties": {
        "name": {
            "type": "string",
            "pattern": "^[a-z][a-z0-9_]*$",
            "description": "Workflow name (lowercase letters, numbers, underscores)",
        },
        "summary": {
            "type": "string",
            "minLength": 1,
            "maxLength": 200,
            "description": "Brief one-line summary of what this workflow accomplishes",
        },
        "steps": {
            "type": "array",
            "minItems": 1,
            "description": "Ordered list of step IDs that comprise this workflow",
            "items": {
                "type": "string",
                "pattern": "^[a-z][a-z0-9_]*$",
            },
        },
    },
    "additionalProperties": False,
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
        "workflows": {
            "type": "array",
            "description": "Named workflows that group steps into multi-step sequences",
            "items": WORKFLOW_SCHEMA,
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
                        "description": "List of output files/directories, optionally with document type references",
                        "items": {
                            "oneOf": [
                                {
                                    "type": "string",
                                    "minLength": 1,
                                    "description": "Simple output file path (backward compatible)",
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
                                "description": "Hooks triggered after the agent finishes (quality validation)",
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
                    # DEPRECATED: Use hooks.after_agent instead
                    "stop_hooks": {
                        "type": "array",
                        "description": "DEPRECATED: Use hooks.after_agent instead. Stop hooks for quality validation loops.",
                        "items": HOOK_ACTION_SCHEMA,
                    },
                    "exposed": {
                        "type": "boolean",
                        "description": "If true, skill is user-invocable in menus. Default: false (hidden from menus).",
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
                    "agent": {
                        "type": "string",
                        "description": "Agent type for this step. When set, the skill uses context: fork and delegates to the specified agent (e.g., 'general-purpose').",
                        "minLength": 1,
                    },
                },
                "additionalProperties": False,
            },
        },
    },
    "additionalProperties": False,
}
