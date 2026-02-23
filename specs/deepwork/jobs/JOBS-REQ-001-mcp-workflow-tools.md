# JOBS-REQ-001: MCP Workflow Tools

## Overview

The DeepWork MCP server exposes four tools to AI agents via the Model Context Protocol (MCP): `get_workflows`, `start_workflow`, `finished_step`, and `abort_workflow`. These tools constitute the primary runtime interface through which agents discover, execute, and manage multi-step workflows. The server is built on FastMCP and all tool responses are serialized as dictionaries via Pydantic `model_dump()`.

## Requirements

### JOBS-REQ-001.1: Server Creation and Configuration

1. The system MUST provide a `create_server()` function that returns a configured `FastMCP` instance.
2. The server MUST accept a `project_root` parameter (Path or str) and resolve it to an absolute path.
3. The server MUST accept an `enable_quality_gate` boolean parameter (default: `True`).
4. The server MUST accept a `quality_gate_timeout` integer parameter in seconds (default: `120`).
5. The server MUST accept a `quality_gate_max_attempts` integer parameter (default: `3`).
6. The server MUST accept an `external_runner` parameter (default: `None`). When set to `"claude"`, the server SHALL use the Claude CLI subprocess for quality reviews. When `None`, the server SHALL use self-review mode.
7. When `enable_quality_gate` is `True` and `external_runner` is `"claude"`, the system MUST create a `QualityGate` with a `ClaudeCLI` instance and `max_inline_files=5`.
8. When `enable_quality_gate` is `True` and `external_runner` is `None`, the system MUST create a `QualityGate` with `cli=None` and `max_inline_files=0`.
9. When `enable_quality_gate` is `False`, the system MUST NOT create a `QualityGate` instance.
10. The server MUST be named `"deepwork"`.
11. The server MUST include instructions text describing the workflow lifecycle (Discover, Start, Execute, Checkpoint, Iterate, Continue, Complete).
12. Every tool call MUST be logged with the tool name and current stack state.

### JOBS-REQ-001.2: get_workflows Tool

1. The `get_workflows` tool MUST be registered as a synchronous MCP tool.
2. The tool MUST accept no parameters.
3. The tool MUST return a dictionary with a `jobs` key containing a list of job info objects.
4. Each job info object MUST contain `name`, `summary`, and `workflows` fields.
5. Each workflow info object MUST contain `name` and `summary` fields.
6. The tool MUST also return an `errors` key containing a list of job load error objects for any jobs that failed to parse.
7. Each job load error object MUST contain `job_name`, `job_dir`, and `error` fields.
8. The tool MUST load jobs from all configured job folders (see JOBS-REQ-008).

### JOBS-REQ-001.3: start_workflow Tool

1. The `start_workflow` tool MUST be registered as an asynchronous MCP tool.
2. The tool MUST require the following parameters: `goal` (str), `job_name` (str), `workflow_name` (str).
3. The tool MUST accept an optional `instance_id` parameter (str or None, default: None).
4. The tool MUST raise `ToolError` if the specified `job_name` does not exist.
5. The tool MUST raise `ToolError` if the specified `workflow_name` does not match any workflow in the job, UNLESS the job has exactly one workflow, in which case that workflow SHALL be auto-selected regardless of the name provided.
6. The tool MUST raise `ToolError` if a job has multiple workflows and the specified name does not match any of them. The error message MUST list the available workflow names.
7. The tool MUST raise `ToolError` if the selected workflow has no steps.
8. The tool MUST create a new workflow session via the StateManager.
9. The tool MUST mark the first step as started.
10. The tool MUST read the instruction file for the first step and include its content in the response.
11. The response MUST contain a `begin_step` object with: `session_id`, `step_id`, `job_dir`, `step_expected_outputs`, `step_reviews`, `step_instructions`, and `common_job_info`.
12. The response MUST contain a `stack` field reflecting the current workflow stack after starting.
13. Each expected output in `step_expected_outputs` MUST include `name`, `type`, `description`, `required`, and `syntax_for_finished_step_tool` fields.
14. The `syntax_for_finished_step_tool` MUST be `"filepath"` for `type: file` outputs and `"array of filepaths for all individual files"` for `type: files` outputs.

### JOBS-REQ-001.4: finished_step Tool

