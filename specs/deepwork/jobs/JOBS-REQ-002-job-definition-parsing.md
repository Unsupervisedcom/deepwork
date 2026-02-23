# JOBS-REQ-002: Job Definition Parsing

## Overview

Job definitions are YAML files (`job.yml`) that declare multi-step workflows for AI agents. The parser reads these files, validates them against a JSON Schema, parses them into typed dataclasses, and performs semantic validation of dependencies, file inputs, reviews, and workflows. This is the foundation of the DeepWork configuration model.

## Requirements

### JOBS-REQ-002.1: Job File Structure

1. A valid job directory MUST contain a file named `job.yml`.
2. The parser MUST raise `ParseError` if the job directory does not exist.
3. The parser MUST raise `ParseError` if the job path is not a directory.
4. The parser MUST raise `ParseError` if `job.yml` is not found in the directory.
5. The parser MUST raise `ParseError` if `job.yml` is empty.
6. The parser MUST raise `ParseError` if `job.yml` contains invalid YAML.

### JOBS-REQ-002.2: JSON Schema Validation

1. The job definition MUST be validated against the DeepWork JSON Schema (`job.schema.json`) before dataclass parsing.
2. The parser MUST raise `ParseError` if schema validation fails, including the validation path and message.
3. The JSON Schema MUST require the following top-level fields: `name`, `version`, `summary`, `common_job_info_provided_to_all_steps_at_runtime`, `steps`.
4. The `name` field MUST match the pattern `^[a-z][a-z0-9_]*$` (lowercase letters, numbers, underscores, must start with a letter).
5. The `version` field MUST match the pattern `^\d+\.\d+\.\d+$` (semantic versioning).
6. The `summary` field MUST have a minimum length of 1 and a maximum length of 200 characters.
7. The `common_job_info_provided_to_all_steps_at_runtime` field MUST have a minimum length of 1.
8. The `steps` array MUST contain at least 1 item.
9. The top-level object MUST NOT allow additional properties beyond those defined in the schema.

### JOBS-REQ-002.3: Step Definition

1. Each step MUST have the following required fields: `id`, `name`, `description`, `instructions_file`, `outputs`, `reviews`.
2. The step `id` MUST match the pattern `^[a-z][a-z0-9_]*$`.
3. The `instructions_file` field MUST be a non-empty string specifying a path relative to the job directory.
4. The `outputs` field MUST be an object mapping output names to output specifications.
5. The `reviews` field MUST be an array (MAY be empty).
6. Steps MAY have optional fields: `inputs`, `dependencies`, `hooks`, `stop_hooks`, `exposed`, `hidden`, `agent`.
7. The `exposed` field MUST default to `false`.
8. Steps MUST NOT allow additional properties beyond those defined in the schema.

### JOBS-REQ-002.4: Step Inputs

1. Step inputs MUST be one of two types: user parameter inputs or file inputs.
2. A user parameter input MUST have `name` and `description` fields (both required, non-empty strings).
3. A file input MUST have `file` and `from_step` fields (both required, non-empty strings).
4. A `StepInput` MUST correctly report `is_user_input()` as `True` when both `name` and `description` are set.
5. A `StepInput` MUST correctly report `is_file_input()` as `True` when both `file` and `from_step` are set.

### JOBS-REQ-002.5: Step Outputs

1. Each output specification MUST have `type`, `description`, and `required` fields (all required).
2. The `type` field MUST be one of: `"file"` or `"files"`.
3. The `description` field MUST be a non-empty string.
4. The `required` field MUST be a boolean.

### JOBS-REQ-002.6: Hook Definitions

