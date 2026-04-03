# job.yml Field Guidance

This document explains what each `job.yml` field *does* at runtime. It is not a schema reference -- it describes behavioral impact so you can make informed authoring decisions. For the authoritative schema, see `src/deepwork/jobs/job.schema.json`.

---

## Root Fields

### `name`

The job's unique identifier (pattern: `^[a-z][a-z0-9_]*$`). This is the value agents pass as `job_name` to `start_workflow`. It also determines the directory name under `.deepwork/jobs/` and appears in `get_workflows` output.

### `summary`

A one-line description (max 200 chars). Shown in `get_workflows` output so agents can decide which job to use. Write it as an action -- "Analyze competitors and produce a positioning report" -- not as a label.

### `step_arguments`

The shared data vocabulary. Every piece of data that flows between steps must be declared here. Steps reference these by name in their `inputs` and `outputs` maps. Think of step_arguments as the schema for the pipeline's data bus.

### `workflows`

A map of named workflows, each defining a sequence of steps. A job can have multiple workflows (e.g., `create` and `repair`). Workflow names are the `workflow_name` parameter in `start_workflow`.

---

## step_arguments: The Data Contract

Each step_argument defines a named piece of data with three required fields (`name`, `description`, `type`) and two optional fields (`review`, `json_schema`).

### `name`

Unique identifier that steps reference in their `inputs` and `outputs` maps. Can contain letters, numbers, dots, slashes, hyphens, and underscores -- so you can use file-like names like `job.yml` or `.deepwork/tmp/test_feedback.md`.

### `description`

Shown to the agent when it needs to produce or consume this argument. Be specific -- "The job.yml definition file for the new job" is far more useful than "A YAML file".

### `type`: string vs file_path

This controls **output validation** in `finished_step`:

- **`file_path`**: The agent provides a path (or list of paths). The framework checks that every referenced file exists on disk. If any file is missing, `finished_step` returns an error immediately. When shown as a step input, file paths appear as backtick-quoted references (e.g., `` `path/to/file.md` ``). Reviews examine the file contents.

- **`string`**: The agent provides inline text. No file existence check -- the value is accepted as-is. When shown as a step input, the actual string content is included inline in the step instructions.