1. The `finished_step` tool MUST be registered as an asynchronous MCP tool.
2. The tool MUST require an `outputs` parameter: a dict mapping output names to file path(s).
3. The tool MUST accept optional parameters: `notes` (str), `quality_review_override_reason` (str), `session_id` (str).
4. The tool MUST raise `StateError` if no active workflow session exists and no `session_id` is provided.
5. When `session_id` is provided, the tool MUST target the session with that ID rather than the top-of-stack session.
6. The tool MUST validate submitted outputs against the current step's declared output specifications (see JOBS-REQ-001.5).
7. The tool MUST return a response with a `status` field that is one of: `"needs_work"`, `"next_step"`, or `"workflow_complete"`.

#### Quality Gate Behavior

8. If a quality gate is configured, the step has reviews, and `quality_review_override_reason` is NOT provided, the tool MUST invoke quality gate evaluation.
9. If `quality_review_override_reason` IS provided, the tool MUST skip quality gate evaluation entirely.
10. In self-review mode (`external_runner=None`): the tool MUST write review instructions to `.deepwork/tmp/quality_review_{session_id}_{step_id}.md` and return `status: "needs_work"` with instructions for the agent to spawn a subagent for self-review.
11. In external runner mode (`external_runner="claude"`): the tool MUST record a quality attempt via the StateManager before invoking the quality gate.
12. In external runner mode, if the quality gate returns failed reviews and the attempt count is below `max_quality_attempts`, the tool MUST return `status: "needs_work"` with combined feedback from all failed reviews.
13. In external runner mode, if the quality gate returns failed reviews and the attempt count has reached `max_quality_attempts`, the tool MUST raise `ToolError` with a message indicating the maximum attempts were exceeded and including the feedback.
14. In external runner mode, if all reviews pass, the tool MUST proceed to step completion.

#### Step Advancement

15. After successful quality gate (or when no gate applies), the tool MUST mark the current step as completed in the StateManager with outputs and notes.
16. If no more step entries remain in the workflow, the tool MUST return `status: "workflow_complete"` with a summary message and `all_outputs` merged from all completed steps.
17. If more step entries remain, the tool MUST advance to the next step entry, return `status: "next_step"`, and include a `begin_step` object with the next step's information.
18. For concurrent step entries (entries with multiple step IDs), the tool MUST use the first step ID as the primary step and append a message about concurrent execution using the Task tool.
19. All `finished_step` responses MUST include a `stack` field reflecting the current workflow stack.

### JOBS-REQ-001.5: Output Validation

1. The system MUST reject submitted output keys that do not match any declared output name. The error MUST list the unknown keys and the valid declared names.
2. The system MUST reject submissions missing any required output (outputs where `required: true`). The error MUST list the missing required outputs.
3. Optional outputs (`required: false`) MAY be omitted from the submission without error.
4. For outputs declared as `type: "file"`, the submitted value MUST be a single string. If not, the system MUST raise `ToolError` indicating the type mismatch.
5. For outputs declared as `type: "file"`, the file at the specified path (relative to project root) MUST exist. If not, the system MUST raise `ToolError`.
6. For outputs declared as `type: "files"`, the submitted value MUST be a list. If not, the system MUST raise `ToolError` indicating the type mismatch.
7. For outputs declared as `type: "files"`, each element in the list MUST be a string. If not, the system MUST raise `ToolError`.
8. For outputs declared as `type: "files"`, each file at the specified path (relative to project root) MUST exist. If not, the system MUST raise `ToolError`.

### JOBS-REQ-001.6: abort_workflow Tool

1. The `abort_workflow` tool MUST be registered as an asynchronous MCP tool.
2. The tool MUST require an `explanation` parameter (str).
3. The tool MUST accept an optional `session_id` parameter (str, default: None).
4. The tool MUST raise `StateError` if no active workflow session exists.
5. The tool MUST mark the targeted session as aborted with the provided explanation.
6. The tool MUST remove the aborted session from the stack.
7. The response MUST contain: `aborted_workflow` (formatted as `"job_name/workflow_name"`), `aborted_step`, `explanation`, `stack`, `resumed_workflow` (or None), and `resumed_step` (or None).
8. If a parent workflow exists on the stack after abortion, `resumed_workflow` and `resumed_step` MUST reflect that parent's state.

### JOBS-REQ-001.7: Tool Response Serialization

1. All tool responses MUST be serialized via Pydantic's `model_dump()` method, returning plain dictionaries.
2. The `StepStatus` enum values MUST be: `"needs_work"`, `"next_step"`, `"workflow_complete"`.
