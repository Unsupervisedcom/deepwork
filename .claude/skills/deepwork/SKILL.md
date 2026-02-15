---
name: deepwork
description: "Start or continue DeepWork workflows using MCP tools"
---

# DeepWork Workflow Manager

Execute multi-step workflows with quality gate checkpoints.

> **IMPORTANT**: Use the DeepWork MCP server tools. All workflow operations
> are performed through MCP tool calls and following the instructions they return,
> not by reading instructions from files.

## How to Use

1. Call `get_workflows` to discover available workflows
2. Call `start_workflow` with goal, job_name, and workflow_name
3. Follow the step instructions returned
4. Call `finished_step` with your outputs when done
5. Handle the response: `needs_work`, `next_step`, or `workflow_complete`

## Creating New Jobs

<important>
You MUST use the `new_job` workflow to create new DeepWork jobs. NEVER create job
definitions by manually writing `job.yml` files, step instructions, or job directory
structures by hand. The `new_job` workflow exists specifically to ensure jobs are
well-structured, tested, and reviewed.
</important>

To create a new job, use the MCP tools:

1. Call `get_workflows` to confirm the `deepwork_jobs` job is available
2. Call `start_workflow` with:
   - `job_name`: `"deepwork_jobs"`
   - `workflow_name`: `"new_job"`
   - `goal`: a description of what the new job should accomplish
   - `instance_id`: a short name for the new job (e.g., `"code_review"`)
3. Follow the guided steps: **define** → **implement** → **test** → **iterate**

The workflow handles specification authoring, file generation, real-world testing, and
iterative refinement. Skipping it produces brittle, untested jobs that lack quality gates.

## Intent Parsing

When the user invokes `/deepwork`, parse their intent:
1. **ALWAYS**: Call `get_workflows` to discover available workflows
2. Based on the available flows and what the user said in their request, proceed:
    - **Explicit workflow**: `/deepwork <a workflow name>` → start the `<a workflow name>` workflow
    - **General request**: `/deepwork <a request>` → infer best match from available workflows
    - **No context**: `/deepwork` alone → ask user to choose from available workflows