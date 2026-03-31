# JOBS-REQ-001: MCP Workflow Tools

## Overview

The DeepWork MCP server exposes workflow tools to AI agents via the Model Context Protocol (MCP): `get_workflows`, `start_workflow`, `finished_step`, `abort_workflow`, and `go_to_step`. These tools constitute the primary runtime interface through which agents discover, execute, and manage multi-step workflows. The server also exposes review tools (`get_review_instructions`, `get_configured_reviews`, `mark_review_as_passed`). Built on FastMCP; all tool responses serialized as dictionaries via Pydantic `model_dump()`. At startup, the server detects issues (e.g., malformed job.yml files) via `detect_issues()` and communicates them through dynamic MCP instructions and by appending warnings to tool responses.

## Requirements

### JOBS-REQ-001.1: Server Creation and Configuration

1. The system MUST provide a `create_server()` function that returns a configured `FastMCP` instance.
2. The server MUST accept a `project_root` parameter (Path or str) and resolve it to an absolute path. This value is used as the startup/fallback root.
3. The server MUST accept an optional `platform` parameter (str or None, default: `None`). When `None`, defaults to `"claude"`.
4. The server MUST accept `**_kwargs` for backwards compatibility with removed parameters (`enable_quality_gate`, `quality_gate_timeout`, `quality_gate_max_attempts`, `external_runner`). These MUST be ignored.
5. The server MUST accept an `explicit_path` keyword argument (bool, default: `True`). When `False`, tool handlers MUST resolve the project root dynamically via `RootResolver.get_root()` on each invocation (see JOBS-REQ-011).
5. The server MUST be named `"deepwork"`.
6. The server MUST include instructions text describing the workflow lifecycle.
7. Every tool call MUST be logged with the tool name and current stack state.
8. On startup, the server MUST copy `job.schema.json` from its package-bundled location to `.deepwork/job.schema.json` under the project root. If the copy fails, the server MUST log a warning and continue.
9. On startup, the server MUST write an initial job manifest via `StatusWriter`.

### JOBS-REQ-001.2: get_workflows Tool

1. The `get_workflows` tool MUST be registered as an asynchronous MCP tool.
2. The tool MUST accept no user-visible parameters (FastMCP auto-injects `Context`).
3. The tool MUST return a dictionary with a `jobs` key containing a list of job info objects.
4. Each job info object MUST contain `name`, `summary`, and `workflows` fields.
5. Each workflow info object MUST contain `name`, `summary`, and `how_to_invoke` fields.
6. When a workflow's `agent` field is set, `how_to_invoke` MUST contain instructions for delegating to a sub-agent of the specified type via the Task tool.
7. When a workflow's `agent` field is not set, `how_to_invoke` MUST contain instructions to call `start_workflow` directly.
8. The tool MUST also return an `errors` key containing a list of job load error objects for jobs that failed to parse.
9. Each job load error object MUST contain `job_name`, `job_dir`, and `error` fields.

### JOBS-REQ-001.3: start_workflow Tool

1. The `start_workflow` tool MUST be registered as an asynchronous MCP tool.
2. The tool MUST require: `goal` (str), `job_name` (str), `workflow_name` (str), `session_id` (str).
3. The tool MUST accept optional: `inputs` (dict of step_argument names to values, or None), `agent_id` (str or None).
4. The tool MUST raise `ToolError` if the specified `job_name` does not exist.
5. The tool MUST raise `ToolError` if the specified `workflow_name` does not match any workflow, UNLESS the job has exactly one workflow, in which case it SHALL be auto-selected.
6. The tool MUST raise `ToolError` if the selected workflow has no steps.
7. The tool MUST create a new workflow session via `StateManager`.
8. The tool MUST resolve input values for the first step from provided `inputs` and previous step outputs.
9. The tool MUST mark the first step as started with resolved input values.
10. The response MUST contain a `begin_step` (`ActiveStepInfo`) with: `session_id`, `step_id`, `job_dir`, `step_expected_outputs`, `step_inputs`, `step_instructions`, `common_job_info`.
11. The response MUST contain a `stack` field and an `important_note` field instructing the agent to clarify ambiguous requests.
12. Each expected output MUST include `name`, `type`, `description`, `required`, and `syntax_for_finished_step_tool`.

### JOBS-REQ-001.4: finished_step Tool

1. The `finished_step` tool MUST be registered as an asynchronous MCP tool.
2. The tool MUST require: `outputs` (dict mapping step_argument names to values), `session_id` (str).
3. The tool MUST accept optional: `work_summary` (str or None), `quality_review_override_reason` (str or None), `agent_id` (str or None).
4. The tool MUST raise `ToolError` if no active workflow session exists for the given `session_id`.
5. The tool MUST validate submitted outputs against the current step's declared output refs (see JOBS-REQ-001.5).
6. The tool MUST return a response with `status` of: `"needs_work"`, `"next_step"`, or `"workflow_complete"`.

#### Quality Gate Behavior

