# JOBS-REQ-003: Workflow Session Management

## Overview

The StateManager manages workflow session state with support for stack-based nesting, filesystem persistence, and async-safe operations. Sessions track the progress of workflow execution including step status, outputs, quality attempts, and timing. All state is persisted per Claude Code session as JSON files in `.deepwork/tmp/sessions/<platform>/session-<id>/` for transparency, recovery, and crash resilience.

## Requirements

### JOBS-REQ-003.1: StateManager Initialization

1. The StateManager MUST accept a `project_root` Path parameter.
2. The StateManager MUST accept a `platform` string parameter for organizing state by platform (e.g., 'claude', 'gemini').
3. The StateManager MUST store session files in `{project_root}/.deepwork/tmp/sessions/{platform}/`.
4. The StateManager MUST hold an `asyncio.Lock` for concurrent access safety.

### JOBS-REQ-003.2: Session-Scoped Storage

1. Session IDs MUST be provided by the caller (e.g., from Claude Code's session context), not generated internally.
2. Each session's state MUST be stored in its own directory: `session-{session_id}/`.
3. The main workflow stack MUST be stored in `state.json` within the session directory.
4. Sub-agent workflow stacks MUST be stored in `agent_{agent_id}.json` within the session directory.

### JOBS-REQ-003.3: Session Creation

1. `create_session()` MUST be an async method.
2. `create_session()` MUST acquire the async lock before modifying state.
3. `create_session()` MUST accept a `session_id` parameter (str) as the storage key.
4. `create_session()` MUST accept an optional `agent_id` parameter for sub-agent scoped state.
5. The created session MUST have `status: "active"`.
6. The created session MUST have `current_entry_index: 0`.
7. The created session MUST record the `started_at` timestamp in UTC ISO format.
8. `create_session()` MUST persist the session by appending to the workflow stack on disk.
9. The returned `WorkflowSession` MUST contain all provided parameters (session_id, job_name, workflow_name, goal, instance_id, first_step_id).

### JOBS-REQ-003.4: State Persistence

1. State MUST be persisted to `{session_dir}/state.json` for the main stack, or `{session_dir}/agent_{agent_id}.json` for sub-agent stacks.
2. State files MUST be JSON-formatted with 2-space indentation.
3. State files MUST contain a `workflow_stack` array of serialized WorkflowSession objects.
4. Writes MUST be atomic: content MUST be written to a temporary file in the same directory, then atomically renamed via `os.replace()` to prevent partial reads on crash.
5. If a write fails, the temporary file MUST be cleaned up.
6. There MUST be no in-memory caching — every operation MUST read from and write to disk.

### JOBS-REQ-003.5: Session Resolution

1. `resolve_session()` MUST be a synchronous method that returns the top-of-stack session.
2. `resolve_session()` MUST accept `session_id` (str) and optional `agent_id` (str or None) parameters.
3. `resolve_session()` MUST raise `StateError` if the state file does not exist.
4. `resolve_session()` MUST raise `StateError` if the state file contains invalid JSON.
5. `resolve_session()` MUST raise `StateError` if the workflow stack is empty.
6. `resolve_session()` MUST return the last (top) entry from the workflow stack.

### JOBS-REQ-003.6: Sub-Agent Isolation

1. When `agent_id` is provided, state operations MUST read from and write to the agent-specific file (`agent_{agent_id}.json`), not the main `state.json`.
2. `get_stack()` with an `agent_id` MUST return the main stack concatenated with the agent's stack, giving sub-agents visibility into parent context.
3. `get_stack()` without an `agent_id` MUST return only the main stack.
4. Sub-agent stacks MUST be fully isolated from each other and from the main stack for mutation operations.

### JOBS-REQ-003.7: Step Progress Tracking

1. `start_step()` MUST create a `StepProgress` entry if one does not exist for the step.
2. `start_step()` MUST update `started_at` to the current UTC ISO timestamp.
3. `start_step()` MUST update the session's `current_step_id`.
4. `start_step()` MUST persist the session after modification.
5. `complete_step()` MUST create a `StepProgress` entry if one does not exist.
6. `complete_step()` MUST set `completed_at` to the current UTC ISO timestamp.
7. `complete_step()` MUST record the outputs and notes on the step progress.
8. `complete_step()` MUST persist the session after modification.

### JOBS-REQ-003.8: Quality Attempt Tracking

1. `record_quality_attempt()` MUST increment the `quality_attempts` counter on the step's progress.
2. `record_quality_attempt()` MUST create a `StepProgress` entry if one does not exist.
3. `record_quality_attempt()` MUST return the updated total attempt count.
4. `record_quality_attempt()` MUST persist the session after modification.

### JOBS-REQ-003.9: Step Advancement

1. `advance_to_step()` MUST update `current_step_id` to the new step ID.
2. `advance_to_step()` MUST update `current_entry_index` to the new entry index.
3. `advance_to_step()` MUST persist the session after modification.

### JOBS-REQ-003.10: Workflow Completion

1. `complete_workflow()` MUST pop the top-of-stack session.
2. `complete_workflow()` MUST write the updated stack (with the session removed) to disk.
3. `complete_workflow()` MUST return the new top-of-stack session, or `None` if the stack is empty.

### JOBS-REQ-003.11: Workflow Abortion

1. `abort_workflow()` MUST pop the top-of-stack session.
2. `abort_workflow()` MUST write the updated stack (with the session removed) to disk.
3. `abort_workflow()` MUST return a tuple of (aborted session, new active session or None).
4. The aborted session object MUST have `status` set to `"aborted"` and `abort_reason` set to the provided explanation.

### JOBS-REQ-003.12: Workflow Stack (Nesting)

1. Starting a new workflow while one is active MUST push the new session onto the stack (nesting).
2. The stack MUST maintain ordering from bottom (oldest) to top (newest/active).
3. `get_stack()` MUST return a list of `StackEntry` objects with `workflow` (formatted as `"job_name/workflow_name"`) and `step` (current step ID).
4. `get_stack_depth()` MUST return the number of sessions on the stack.

### JOBS-REQ-003.13: Output Aggregation

1. `get_all_outputs()` MUST merge outputs from all completed steps in the targeted session.
2. Later steps' outputs MUST overwrite earlier steps' outputs when keys conflict.

### JOBS-REQ-003.14: Step Navigation (go_to_step)

1. `go_to_step()` MUST be an async method.
2. `go_to_step()` MUST acquire the async lock before modifying state.
3. `go_to_step()` MUST accept `session_id` (str), `step_id` (str), `entry_index` (int), and `invalidate_step_ids` (list of str) parameters.
4. `go_to_step()` MUST accept an optional `agent_id` parameter (str or None).
5. `go_to_step()` MUST delete `step_progress` entries for all step IDs in `invalidate_step_ids`.
6. `go_to_step()` MUST preserve `step_progress` entries for steps not in `invalidate_step_ids`.
7. `go_to_step()` MUST update `current_step_id` to the provided `step_id`.
8. `go_to_step()` MUST update `current_entry_index` to the provided `entry_index`.
9. `go_to_step()` MUST persist the session after modification.

### JOBS-REQ-003.15: Async Safety

1. All state-modifying operations MUST acquire the `asyncio.Lock` before making changes.
2. The StateManager MUST be safe for concurrent async access within a single event loop.
3. The lock MUST be an `asyncio.Lock` instance (not threading.Lock).

### JOBS-REQ-003.16: WorkflowSession Data Model

1. The `WorkflowSession` model MUST support serialization via `to_dict()` using Pydantic `model_dump()`.
2. The `WorkflowSession` model MUST support deserialization via `from_dict()` using Pydantic `model_validate()`.
3. The `status` field MUST be one of: `"active"`, `"completed"`, `"aborted"`.
4. The `step_progress` field MUST be a dict mapping step IDs to `StepProgress` objects.
5. The `StepProgress` model MUST track: `step_id`, `started_at`, `completed_at`, `outputs`, `notes`, `quality_attempts` (default 0).

### JOBS-REQ-003.17: Crash Resilience

1. State MUST survive MCP server restarts — a new StateManager instance pointed at the same `project_root` and `platform` MUST be able to read state written by a prior instance.
2. State writes MUST be atomic (write-then-rename) so that a crash mid-write does not corrupt the state file.
3. If a state file contains invalid JSON, read operations MUST treat it as an empty stack rather than raising an unhandled exception.
