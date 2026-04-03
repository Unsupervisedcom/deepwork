# JOBS-REQ-014: DeepPlan Standard Job

## Overview

DeepPlan is a standard job that provides a structured planning workflow. When an agent enters plan mode, it starts the `create_deep_plan` workflow which guides it through exploring the problem, generating design alternatives, synthesizing a plan, enriching it into an executable DeepWork job definition via `register_session_job`, and presenting it for user approval. The enriched plan becomes a session-scoped job that can be executed after plan approval.

## Requirements

### JOBS-REQ-014.1: Standard Job Definition

1. The `deepplan` job MUST be located in `src/deepwork/standard_jobs/deepplan/`.
2. The job MUST be auto-discovered at runtime by the MCP server (standard job behavior per JOBS-REQ-008.4).
3. The job definition MUST pass validation via `parse_job_definition()`.
4. The job `name` field MUST be `deepplan`.

### JOBS-REQ-014.2: Workflow Structure

1. The job MUST define a workflow named `create_deep_plan`.
2. The workflow MUST contain exactly five steps in this order: `initial_understanding`, `design_alternatives`, `review_and_synthesize`, `enrich_the_plan`, `present_plan`.
3. The workflow MUST define `common_job_info_provided_to_all_steps_at_runtime` that tells the agent its instructions supersede default planning phases.
4. The workflow MUST define `post_workflow_instructions` that guide the agent to start the session job after completion.

### JOBS-REQ-014.3: Step Arguments

1. The job MUST define an `original_user_request` step argument of type `string`.
2. The job MUST define a `draft_plan_file` step argument of type `file_path`.
3. The job MUST define a `session_job_name` step argument of type `string`.
4. The job SHOULD define a `key_reference_files` step argument of type `file_path`.
5. The job SHOULD define a `key_affected_files` step argument of type `file_path`.

### JOBS-REQ-014.4: Step Data Flow

1. The `initial_understanding` step MUST output `original_user_request` as required.
2. The `design_alternatives` step MUST accept `original_user_request` as a required input.
3. The `review_and_synthesize` step MUST output `draft_plan_file` as required.
4. The `enrich_the_plan` step MUST output `session_job_name` as required.
5. The `present_plan` step MUST accept `session_job_name` and `draft_plan_file` as required inputs.
6. The `original_user_request` MUST flow through all steps after `initial_understanding` as an input.

### JOBS-REQ-014.5: Planning Mode Integration

1. The startup context hook MUST inject an instruction telling agents to start the `create_deep_plan` workflow when entering plan mode.
2. The `present_plan` step MUST instruct the agent to call `ExitPlanMode` instead of `finished_step`.
3. The plan file MUST include execution instructions telling the post-approval agent to call `finished_step` on `present_plan` and then `start_workflow` on the session job.

### JOBS-REQ-014.6: Quality Reviews

1. The `draft_plan_file` step argument MUST have a review checking whether it achieves the `original_user_request`.
2. The `enrich_the_plan` step MUST have a review on `session_job_name` checking whether the registered job completes the `original_user_request`.
3. The `enrich_the_plan` step MUST have a review on `draft_plan_file` checking alignment with the session job.
