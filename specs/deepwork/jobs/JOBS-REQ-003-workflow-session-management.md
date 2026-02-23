# JOBS-REQ-003: Workflow Session Management

## Overview

The StateManager manages workflow session state with support for stack-based nesting, filesystem persistence, and async-safe operations. Sessions track the progress of workflow execution including step status, outputs, quality attempts, and timing. All state is persisted as JSON files in `.deepwork/tmp/` for transparency and recovery.

## Requirements

### JOBS-REQ-003.1: StateManager Initialization

1. The StateManager MUST accept a `project_root` Path parameter.
2. The StateManager MUST store session files in `{project_root}/.deepwork/tmp/`.
3. The StateManager MUST maintain an in-memory session stack (`_session_stack`) as a list.
4. The StateManager MUST hold an `asyncio.Lock` for concurrent access safety.

### JOBS-REQ-003.2: Session ID Generation

1. Session IDs MUST be generated from UUID4 values.
2. Session IDs MUST be exactly 8 characters long (the first 8 characters of the UUID4 string representation).
3. Each generated session ID MUST be unique within the server's lifetime.

### JOBS-REQ-003.3: Session Creation

1. `create_session()` MUST be an async method.
2. `create_session()` MUST acquire the async lock before modifying state.
3. `create_session()` MUST ensure the sessions directory exists.
4. `create_session()` MUST generate a unique session ID.
5. The created session MUST have `status: "active"`.
6. The created session MUST have `current_entry_index: 0`.
7. The created session MUST record the `started_at` timestamp in UTC ISO format.
8. `create_session()` MUST persist the session to a JSON file.
9. `create_session()` MUST append the session to the in-memory stack.
10. The returned `WorkflowSession` MUST contain all provided parameters (job_name, workflow_name, goal, instance_id, first_step_id).

### JOBS-REQ-003.4: Session Persistence

1. Session state MUST be persisted to `{sessions_dir}/session_{session_id}.json`.
2. Session files MUST be JSON-formatted with 2-space indentation.
3. Session files MUST be written using `aiofiles` for async I/O.
4. The `_save_session_unlocked()` method MUST be called only when the lock is already held.
5. The `_save_session()` method MUST acquire the lock before saving.

### JOBS-REQ-003.5: Session Loading

1. `load_session()` MUST be an async method.
2. `load_session()` MUST raise `StateError` if the session file does not exist.
3. `load_session()` MUST deserialize the JSON file into a `WorkflowSession` using `from_dict()`.
4. When the in-memory stack is non-empty, `load_session()` MUST replace the top-of-stack with the loaded session.
5. When the in-memory stack is empty, `load_session()` MUST push the loaded session onto the stack.

### JOBS-REQ-003.6: Active Session Access

1. `get_active_session()` MUST return the top-of-stack session, or `None` if the stack is empty.
2. `require_active_session()` MUST return the top-of-stack session.
3. `require_active_session()` MUST raise `StateError` with an instructive message if the stack is empty.

### JOBS-REQ-003.7: Session ID Routing

1. `_resolve_session(session_id)` MUST search the entire stack for a session matching the provided `session_id`.
2. If `session_id` is provided but not found in the stack, `_resolve_session()` MUST raise `StateError`.
3. If `session_id` is `None`, `_resolve_session()` MUST fall back to `require_active_session()` (top-of-stack).
4. All state-modifying methods that accept `session_id` (start_step, complete_step, record_quality_attempt, advance_to_step, complete_workflow, abort_workflow) MUST use `_resolve_session()` for session lookup.

### JOBS-REQ-003.8: Step Progress Tracking

1. `start_step()` MUST create a `StepProgress` entry if one does not exist for the step.
2. `start_step()` MUST update `started_at` to the current UTC ISO timestamp.
3. `start_step()` MUST update the session's `current_step_id`.
4. `start_step()` MUST persist the session after modification.
5. `complete_step()` MUST create a `StepProgress` entry if one does not exist.
6. `complete_step()` MUST set `completed_at` to the current UTC ISO timestamp.
7. `complete_step()` MUST record the outputs and notes on the step progress.
8. `complete_step()` MUST persist the session after modification.