1. The `hooks` object MUST support three lifecycle event keys: `after_agent`, `before_tool`, `before_prompt`.
2. The `hooks` object MUST NOT allow additional properties beyond these three events.
3. Each hook event MUST contain an array of hook actions.
4. Each hook action MUST be exactly one of: `prompt` (inline text), `prompt_file` (path to file), or `script` (path to shell script).
5. The deprecated `stop_hooks` field MUST be migrated to `hooks.after_agent` during parsing.
6. When both `stop_hooks` and `hooks.after_agent` are present, the `stop_hooks` entries MUST be appended to the existing `after_agent` hooks.
7. The `HookAction` class MUST provide `is_prompt()`, `is_prompt_file()`, and `is_script()` predicate methods.

### JOBS-REQ-002.7: Review Definitions

1. Each review MUST have `run_each` and `quality_criteria` fields (both required).
2. The `run_each` field MUST be a non-empty string: either `"step"` or the name of a specific output.
3. The `quality_criteria` field MUST be an object mapping criterion names to criterion questions (both non-empty strings).
4. The `quality_criteria` object MUST contain at least 1 property.
5. Reviews MAY have an optional `additional_review_guidance` string field.

### JOBS-REQ-002.8: Workflow Definitions

1. Each workflow MUST have `name`, `summary`, and `steps` fields (all required).
2. The workflow `name` MUST match the pattern `^[a-z][a-z0-9_]*$`.
3. The workflow `summary` MUST be a non-empty string with a maximum length of 200 characters.
4. The workflow `steps` array MUST contain at least 1 item.
5. Each workflow step entry MUST be either a step ID string (sequential execution) or an array of step ID strings (concurrent execution).
6. When a step entry is a string, it SHALL be parsed as a `WorkflowStepEntry` with `is_concurrent=False`.
7. When a step entry is a list, it SHALL be parsed as a `WorkflowStepEntry` with `is_concurrent=True`.

### JOBS-REQ-002.9: Semantic Validation - Dependencies

1. The parser MUST validate that all step dependencies reference existing step IDs. A `ParseError` MUST be raised for any dependency referencing a non-existent step.
2. The parser MUST detect circular dependencies using topological sort and raise `ParseError` if a cycle is found.

### JOBS-REQ-002.10: Semantic Validation - File Inputs

1. For every file input, the `from_step` MUST reference an existing step. A `ParseError` MUST be raised otherwise.
2. For every file input, the `from_step` MUST be listed in the consuming step's `dependencies` array. A `ParseError` MUST be raised otherwise.

### JOBS-REQ-002.11: Semantic Validation - Reviews

1. For every review, if `run_each` is not `"step"`, it MUST match the name of a declared output on that step. A `ParseError` MUST be raised otherwise, listing the valid values.

### JOBS-REQ-002.12: Semantic Validation - Workflows

1. The parser MUST reject duplicate workflow names within the same job.
2. The parser MUST reject workflow step references to non-existent step IDs.
3. The parser MUST reject duplicate step IDs within a single workflow.

### JOBS-REQ-002.13: Orphaned Step Detection

1. After validation, the parser MUST identify steps not included in any workflow.
2. Orphaned steps MUST be logged as warnings.
3. Orphaned step detection MUST return the list of orphaned step IDs.

### JOBS-REQ-002.14: JobDefinition Navigation Methods

1. `get_step(step_id)` MUST return the Step if found, or `None` otherwise.
2. `get_workflow_for_step(step_id)` MUST return the Workflow containing the step, or `None` if standalone.
3. `get_next_step_in_workflow(step_id)` MUST return the next step ID in sequence, or `None` if last.
4. `get_prev_step_in_workflow(step_id)` MUST return the previous step ID in sequence, or `None` if first.
5. `get_step_position_in_workflow(step_id)` MUST return a 1-based `(position, total)` tuple, or `None`.
6. `get_step_entry_position_in_workflow(step_id)` MUST return `(1-based entry position, total entries, WorkflowStepEntry)`, or `None`.
7. `get_concurrent_step_info(step_id)` MUST return `(1-based position in group, total in group)` if the step is in a concurrent group, or `None` otherwise.