Rule of thumb: if the data would be committed to Git (a report, a config file), use `file_path`. If it is transient context (a user's answer, a job name), use `string`.

### `review`

An optional review block that applies **whenever this argument is produced as a step output, in any step, in any workflow**. This is a default review for this piece of data.

```yaml
- name: step_instruction_files
  description: "Instruction Markdown files for each step"
  type: file_path
  review:
    strategy: individual
    instructions: |
      Evaluate: Complete instructions, specific & actionable, output examples shown.
```

You define quality criteria once, and they apply everywhere. If three workflows all produce `step_instruction_files`, they all get this review. Steps can add additional scrutiny with output-level reviews (see "Review Cascade" below).

### `json_schema`

Only applies to `file_path` arguments. When set, the framework parses each output file (JSON or YAML based on file extension) and validates it against the schema **before any reviews run**. If validation fails, `finished_step` returns the error immediately -- reviews are skipped entirely. This is a hard gate, not a soft review. Use for structured outputs where format correctness is non-negotiable.

---

## Workflows

Workflows are the primary execution unit. Agents start workflows, not individual steps.

### `summary`

A one-line description (max 200 chars) shown alongside the workflow name in `get_workflows` output. Helps the agent pick the right workflow when a job has multiple.

### `agent`

Changes how the workflow appears in `get_workflows`. Without `agent`, the response tells the caller to invoke `start_workflow` directly:

> Call `start_workflow` with job_name="X" and workflow_name="Y", then follow the step instructions it returns.

With `agent` set (e.g., `"general-purpose"`), the response tells the caller to spawn a **Task sub-agent** of that type:

> Invoke as a Task using subagent_type="general-purpose" with a prompt giving full context and instructions to call `start_workflow`...

If the agent does not have the Task tool available, the instructions fall back to direct invocation.

Use `agent` for workflows that should execute autonomously without blocking the main conversation.

### `common_job_info_provided_to_all_steps_at_runtime`

This text has **two runtime effects**:

1. **Step instructions**: Delivered as a separate `common_job_info` field in the response when a step starts. The agent sees it alongside the step instructions.
2. **Review prompts**: Included as a "Job Context" preamble in every dynamic review built from this workflow's step outputs. Reviewers see it automatically.

Use it for shared knowledge every step (and every reviewer) needs: project background, key terminology, constraints, conventions, schema references. This avoids duplicating the same context in every step's `instructions` field and every review's `instructions` field.

### `post_workflow_instructions`

Returned to the agent when the **last step completes successfully** (in the `workflow_complete` response from `finished_step`). Use for guidance on what to do after the workflow finishes -- "Create a PR", "Run the test suite", "Notify the user".

This text is only delivered once, at the end. It is not included in any step instructions or reviews.

### `steps`

An ordered array of step definitions. Steps execute sequentially -- the agent completes one step (via `finished_step`) before receiving the next step's instructions.

---

## Steps

Each step must have a `name` and exactly one of `instructions` or `sub_workflow`. Having both or neither is a parse error.

### `name`

Unique step identifier within the workflow (pattern: `^[a-z][a-z0-9_]*$`). Used as `step_id` in MCP responses and for tracking progress.

### `instructions`

Inline markdown telling the agent what to do. At runtime, the framework builds the final instructions by prepending resolved input values (file paths as backtick references, string values inline), then appending the step's instructions. The `common_job_info` is delivered as a separate field in the response.

### `sub_workflow`

Instead of inline instructions, delegate this step to another workflow. The framework auto-generates instructions:

> Call `start_workflow` with job_name="current_job" and workflow_name="target_workflow", then follow the instructions it returns until the sub-workflow completes.

See "Sub-workflows" below for details on same-job vs cross-job references and stack behavior.

### `inputs`

A map of step_argument names to input configuration. Input values are resolved at runtime from two sources, checked in order:

1. **Provided inputs** from `start_workflow`'s `inputs` parameter (first step only)
2. **Previous step outputs** accumulated in the session

Each input has a `required` flag (default `true`). Missing required inputs show as "not yet available" in the step instructions rather than causing an error. Optional inputs (`required: false`) behave the same way but signal intent that the value may not exist.

Resolved input values are formatted and prepended to the step instructions:
- `file_path` inputs: `` - **name** (required): `path/to/file.md` ``
- `string` inputs: `- **name** (required): the actual value`

These same input values are also included in review prompts as "Step Inputs" context.

### `outputs`

A map of step_argument names to output configuration. When the agent calls `finished_step`, validation runs in this order:

1. **Completeness**: All required outputs must be present. No unknown output names allowed.
2. **Type validation**: `file_path` values must point to existing files. `string` values must be strings.
3. **JSON schema**: If the step_argument has `json_schema`, file contents are parsed (JSON or YAML based on extension) and validated. Failures are returned immediately; reviews are skipped.
4. **Quality reviews**: Dynamic reviews from the output ref and step_argument, plus .deepreview rules.

**Important**: The agent must provide ALL required outputs on every `finished_step` call, even outputs whose files have not changed since a previous attempt. The framework re-validates everything each time.

The `review` field on an output is step-specific and **supplements** (does not replace) any review on the step_argument. See "Review Cascade" below.

### `process_requirements`

A map of requirement names to **requirement statements using RFC 2119 keywords** (MUST, SHOULD, MAY, SHALL, RECOMMENDED, etc.):

```yaml
process_requirements:
  tests_written: "Unit tests MUST be written before implementation code."
  user_consulted: "The user SHOULD be asked to confirm the approach."
```

The reviewer will fail any MUST/SHALL requirement that is not met, fail any SHOULD/RECOMMENDED requirement that appears easily achievable but was not followed, and give feedback without failing for other applicable requirements.

At runtime, this creates a synthetic review with `matches_together` strategy that evaluates the agent's `work_summary` (provided in `finished_step`) against these criteria. The review prompt includes:
- The workflow's `common_job_info`
- The step's input values
- All quality criteria as a bulleted list
- The `work_summary` text
- References to all output files (so the reviewer can cross-check claims)

The reviewer checks whether the work described in `work_summary` satisfies each criterion. If the work_summary is incomplete or inaccurate, the reviewer tells the agent to fix its work or its work_summary.

This is for **process quality** -- did the agent follow the right process? -- not for output quality, which is handled by output reviews.

---

## The Review Cascade

Reviews on step outputs come from **three independent sources** that are merged at runtime. Understanding their interaction is essential.

### Source 1: Step output review

A `review` block on a specific step's output ref. Created as a dynamic `ReviewRule` named `step_{step_name}_output_{arg_name}`.

### Source 2: Step_argument review

A `review` block on the step_argument itself. Created as a dynamic `ReviewRule` named `step_{step_name}_output_{arg_name}_arg` (note the `_arg` suffix).

### Source 3: .deepreview rules

Project-wide review rules from `.deepreview` files. These match output files by glob pattern and are loaded independently of the job definition.

### How they merge

All three sources produce `ReviewRule` objects that are matched against the output file paths. They run as **separate, independent reviews** -- they do not replace each other.

The ordering matters: for each output, the step output review (source 1) is added first, then the step_argument review (source 2) with the `_arg` suffix. Both run as separate review tasks. Then .deepreview rules are matched and added after all dynamic rules.

```
Step output review:      step_define_output_job.yml      -> runs
Step_argument review:    step_define_output_job.yml_arg  -> runs (separately)
.deepreview rule:        yaml_standards                  -> runs (if pattern matches)
```

The practical effect: a step_argument review provides a baseline quality check that applies everywhere, a step output review adds step-specific scrutiny, and .deepreview rules add project-wide standards. They stack.

### Review context

Every dynamic review (from sources 1 and 2) automatically receives a preamble containing:
- The workflow's `common_job_info` as "Job Context" (if set)
- The step's resolved input values as "Step Inputs"

This is prepended to the review's own `instructions`. You do not need to repeat domain context in review instructions.

### After reviews

If any reviews need to run, `finished_step` returns `NEEDS_WORK` status with instructions for the agent to launch review tasks. After fixing issues (or marking reviews as passed), the agent calls `finished_step` again. Previously passing reviews are skipped via `.passed` marker files.

---

## Sub-workflows

### Same-job references

```yaml
sub_workflow:
  workflow_name: code_review
```

References another workflow in the same job. Validated at parse time -- the parser checks that the target workflow exists.

### Cross-job references

```yaml
sub_workflow:
  workflow_name: quality_check
  workflow_job: shared_tools
```

References a workflow in a different job. **Not validated at parse time** because the other job may not be loaded. Validated at runtime when `start_workflow` is called.

### Stack behavior

When a step has `sub_workflow`, the agent calls `start_workflow` for the sub-workflow. This **pushes onto the session stack**. The sub-workflow runs its steps normally. When its last step completes, `finished_step` returns `workflow_complete` and the sub-workflow **pops off the stack**, returning control to the parent workflow.

The agent still needs to call `finished_step` on the parent step after the sub-workflow completes -- the sub-workflow's completion does not automatically advance the parent.

The `abort_workflow` tool can unwind the stack, aborting the current sub-workflow and resuming the parent.

---

## review_block Fields

Both step_argument reviews and step output reviews use the same shape:

### `strategy`

- **`individual`**: One review per output file. Each file gets its own review agent call. Use when multiple files should be evaluated independently. Many files do NOT cause timeout accumulation -- each is a separate MCP call.
- **`matches_together`**: All matched output files reviewed in one call. Use when files form a coherent set that must be evaluated together.

Note: `all_changed_files` (available in `.deepreview` rules) is not available in job.yml review blocks.

### `instructions`

What to tell the reviewer. Be specific and actionable -- "Verify the YAML has at least 3 steps and each step has both inputs and outputs" is better than "Check if the job looks good." The framework prepends job context and step inputs automatically.

### `agent`

Routes the review to a specific agent persona. A map of platform names to persona identifiers:

```yaml
agent:
  claude: "security-expert"
```

When not set, reviews use the default reviewer.

### `additional_context`

Flags controlling extra information in the review prompt:

- **`all_changed_filenames: true`**: Include a list of all output files, even if the review strategy only examines a subset. Useful when reviewing one file but needing awareness of the full change set.
- **`unchanged_matching_files: true`**: Include files that match the include patterns but were not produced as outputs. Useful for freshness reviews where the reviewer needs to see existing documents alongside new ones.

---

## Data Flow Summary

Input values are resolved in order: (1) `start_workflow` provided inputs, then (2) accumulated outputs from previous steps. All required outputs must be provided on every `finished_step` call, even unchanged ones. When the last step completes, all accumulated outputs are returned alongside `post_workflow_instructions`.
