# JOBS-REQ-004: Quality Review System

## Overview

The quality review system evaluates step outputs against defined quality criteria using the DeepWork Reviews infrastructure. It builds dynamic `ReviewRule` objects from step output reviews and `process_requirements`, validates outputs against JSON schemas, and produces review instructions through the standard review pipeline (`write_instruction_files`, `format_for_claude`). There is no subprocess invocation — all reviews are handled via the Reviews pipeline.

## Requirements

### JOBS-REQ-004.1: Entry Point

1. `run_quality_gate()` MUST accept: `step` (WorkflowStep), `job` (JobDefinition), `workflow` (Workflow), `outputs` (dict), `input_values` (dict), `work_summary` (str or None), `project_root` (Path), and `platform` (str, default `"claude"`).
2. `run_quality_gate()` MUST return `None` when no reviews are needed (all pass or no review rules match).
3. `run_quality_gate()` MUST return a string containing review guidance when reviews are required.

### JOBS-REQ-004.2: JSON Schema Validation

1. `validate_json_schemas()` MUST check all `file_path` type outputs that have a `json_schema` defined on their `StepArgument`.
2. For each such output, the file content MUST be parsed as JSON and validated against the schema.
3. If JSON parsing fails, the error MUST be included in the returned error list.
4. If schema validation fails, the error MUST be included in the returned error list.
5. Files that do not exist MUST be skipped (not treated as errors by this function).
6. `run_quality_gate()` MUST run JSON schema validation before building review rules. If schema errors exist, it MUST return an error message listing them without proceeding to reviews.

### JOBS-REQ-004.3: Dynamic Review Rule Construction

1. `build_dynamic_review_rules()` MUST create `ReviewRule` objects from step output `ReviewBlock` definitions.
2. For each output with a review (on the `StepOutputRef` or inherited from the `StepArgument`), a `ReviewRule` MUST be created with the output files as `include_patterns`.
3. If an output has reviews at both the `StepOutputRef` level and the `StepArgument` level, both MUST generate separate rules (suffixed `_arg` for the argument-level rule).
4. Each rule's `instructions` MUST be prefixed with a preamble containing workflow `common_job_info` and input context (if available).
5. Outputs with no review blocks MUST be skipped.
6. Outputs with `None` values MUST be skipped.
7. Only `file_path` type arguments with actual file paths generate `ReviewRule` objects.

### JOBS-REQ-004.4: Process Requirements

1. When a step has `process_requirements` and a `work_summary` is provided, `build_dynamic_review_rules()` MUST create a `ReviewRule` with strategy `"matches_together"`.
2. The rule's instructions MUST include the quality criteria list, the `work_summary`, and output context.
3. The rule MUST match all `file_path` output files so the reviewer can read them if needed.
4. If there are no `file_path` output files, the process quality rule MUST NOT be created.

### JOBS-REQ-004.5: Review Pipeline Integration

1. `run_quality_gate()` MUST load `.deepreview` rules via `load_all_rules()`.
2. `.deepreview` rules MUST be matched against output file paths via `match_files_to_rules()`.
3. Dynamic rules (from step reviews) MUST also be matched via `match_files_to_rules()`.
4. All matched tasks (dynamic + `.deepreview`) MUST be combined.
5. Combined tasks MUST be passed to `write_instruction_files()`, which honors `.passed` marker files.
6. If `write_instruction_files()` returns no task files (all already passed), `run_quality_gate()` MUST return `None`.
7. Remaining task files MUST be formatted via `format_for_claude()`.

### JOBS-REQ-004.6: Review Guidance Output

1. The review guidance MUST include the formatted review output from `format_for_claude()`.
2. The guidance MUST instruct the agent to launch review tasks as parallel Task agents.
3. The guidance MUST explain how to handle failing reviews (fix issues or call `mark_review_as_passed`).
4. The guidance MUST instruct the agent to call `finished_step` again after reviews complete.

### JOBS-REQ-004.7: Input Context Building

1. `_build_input_context()` MUST produce a markdown section describing step inputs and their values.
2. For `file_path` inputs, values MUST be shown as `@path` references.
3. For `string` inputs, values MUST be shown inline.
4. Inputs with no value MUST be shown as "not available".
5. If the step has no inputs, an empty string MUST be returned.
