# JOBS-REQ-002: Job Definition Parsing

## Overview

Job definitions are YAML files (`job.yml`) that declare multi-step workflows for AI agents. The parser reads these files, validates them against a JSON Schema, parses them into typed dataclasses, and performs semantic validation. Steps are defined inline within workflows as `WorkflowStep` objects, with shared `step_arguments` defining the input/output contract.

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
3. The JSON Schema MUST require the following top-level fields: `name`, `summary`.
4. The `name` field MUST match the pattern `^[a-z][a-z0-9_]*$`.
5. The `summary` field MUST be a non-empty string.
6. The top-level object MUST support `step_arguments` (array) and `workflows` (object) fields.

### JOBS-REQ-002.3: Step Arguments

1. Each step argument MUST have `name`, `description`, and `type` fields (all required).
2. The `type` field MUST be one of: `"string"` or `"file_path"`.
3. The `name` and `description` fields MUST be non-empty strings.
4. Step arguments MAY have an optional `review` field containing a `ReviewBlock`.
5. Step arguments MAY have an optional `json_schema` field containing a JSON Schema object for output validation.

### JOBS-REQ-002.4: ReviewBlock

1. Each `ReviewBlock` MUST have `strategy` and `instructions` fields (both required).
2. The `strategy` field MUST be one of: `"individual"` or `"matches_together"`.
3. The `instructions` field MUST be a non-empty string.
4. A `ReviewBlock` MAY have an optional `agent` field (dict with string keys/values).
5. A `ReviewBlock` MAY have an optional `additional_context` field (dict with boolean values, e.g., `all_changed_filenames`, `unchanged_matching_files`).

### JOBS-REQ-002.5: WorkflowStep Definition

1. Each `WorkflowStep` MUST have a `name` field (required, non-empty string).
2. Each `WorkflowStep` MUST have exactly one of `instructions` (inline string) or `sub_workflow` (reference to another workflow). A `ParseError` MUST be raised if a step has both or neither.
3. The `instructions` field, when present, MUST be a non-empty string containing the step instructions inline (NOT a file path).
4. Steps MAY have `inputs` and `outputs` dicts mapping step_argument names to `StepInputRef` / `StepOutputRef` objects.
5. Steps MAY have a `process_quality_attributes` dict mapping attribute names to quality statements.

### JOBS-REQ-002.6: StepInputRef and StepOutputRef

1. A `StepInputRef` MUST have an `argument_name` field referencing a declared `step_argument`.
2. A `StepInputRef` MAY have a `required` field (boolean, default: `true`).
3. A `StepOutputRef` MUST have an `argument_name` field referencing a declared `step_argument`.
4. A `StepOutputRef` MAY have a `required` field (boolean, default: `true`).
5. A `StepOutputRef` MAY have a `review` field containing a `ReviewBlock` that overrides or supplements the step_argument-level review.

### JOBS-REQ-002.7: SubWorkflowRef

1. A `SubWorkflowRef` MUST have a `workflow_name` field (required, non-empty string).
2. A `SubWorkflowRef` MAY have a `workflow_job` field. When absent, the reference is to a workflow in the same job.

### JOBS-REQ-002.8: Workflow Definitions

1. Each workflow MUST have `summary` and `steps` fields (both required).
2. The workflow name is the key in the `workflows` dict and MUST match the pattern `^[a-z][a-z0-9_]*$`.
3. The workflow `summary` MUST be a non-empty string.
4. The workflow `steps` array MUST contain at least 1 `WorkflowStep` item (inline, not references).
5. Workflows MAY have an optional `agent` field (non-empty string) for delegating to a sub-agent.
6. Workflows MAY have an optional `common_job_info_provided_to_all_steps_at_runtime` field (string) for shared context.
7. Workflows MAY have an optional `post_workflow_instructions` field (string) returned on workflow completion.

### JOBS-REQ-002.9: Semantic Validation - Argument References

1. All `StepInputRef` and `StepOutputRef` argument names MUST reference existing entries in `step_arguments`. A `ParseError` MUST be raised for any reference to a non-existent step_argument.

### JOBS-REQ-002.10: Semantic Validation - Sub-Workflow References

1. For same-job `SubWorkflowRef` (no `workflow_job`), the `workflow_name` MUST reference an existing workflow in the same job. A `ParseError` MUST be raised otherwise.
2. Cross-job `SubWorkflowRef` (with `workflow_job`) SHALL be validated at runtime, not parse time.

### JOBS-REQ-002.11: Semantic Validation - Step Name Uniqueness

1. Step names MUST be unique within each workflow. A `ParseError` MUST be raised for duplicate step names.

### JOBS-REQ-002.12: JobDefinition Navigation Methods

1. `get_argument(name)` MUST return the `StepArgument` if found, or `None` otherwise.
2. `get_workflow(name)` MUST return the `Workflow` if found, or `None` otherwise.

### JOBS-REQ-002.13: Workflow Navigation Methods

1. `Workflow.get_step(step_name)` MUST return the `WorkflowStep` if found, or `None` otherwise.
2. `Workflow.get_step_index(step_name)` MUST return the 0-based index of the step, or `None` if not found.
3. `Workflow.step_names` MUST return the ordered list of step names.
