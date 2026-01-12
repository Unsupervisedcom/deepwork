"""JSON Schema definition for job definitions."""

from typing import Any

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
                        "minItems": 1,
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
                },
                "additionalProperties": False,
            },
        },
    },
    "additionalProperties": False,
}
