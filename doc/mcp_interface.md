# DeepWork MCP Interface Documentation

This document describes the Model Context Protocol (MCP) tools exposed by the DeepWork server. AI agents use these tools to discover and execute multi-step workflows.

## Server Information

- **Server Name**: `deepwork`
- **Transport**: stdio (default) or SSE
- **Starting the server**: `deepwork serve --path /path/to/project`

## Tools

DeepWork exposes six MCP tools:

### 1. `get_workflows`

List all available DeepWork workflows. Call this first to discover available workflows.

#### Parameters

None.

#### Returns

```typescript
{
  jobs: JobInfo[]
}
```

Where `JobInfo` is:

```typescript
interface JobInfo {
  name: string;              // Job identifier
  summary: string;           // Short summary of the job
  description: string | null; // Full description (optional)
  workflows: WorkflowInfo[];  // Named workflows in the job
}

interface WorkflowInfo {
  name: string;              // Workflow identifier
  summary: string;           // Short description
}
```

---

### 2. `start_workflow`

Start a new workflow session. Creates a git branch, initializes state tracking, and returns the first step's instructions. Supports nested workflows — starting a workflow while one is active pushes onto a stack.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `goal` | `string` | Yes | What the user wants to accomplish |
| `job_name` | `string` | Yes | Name of the job |
| `workflow_name` | `string` | Yes | Name of the workflow within the job. If the name doesn't match but the job has only one workflow, that workflow is selected automatically. If the job has multiple workflows, an error is returned listing the available workflow names. |
| `instance_id` | `string \| null` | No | Optional identifier for naming (e.g., 'acme', 'q1-2026') |

#### Returns

```typescript
{
  begin_step: ActiveStepInfo; // Information about the first step to begin
  stack: StackEntry[];        // Current workflow stack after starting
}
```

---

### 3. `finished_step`

Report that you've finished a workflow step. Validates outputs against quality criteria (if configured), then returns the next action.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `outputs` | `Record<string, string \| string[]>` | Yes | Map of output names to file path(s). For outputs declared as type `file`: pass a single string path (e.g. `"report.md"`). For outputs declared as type `files`: pass a list of string paths (e.g. `["a.md", "b.md"]`). Outputs with `required: false` can be omitted. Check `step_expected_outputs` to see each output's declared type and required status. |
| `notes` | `string \| null` | No | Optional notes about work done |
| `quality_review_override_reason` | `string \| null` | No | If provided, skips quality review (must explain why) |
| `session_id` | `string \| null` | No | Target a specific workflow session by ID. Use when multiple workflows are active concurrently. If omitted, operates on the top-of-stack session. The session_id is returned in `ActiveStepInfo` from `start_workflow` and `finished_step`. |

#### Returns

The response varies based on the `status` field:

```typescript
{
  status: "needs_work" | "next_step" | "workflow_complete";

  // For status = "needs_work"
  feedback?: string;                    // Combined feedback from failed reviews
  failed_reviews?: ReviewResult[];      // Failed review results

  // For status = "next_step"
  begin_step?: ActiveStepInfo;         // Information about the next step to begin

  // For status = "workflow_complete"
  summary?: string;                    // Summary of completed workflow
  all_outputs?: Record<string, string | string[]>; // All outputs from all steps

  // Always included
  stack: StackEntry[];                 // Current workflow stack after this operation
}
```

---

### 4. `abort_workflow`

Abort the current workflow and return to the parent workflow (if nested). Use this when a workflow cannot be completed.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `explanation` | `string` | Yes | Why the workflow is being aborted |
| `session_id` | `string \| null` | No | Target a specific workflow session by ID. Use when multiple workflows are active concurrently. If omitted, aborts the top-of-stack session. |

#### Returns

```typescript
{
  aborted_workflow: string;           // The workflow that was aborted (job_name/workflow_name)
  aborted_step: string;               // The step that was active when aborted
  explanation: string;                // The explanation provided
  stack: StackEntry[];                // Current workflow stack after abort
  resumed_workflow?: string | null;   // The workflow now active (if any)
  resumed_step?: string | null;       // The step now active (if any)
}
```

---

### 5. `get_review_instructions`

