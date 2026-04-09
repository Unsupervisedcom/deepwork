---
name: deepwork
description: "Start or continue DeepWork workflows in OpenClaw using MCP tools"
---

# DeepWork Workflow Manager

Execute multi-step DeepWork workflows in OpenClaw.

## Runtime Contract

- Read the injected DeepWork OpenClaw bootstrap note before using the tools.
- Use the `session_id` shown there for all DeepWork MCP calls in the current OpenClaw session.
- If the bootstrap note says prior DeepWork state may exist, call `deepwork__get_active_workflow` first to restore context before starting anything new.

## How to Use

1. Call `deepwork__get_workflows` to discover available workflows.
2. If resuming, call `deepwork__get_active_workflow`.
3. Call `deepwork__start_workflow` with `goal`, `job_name`, `workflow_name`, and `session_id`.
4. Follow the returned step instructions.
5. If `begin_step.step_inputs` shows any required input with `value: null`, stop before doing step work.
6. If the missing input is already clear from the user's request, restart the workflow with `deepwork__start_workflow(..., inputs={...})` so the value is populated from the beginning.
7. If the missing input is not clear, ask the user instead of fabricating outputs or calling `deepwork__finished_step`.
8. Never call `deepwork__finished_step` for a step whose required inputs are still missing.
9. Before submitting outputs, compare them to `step_expected_outputs` or call `deepwork__validate_step_outputs`.
10. Call `deepwork__finished_step` with your outputs when the step is done.
11. Handle the response: `needs_work`, `next_step`, or `workflow_complete`.

## Quality Gates

- DeepWork may require reviews before a step can advance.
- In OpenClaw, prefer launching those reviews as parallel sub-agents with `sessions_spawn`, then use `sessions_yield` to wait for completions.
- Spawn all review sub-agents before waiting, keep instruction paths workspace-relative, and do not set `timeoutSeconds` on review spawns unless you must use `0`.
- After applying any fixes, call `deepwork__finished_step` again.

## Navigation

- Use `deepwork__abort_workflow` if a workflow cannot be completed.
- Use `deepwork__go_to_step` to revisit an earlier step and clear later progress.

## Intent Parsing

When the user invokes `/deepwork`:

1. Always call `deepwork__get_workflows`.
2. If the request clearly matches one workflow, start it.
3. If multiple workflows could fit, summarize the closest matches and ask the user which one they want.