### JOBS-REQ-003.9: Quality Attempt Tracking

1. `record_quality_attempt()` MUST increment the `quality_attempts` counter on the step's progress.
2. `record_quality_attempt()` MUST create a `StepProgress` entry if one does not exist.
3. `record_quality_attempt()` MUST return the updated total attempt count.
4. `record_quality_attempt()` MUST persist the session after modification.

### JOBS-REQ-003.10: Step Advancement

1. `advance_to_step()` MUST update `current_step_id` to the new step ID.
2. `advance_to_step()` MUST update `current_entry_index` to the new entry index.
3. `advance_to_step()` MUST persist the session after modification.

### JOBS-REQ-003.11: Workflow Completion

1. `complete_workflow()` MUST set `completed_at` to the current UTC ISO timestamp.
2. `complete_workflow()` MUST set `status` to `"completed"`.
3. `complete_workflow()` MUST persist the session to its JSON file.
4. `complete_workflow()` MUST remove the completed session from the in-memory stack using filter (not pop), to support mid-stack removal.
5. `complete_workflow()` MUST return the new top-of-stack session, or `None` if the stack is empty.

### JOBS-REQ-003.12: Workflow Abortion

1. `abort_workflow()` MUST set `completed_at` to the current UTC ISO timestamp.
2. `abort_workflow()` MUST set `status` to `"aborted"`.
3. `abort_workflow()` MUST set `abort_reason` to the provided explanation.
4. `abort_workflow()` MUST persist the session to its JSON file.
5. `abort_workflow()` MUST remove the aborted session from the in-memory stack using filter (not pop), to support mid-stack removal.
6. `abort_workflow()` MUST return a tuple of (aborted session, new active session or None).

### JOBS-REQ-003.13: Workflow Stack (Nesting)

1. Starting a new workflow while one is active MUST push the new session onto the stack (nesting).
2. The stack MUST maintain ordering from bottom (oldest) to top (newest/active).
3. `get_stack()` MUST return a list of `StackEntry` objects with `workflow` (formatted as `"job_name/workflow_name"`) and `step` (current step ID).
4. `get_stack_depth()` MUST return the number of sessions on the stack.
5. Completing or aborting a workflow MUST remove only that specific session from the stack, not necessarily the top.

### JOBS-REQ-003.14: Output Aggregation

1. `get_all_outputs()` MUST merge outputs from all completed steps in the targeted session.
2. Later steps' outputs MUST overwrite earlier steps' outputs when keys conflict.
3. `get_all_outputs()` MUST accept an optional `session_id` parameter for targeting specific sessions.

### JOBS-REQ-003.15: Session Listing and Querying

1. `list_sessions()` MUST scan all `session_*.json` files in the sessions directory.
2. `list_sessions()` MUST skip corrupted files (invalid JSON, validation errors) without raising.
3. `list_sessions()` MUST return sessions sorted by `started_at` in descending order (most recent first).
4. `find_active_sessions_for_workflow()` MUST filter sessions by job_name, workflow_name, and `status == "active"`.

### JOBS-REQ-003.16: Session Deletion

1. `delete_session()` MUST remove the session file from disk if it exists.
2. `delete_session()` MUST remove the session from the in-memory stack if present.
3. `delete_session()` MUST acquire the lock before modifying state.

### JOBS-REQ-003.17: Async Safety

1. All state-modifying operations MUST acquire the `asyncio.Lock` before making changes.
2. The StateManager MUST be safe for concurrent async access within a single event loop.
3. The lock MUST be an `asyncio.Lock` instance (not threading.Lock).

### JOBS-REQ-003.18: WorkflowSession Data Model

1. The `WorkflowSession` model MUST support serialization via `to_dict()` using Pydantic `model_dump()`.
2. The `WorkflowSession` model MUST support deserialization via `from_dict()` using Pydantic `model_validate()`.
3. The `status` field MUST be one of: `"active"`, `"completed"`, `"aborted"`.
4. The `step_progress` field MUST be a dict mapping step IDs to `StepProgress` objects.
5. The `StepProgress` model MUST track: `step_id`, `started_at`, `completed_at`, `outputs`, `notes`, `quality_attempts` (default 0).