Run a review of changed files based on `.deepreview` configuration files. Returns a list of review tasks to invoke in parallel. Each task has `name`, `description`, `subagent_type`, and `prompt` fields for the Task tool.

This tool operates outside the workflow lifecycle — it can be called independently at any time.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `files` | `string[] \| null` | No | Explicit file paths to review. When omitted, detects changes via git diff against the default branch. |

#### Returns

A plain string with one of:
- An informational message (no rules found, no changed files, no matches)
- Formatted review task list ready for parallel dispatch

---

### 6. `get_configured_reviews`

List all configured review rules from `.deepreview` files. Returns each rule's name, description, and defining file location. Optionally filters to rules matching specific files.

This tool operates outside the workflow lifecycle — it can be called independently at any time.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `only_rules_matching_files` | `string[] \| null` | No | File paths to filter by. When provided, only rules whose include/exclude patterns match at least one file are returned. When omitted, all rules are returned. |

#### Returns

```typescript
Array<{
  name: string;           // Rule name from the .deepreview file
  description: string;    // Rule description
  defining_file: string;  // Relative path to .deepreview file with line number (e.g., ".deepreview:1")
}>
```

---

## Shared Types

```typescript
interface ExpectedOutput {
  name: string;                    // Output name (use as key in finished_step outputs)
  type: string;                    // "file" or "files"
  description: string;             // What this output should contain
  required: boolean;               // If false, this output can be omitted from finished_step
  syntax_for_finished_step_tool: string; // Value format hint:
                                         //   "filepath" for type "file"
                                         //   "array of filepaths for all individual files" for type "files"
}

interface ActiveStepInfo {
  session_id: string;              // Unique session identifier
  step_id: string;                 // ID of the current step
  job_dir: string;                 // Absolute path to job directory (templates, scripts, etc.)
  step_expected_outputs: ExpectedOutput[]; // Expected outputs with type and format hints
  step_reviews: ReviewInfo[];      // Reviews to run when step completes
  step_instructions: string;       // Instructions for the step
}

interface ReviewInfo {
  run_each: string;                // 'step' or output name to review
  quality_criteria: Record<string, string>; // Map of criterion name to question
}

interface ReviewResult {
  review_run_each: string;         // 'step' or output name that was reviewed
  target_file: string | null;      // Specific file reviewed (for per-file reviews)
  passed: boolean;                 // Whether this review passed
  feedback: string;                // Summary feedback
  criteria_results: QualityCriteriaResult[];
}

interface QualityCriteriaResult {
  criterion: string;               // The quality criterion name
  passed: boolean;                 // Whether this criterion passed
  feedback: string | null;         // Feedback if failed
}

interface StackEntry {
  workflow: string;                // Workflow identifier (job_name/workflow_name)
  step: string;                    // Current step ID in this workflow
}
```

---

## Status Values

The `finished_step` tool returns one of three statuses:

| Status | Meaning | Next Action |
|--------|---------|-------------|
| `needs_work` | Quality criteria not met | Fix issues based on feedback, call `finished_step` again |
| `next_step` | Step complete, more steps remain | Execute instructions in response, call `finished_step` when done |
| `workflow_complete` | All steps complete | Workflow is finished |

---

## Workflow Usage Pattern

```
1. get_workflows()
   |
   Discover available jobs and workflows
   |
2. start_workflow(goal, job_name, workflow_name)
   |
   Get session_id, first step instructions
   |
3. Execute step instructions, create outputs
   |
4. finished_step(outputs)
   |
   +-- status = "needs_work" -> Fix issues, goto 4
   +-- status = "next_step"  -> Execute new instructions, goto 4
   +-- status = "workflow_complete" -> Done!
```

---

## Quality Gates

Steps may define quality reviews that outputs must pass. When `finished_step` is called:

1. If the step has reviews and a quality gate is configured, outputs are evaluated
2. **Input files from prior steps are included** alongside outputs in the review payload, giving the reviewer full context to evaluate whether outputs are consistent with their inputs
3. If any review fails, `status = "needs_work"` with feedback
4. If all reviews pass (or no reviews defined), workflow advances
5. After 3 failed attempts (configurable), the quality gate raises an error

### Review Payload Structure

The quality gate builds a prompt for the review agent with clearly separated sections:

