# DeepWork Workflow Manager

Execute multi-step workflows with quality gate checkpoints.

## Terminology

A **job** is a collection of related **workflows**. For example, a "code_review" job
might contain workflows like "review_pr" and "review_diff". Users may use the terms
"job" and "workflow" somewhat interchangeably when describing the work they want done —
use context and the available workflows from `get_workflows` to determine the best match.

> **IMPORTANT**: Use the DeepWork MCP server tools. All workflow operations
> are performed through MCP tool calls and following the instructions they return,
> not by reading instructions from files.

## How to Use

1. Call `get_workflows` to discover available workflows
2. Call `start_workflow` with goal, job_name, and workflow_name
3. Follow the step instructions returned; use the `session_id` from `begin_step` for all subsequent calls
4. Call `finished_step` with your outputs when done
5. Handle the response: `needs_work`, `next_step`, or `workflow_complete`

## Creating New Jobs

<important>
You MUST create new DeepWork jobs by starting the `new_job` workflow via the DeepWork
MCP tools. Follow the guidance from the DeepWork MCP server as you go through the
workflow — it will walk you through each step.
</important>

To create a new job, use the MCP tools:

1. Call `get_workflows` to confirm the `deepwork_jobs` job is available
2. Call `start_workflow` with:
   - `job_name`: `"deepwork_jobs"`
   - `workflow_name`: `"new_job"`
   - `goal`: a description of what the new job should accomplish
3. Follow the instructions returned by the MCP tools as you progress through the workflow

## Quality Gates

Steps may have quality criteria. When you call `finished_step`:
- Outputs are evaluated against review criteria
- If any fail, you get `needs_work` with feedback — fix issues and call `finished_step` again
- After passing, you get the next step or completion

## Nested Workflows and Navigation

- Starting a workflow while one is active pushes onto a stack. Check the `stack` field in responses.
- Use `abort_workflow` with an explanation if a workflow cannot be completed.
- Use `go_to_step` to revisit an earlier step — clears progress from that step onward.

## Tips

- Create all expected outputs before calling `finished_step` — check `step_expected_outputs` for what's required
- Provide clear, specific goals when starting — they're used for context throughout the workflow
- Read quality gate feedback carefully before retrying — it tells you exactly what to fix
- Don't leave workflows in a broken state — use `abort_workflow` if you can't complete

## Intent Parsing

When the user invokes `/deepwork`, parse their intent:
1. **ALWAYS**: Call `get_workflows` to discover available workflows
2. Based on the available flows and what the user said in their request, proceed:
    - **Explicit workflow**: `/deepwork <a workflow name>` → start the `<a workflow name>` workflow
    - **General request**: `/deepwork <a request>` → infer best match from available workflows
    - **No context**: `/deepwork` alone → ask user to choose from available workflows
