# JOBS-REQ-010: Status Reporting

## Overview

DeepWork provides a file-based external interface for reporting the current status of jobs and workflow sessions. This allows external tools (UIs, dashboards, monitoring) to read the current state without going through the MCP protocol. Status files are a **stable external interface** — the file format MUST NOT change without versioning.

## Requirements

### JOBS-REQ-010.1: Status Directory Structure

1. Status files MUST be written to `.deepwork/tmp/status/v1/` under the project root.
2. The job manifest MUST be written to `.deepwork/tmp/status/v1/job_manifest.yml`.
3. Per-session status files MUST be written to `.deepwork/tmp/status/v1/sessions/<session_id>.yml`.
4. The status directory structure MUST be versioned (currently `v1`) to allow future format changes.

### JOBS-REQ-010.2: Job Manifest

1. `job_manifest.yml` MUST contain a `jobs` array of all available job definitions.
2. Each job entry MUST include `name`, `display_name`, `summary`, and `workflows`.
3. Each workflow entry MUST include `name`, `display_name`, `summary`, and `steps`.
4. Each step entry MUST include `name` and `display_name`.
5. Jobs MUST be sorted alphabetically by `name`.
6. Workflows within each job MUST be sorted alphabetically by `name`.

### JOBS-REQ-010.3: Job Manifest Write Triggers

1. The manifest MUST be written at MCP server startup.
2. The manifest MUST be written when `get_workflows` is called.

### JOBS-REQ-010.4: Display Name Derivation

1. `display_name` MUST be derived from the API name by replacing underscores and hyphens with spaces, then title-casing the result.
2. An empty API name MUST produce an empty display name.

### JOBS-REQ-010.5: Session Status Format

1. Each session status file MUST include `session_id`, `last_updated_at`, `active_workflow`, and `workflows`.
2. `active_workflow` MUST be the `workflow_instance_id` of the top-of-stack workflow on the main stack, or `null` if no active workflow.
3. `last_updated_at` MUST be an ISO 8601 timestamp in UTC.
4. `workflows` MUST be an array of all workflow instances (active, completed, and aborted) for the session.
5. Each workflow entry MUST include `workflow_instance_id`, `job_name`, `status`, `workflow` (definition snapshot), `agent_id`, and `steps` (ordered history).

### JOBS-REQ-010.6: Session Status Write Triggers

1. Session status MUST be written when `start_workflow` is called.
2. Session status MUST be written when `finished_step` is called (for all result statuses: needs_work, next_step, workflow_complete).
3. Session status MUST be written when `go_to_step` is called.
4. Session status MUST be written when `abort_workflow` is called.

### JOBS-REQ-010.7: Workflow Instance ID

1. Each WorkflowSession MUST have a `workflow_instance_id` field.
2. `workflow_instance_id` MUST be generated as `uuid4().hex` (32 hex characters).
3. `workflow_instance_id` MUST be generated via a default factory so existing state files without the field are backward-compatible.
4. `workflow_instance_id` MUST be unique across all workflow instances.

### JOBS-REQ-010.8: Step History

1. Each WorkflowSession MUST maintain a `step_history` list of `StepHistoryEntry` objects.
2. `start_step()` MUST append a new `StepHistoryEntry` with `step_id` and `started_at`.
3. `complete_step()` MUST update the last matching `StepHistoryEntry`'s `finished_at`.
4. `go_to_step()` followed by `start_step()` MUST create a new history entry, resulting in the same step appearing multiple times in history.
5. Step history entries MUST NOT be cleared by `go_to_step()` (only `step_progress` is cleared).

### JOBS-REQ-010.9: Sub-Workflow Instance Tracking

1. `StepProgress` MUST have a `sub_workflow_instance_ids` list field.
2. `StepHistoryEntry` MUST have a `sub_workflow_instance_ids` list field.
3. When a nested workflow is started (parent exists on same stack), the child's `workflow_instance_id` MUST be appended to the parent's current step's `sub_workflow_instance_ids` in both `step_progress` and `step_history`.
4. When a cross-agent sub-workflow is started (agent_id set, parent on main stack), the child's `workflow_instance_id` MUST also be recorded on the main stack parent's current step.

### JOBS-REQ-010.10: Completed/Aborted Workflow Preservation

1. State files MUST support a `completed_workflows` array alongside `workflow_stack`.
2. `complete_workflow()` MUST move the completed session from `workflow_stack` to `completed_workflows`.
3. `abort_workflow()` MUST move the aborted session from `workflow_stack` to `completed_workflows`.
4. `_write_stack()` MUST preserve existing `completed_workflows` when the parameter is not explicitly provided.
5. Multiple completed/aborted workflows MUST accumulate in the `completed_workflows` array.

### JOBS-REQ-010.11: Session Data Retrieval

1. `get_all_session_data()` MUST scan the session directory for `state.json` and `agent_*.json` files.
2. `get_all_session_data()` MUST return a dict mapping agent_id (None for main) to (active_stack, completed_workflows) tuples.
3. `get_all_session_data()` MUST return an empty dict for non-existent sessions.

### JOBS-REQ-010.12: Fire-and-Forget Semantics

1. Status writing failures MUST be logged as warnings.
2. Status writing failures MUST NOT cause the MCP tool call to fail.
3. Status writing MUST NOT block or delay the tool response.

### JOBS-REQ-010.13: External Interface Stability

1. The file format of `job_manifest.yml` and `sessions/<session_id>.yml` is a stable external contract.
2. Field additions are permitted (backward-compatible).
3. Field removals, renames, or semantic changes MUST NOT be made without incrementing the version path (e.g., `v2/`).

## Test Coverage

| Requirement | Test File | Test Name |
|-------------|-----------|-----------|
| JOBS-REQ-010.1 | test_status.py | TestWriteManifest::test_creates_manifest_file |
| JOBS-REQ-010.2 | test_status.py | TestWriteManifest::test_manifest_structure |
| JOBS-REQ-010.3 | test_tools.py | TestStatusWriterIntegration::test_get_workflows_writes_manifest |
| JOBS-REQ-010.4 | test_status.py | TestDeriveDisplayName::* |
| JOBS-REQ-010.5 | test_status.py | TestWriteSessionStatus::test_session_status_structure |
| JOBS-REQ-010.6 | test_tools.py | TestStatusWriterIntegration::test_start_workflow_writes_session_status, test_finished_step_writes_session_status, test_abort_workflow_writes_session_status |
| JOBS-REQ-010.7 | test_state.py | TestWorkflowInstanceId::* |
| JOBS-REQ-010.8 | test_state.py | TestStepHistory::* |
| JOBS-REQ-010.9 | test_state.py | TestSubWorkflowInstanceIds::* |
| JOBS-REQ-010.10 | test_state.py | TestCompletedWorkflows::* |
| JOBS-REQ-010.11 | test_state.py | TestGetAllSessionData::* |
| JOBS-REQ-010.12 | test_tools.py | TestStatusWriterIntegration::test_status_writer_failure_does_not_break_tool |
| JOBS-REQ-010.13 | (Manual review — structural contract) |
