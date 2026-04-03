# JOBS-REQ-013: Session Job Tools

## Overview

DeepWork supports transient job definitions scoped to a session via two MCP tools: `register_session_job` and `get_session_job`. These enable workflows (like DeepPlan) to dynamically create executable job definitions during a session that can then be started with `start_workflow`. Session jobs are stored on disk under the session directory and survive MCP server restarts.

## Requirements

### JOBS-REQ-013.1: Job Registration

1. The `register_session_job` tool MUST accept `job_name`, `job_definition_yaml`, and `session_id` as required parameters.
2. The `job_name` parameter MUST be validated against the pattern `^[a-z][a-z0-9_]*$`.
3. Invalid job names MUST result in a `ToolError` with a descriptive message.
4. The `job_definition_yaml` MUST be validated as syntactically valid YAML before writing.
5. Invalid YAML syntax MUST result in a `ToolError`.
6. After writing, the job definition MUST be validated against the job schema via `parse_job_definition()`.
7. Schema validation failures MUST result in a `ToolError` that includes the validation error details.
8. The job file MUST be preserved on disk even when schema validation fails, so the agent can inspect it.
9. On success, the tool MUST return a dict with `status`, `job_name`, `job_dir`, and `message` fields.
10. Calling `register_session_job` multiple times with the same `job_name` and `session_id` MUST overwrite the previous definition.

### JOBS-REQ-013.2: Job Storage

1. Session jobs MUST be stored at `.deepwork/tmp/sessions/<platform>/session-<session_id>/jobs/<job_name>/job.yml`.
2. The storage directory MUST be created automatically if it does not exist.
3. Session jobs MUST survive MCP server restarts (stored on disk, not in memory).

### JOBS-REQ-013.3: Job Retrieval

1. The `get_session_job` tool MUST accept `job_name` and `session_id` as required parameters.
2. The tool MUST return the full YAML content of the registered job definition.
3. If no job with the given name exists for the session, the tool MUST raise a `ToolError`.
4. The return value MUST include `job_name` and `job_definition_yaml` fields.

### JOBS-REQ-013.4: Session Job Discovery

1. `start_workflow` MUST check session-scoped job directories before standard job discovery when a `session_id` is provided.
2. Session jobs MUST take priority over standard and project-local jobs with the same name.
3. `finished_step` and `go_to_step` MUST also resolve jobs from session directories when operating on a session job workflow.
4. A session job registered under one `session_id` MUST NOT be discoverable by `start_workflow` with a different `session_id`.

### JOBS-REQ-013.5: Session ID Requirement

1. Both `register_session_job` and `get_session_job` MUST require `session_id`.
2. When `session_id` is not provided, the tools MUST return an error dict (not raise an exception) with an `error` field explaining the requirement.