7. If `quality_review_override_reason` is NOT provided, the tool MUST invoke `run_quality_gate()` from `quality_gate.py`.
8. If `quality_review_override_reason` IS provided, the tool MUST skip quality gate evaluation entirely.
9. `run_quality_gate()` returns `None` (no reviews needed) or a string (review feedback). When it returns a string, the tool MUST record a quality attempt and return `status: "needs_work"` with the feedback.
10. When `run_quality_gate()` returns `None`, the tool MUST proceed to step completion.

#### Step Advancement

11. After successful quality gate (or when no gate applies), the tool MUST mark the current step as completed with outputs and work_summary.
12. If no more steps remain, the tool MUST return `status: "workflow_complete"` with `all_outputs` merged from all completed steps and `post_workflow_instructions` (if defined on the workflow).
13. If more steps remain, the tool MUST advance to the next step, resolve its input values, mark it as started, and return `status: "next_step"` with a `begin_step` object.
14. All `finished_step` responses MUST include a `stack` field.

### JOBS-REQ-001.5: Output Validation

1. The system MUST reject submitted output keys that do not match any declared output name.
2. The system MUST reject submissions missing any required output (`required: true` on the `StepOutputRef`).
3. Optional outputs (`required: false`) MAY be omitted without error.
4. For outputs with `StepArgument.type == "file_path"`: the value MUST be a string or list of strings. Each path (relative to project root) MUST exist. `ToolError` MUST be raised on type mismatch or missing file.
5. For outputs with `StepArgument.type == "string"`: the value MUST be a string. `ToolError` MUST be raised on type mismatch.

### JOBS-REQ-001.6: abort_workflow Tool

1. The `abort_workflow` tool MUST be registered as an asynchronous MCP tool.
2. The tool MUST require `explanation` (str) and `session_id` (str).
3. The tool MUST accept optional `agent_id` (str or None).
4. The tool MUST raise `StateError` if no active workflow session exists.
5. The tool MUST mark the session as aborted and remove it from the stack.
6. The response MUST contain: `aborted_workflow`, `aborted_step`, `explanation`, `stack`, `resumed_workflow` (or None), `resumed_step` (or None).

### JOBS-REQ-001.7: go_to_step Tool

1. The `go_to_step` tool MUST be registered as an asynchronous MCP tool.
2. The tool MUST require `step_id` (str) and `session_id` (str). Optional: `agent_id`.
3. The tool MUST raise `StateError` if no active workflow session exists.
4. The tool MUST raise `ToolError` if `step_id` does not exist in the workflow, listing available step names.
5. The tool MUST raise `ToolError` if the target step index is greater than the current step index (forward navigation). The error MUST direct the agent to use `finished_step`.
6. The tool MUST allow navigating to the current step (same index) to restart it.
7. The tool MUST collect all step names from the target index through the end of the workflow as invalidated steps.
8. The tool MUST clear session tracking state for all invalidated steps via `StateManager`. Files on disk MUST NOT be deleted.
9. The tool MUST mark the target step as started with resolved input values.
10. The response MUST contain `begin_step`, `invalidated_steps`, and `stack`.

### JOBS-REQ-001.8: Tool Response Serialization

1. All tool responses MUST be serialized via Pydantic's `model_dump()` method, returning plain dictionaries.
2. The `StepStatus` enum values MUST be: `"needs_work"`, `"next_step"`, `"workflow_complete"`.

### JOBS-REQ-001.9: Issue Detection

1. The system MUST provide a `detect_issues()` function in `deepwork.jobs.issues` that accepts a `project_root` (Path) and returns a list of `Issue` objects.
2. `detect_issues()` MUST detect job.yml files that fail schema validation or parsing by calling `load_all_jobs()`.
3. Each `Issue` MUST have: `severity` (str), `job_name` (str), `job_dir` (str), `message` (str), `suggestion` (str).
4. The `suggestion` for schema errors MUST reference `/deepwork repair` as a remediation path.
5. `detect_issues()` MUST return an empty list when all jobs parse successfully.
6. `detect_issues()` MUST be importable independently of the MCP layer so other agent implementations can use it.

### JOBS-REQ-001.10: Startup Instructions

1. The MCP server's `instructions` field MUST be built dynamically at startup based on `detect_issues()` results.
2. The instructions MUST always include static server instructions describing the workflow lifecycle and session identity.
3. When issues are detected, the instructions MUST include an `IMPORTANT: ISSUE DETECTED` section with the formatted issue details.
4. When no issues are detected, the instructions MUST include an `Available Workflows` section listing all discovered jobs with summaries.
5. When issues are detected, the `Available Workflows` section MUST NOT be included.
6. The total instructions string MUST NOT exceed 2048 bytes, to avoid truncation by MCP clients.
7. Dynamic content (issues or workflow list) MUST appear before static server instructions, so it survives truncation.

### JOBS-REQ-001.11: Issue Appending to Tool Responses

1. When issues are detected at startup, all workflow tool responses (`get_workflows`, `start_workflow`, `finished_step`, `abort_workflow`, `go_to_step`) MUST include an `issue_detected` key with the formatted issue warning.
2. When no issues are detected, tool responses MUST NOT include the `issue_detected` key.
3. The `get_workflows` tool MUST use `detect_issues()` to populate its `errors` field, replacing inline error enhancement.
