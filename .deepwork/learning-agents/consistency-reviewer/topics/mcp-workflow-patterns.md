---
name: "MCP Workflow Patterns"
keywords:
  - mcp
  - workflow
  - finished_step
  - start_workflow
  - get_workflows
  - abort_workflow
  - state
  - session
  - nested
  - concurrent
  - outputs
last_updated: "2026-02-18"
---

## MCP Server Overview

DeepWork's MCP server (`src/deepwork/mcp/`) provides four tools that agents use to execute workflows:

1. **`get_workflows`** — Lists all available jobs and their workflows. Auto-discovers from `.deepwork/jobs/` at runtime.
2. **`start_workflow`** — Begins a workflow session. Creates state, generates a branch name, returns first step instructions.
3. **`finished_step`** — Reports step completion with outputs. Runs quality gates, then returns next step or workflow completion.
4. **`abort_workflow`** — Cancels the current workflow with an explanation.

## Session and State Model

- State is persisted to `.deepwork/tmp/session_<id>.json` (JSON files for transparency)
- Sessions track: job name, workflow name, goal, current step, step progress, outputs
- Branch naming: `deepwork/<job_name>-<workflow_name>-<instance_or_date>`
- State manager uses an async lock for concurrent access safety

## Output Validation (Critical Consistency Point)

When `finished_step` is called, outputs are validated strictly:

1. **Every submitted key must match a declared output name** — unknown keys are rejected
2. **Every required output must be provided** — missing required outputs are rejected
3. **Type enforcement**: `type: file` requires a single string path; `type: files` requires a list of strings
4. **File existence**: Every referenced file must exist on disk at the project-relative path

**Common mistake to watch for**: A PR that adds a new output to a step's `job.yml` declaration but doesn't ensure the agent actually creates that file before calling `finished_step`. This will cause a runtime error.

**Another gotcha**: The `files` type cannot be an empty list if the output is `required: true`. If a step declares `scripts` as `type: files, required: false`, the agent can omit it entirely, but if it's `required: true`, it must provide at least one file path.

## Nested Workflows

Workflows can nest — calling `start_workflow` during an active workflow pushes onto a stack:

- All tool responses include a `stack` field showing the current depth
- `complete_workflow` and `abort_workflow` pop from the stack
- The `session_id` parameter on `finished_step` and `abort_workflow` allows targeting a specific session in the stack

**Consistency check**: Any change to state management must preserve stack integrity. The stack uses list filtering (not index-based pop) for mid-stack removal safety.

## Concurrent Steps

Workflow steps can be concurrent (defined as arrays in `job.yml`):

```yaml
steps:
  - step_a
  - [step_b, step_c]  # These run in parallel
  - step_d
```

When the server encounters a concurrent entry, it:
1. Uses the first step ID as the "current" step
2. Appends a `**CONCURRENT STEPS**` message to the instructions
3. Expects the agent to use the Task tool to execute them in parallel

**Consistency check**: The `current_entry_index` tracks position in the `step_entries` list (which may contain concurrent groups), not the flat step list.

## Auto-Selection Behavior

If a job has exactly one workflow, `_get_workflow` auto-selects it regardless of the workflow name provided. This is a convenience for single-workflow jobs but can mask bugs where the wrong workflow name is passed.

## Key Files

- `src/deepwork/mcp/tools.py` — Tool implementations (WorkflowTools class)
- `src/deepwork/mcp/state.py` — Session state management (StateManager class)
- `src/deepwork/mcp/schemas.py` — Pydantic models for all request/response types
- `src/deepwork/mcp/server.py` — FastMCP server definition and tool registration
- `src/deepwork/mcp/quality_gate.py` — Quality gate evaluation
- `src/deepwork/mcp/claude_cli.py` — Claude CLI subprocess wrapper for external reviews