```
==================== BEGIN INPUTS ====================
(contents of input files from prior steps)
==================== END INPUTS ====================

==================== BEGIN OUTPUTS ====================
(contents of output files from current step)
==================== END OUTPUTS ====================
```

- **Inputs** are resolved automatically from prior step outputs recorded in the session state. If a step declares `file` inputs with `from_step` references, the quality gate looks up the actual file paths from the referenced step's completed outputs.
- **The inputs section is omitted** if the step has no file inputs from prior steps.
- **Binary files** (e.g., PDFs) that cannot be decoded as UTF-8 are not embedded in the payload. Instead, a placeholder is included: `[Binary file — not included in review. Read from: /absolute/path/to/file]`

### Review Types

Reviews are defined per-step in the job.yml:

```yaml
reviews:
  - run_each: step                    # Review all outputs together
    quality_criteria:
      "Criterion Name": "Question to evaluate"
  - run_each: output_name             # Review a specific output
    quality_criteria:
      "Criterion Name": "Question to evaluate"
```

- `run_each: step` — Review runs once with ALL output files
- `run_each: <output_name>` where output is `type: file` — Review runs once with that specific file
- `run_each: <output_name>` where output is `type: files` — Review runs once per file in the list

To skip quality review (use sparingly):
- Provide `quality_review_override_reason` explaining why review is unnecessary

---

## Nested Workflows

Workflows can be nested — starting a new workflow while one is active pushes onto a stack:

- All tool responses include a `stack` field showing the current workflow stack
- Each stack entry shows `{workflow: "job/workflow", step: "current_step"}`
- When a workflow completes, it pops from the stack and resumes the parent
- Use `abort_workflow` to cancel the current workflow and return to parent

---

## Configuration

The MCP server is configured via `.deepwork/config.yml`:

```yaml
version: "1.0"
platforms:
  - claude
```

Quality gate is enabled by default and uses Claude Code to evaluate step outputs
against quality criteria. See `doc/reference/calling_claude_in_print_mode.md` for
details on how Claude CLI is invoked.

---

## Server CLI Options

```bash
deepwork serve [OPTIONS]

Options:
  --path PATH            Project root directory (default: current directory)
  --no-quality-gate      Disable quality gate evaluation
  --transport TYPE       Transport type: stdio or sse (default: stdio)
  --port PORT            Port for SSE transport (default: 8000)
  --external-runner TYPE External runner for quality gate reviews (default: None)
  --platform NAME        Platform identifier (e.g., 'claude'). Used by the review tool to format output.
```

---

## Example MCP Configuration

Add to your `.mcp.json`:

```json
{
  "mcpServers": {
    "deepwork": {
      "command": "deepwork",
      "args": ["serve", "--path", "."]
    }
  }
}
```

---

## Changelog

| Version | Changes |
|---------|---------|
| 1.6.0 | Added `get_configured_reviews` tool for listing configured review rules without running the full pipeline. Supports optional file-based filtering. |
| 1.5.0 | Added `get_review_instructions` tool (originally named `review`) for running `.deepreview`-based code reviews via MCP. Added `--platform` CLI option to `serve` command. |
| 1.4.0 | Added optional `session_id` parameter to `finished_step` and `abort_workflow` for concurrent workflow safety. When multiple workflows are active on the stack, callers can pass the `session_id` (returned in `ActiveStepInfo`) to target the correct session. Fully backward compatible — omitting `session_id` preserves existing top-of-stack behavior. |
| 1.3.0 | `step_expected_outputs` changed from `string[]` to `ExpectedOutput[]` — each entry includes `name`, `type`, `description`, and `syntax_for_finished_step_tool` so agents know exactly what format to use when calling `finished_step`. |
| 1.2.0 | Quality gate now includes input files from prior steps in review payload with BEGIN INPUTS/END INPUTS and BEGIN OUTPUTS/END OUTPUTS section headers. Binary files (PDFs, etc.) get a placeholder instead of raw content. |
| 1.1.0 | Added `abort_workflow` tool, `stack` field in all responses, `ReviewInfo`/`ReviewResult` types, typed outputs as `Record<string, string \| string[]>` |
| 1.0.0 | Initial MCP interface with `get_workflows`, `start_workflow`, `finished_step` |
