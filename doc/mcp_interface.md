# DeepWork MCP Interface Documentation

This document describes the Model Context Protocol (MCP) tools exposed by the DeepWork server. AI agents use these tools to discover and execute multi-step workflows.

## Server Information

- **Server Name**: `deepwork`
- **Transport**: stdio (default) or SSE
- **Starting the server**: `deepwork serve --path /path/to/project`

## Tools

DeepWork exposes three MCP tools:

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

interface ActiveStepInfo {
  session_id: string;        // Unique session identifier
  branch_name: string;       // Git branch for this workflow instance
  step_id: string;           // ID of the current step
  step_expected_outputs: string[]; // Expected output files for this step
  step_quality_criteria: string[]; // Criteria for step completion (if configured)
  step_instructions: string; // Instructions for the step
}
```

---

### 2. `start_workflow`

Start a new workflow session. Creates a git branch, initializes state tracking, and returns the first step's instructions.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `goal` | `string` | Yes | What the user wants to accomplish |
| `job_name` | `string` | Yes | Name of the job |
| `workflow_name` | `string` | Yes | Name of the workflow within the job |
| `instance_id` | `string \| null` | No | Optional identifier for naming (e.g., 'acme', 'q1-2026') |

#### Returns

```typescript
{
  begin_step: ActiveStepInfo; // Information about the first step to begin
}
```

---

### 3. `finished_step`

Report that you've finished a workflow step. Validates outputs against quality criteria (if configured), then returns the next action.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `outputs` | `string[]` | Yes | List of output file paths created |
| `notes` | `string \| null` | No | Optional notes about work done |
| `quality_review_override_reason` | `string \| null` | No | If provided, skips quality review (must explain why) |

#### Returns

The response varies based on the `status` field:

```typescript
{
  status: "needs_work" | "next_step" | "workflow_complete";

  // For status = "needs_work"
  feedback?: string;                    // Feedback from quality gate
  failed_criteria?: QualityCriteriaResult[]; // Failed quality criteria

  // For status = "next_step"
  begin_step?: ActiveStepInfo;         // Information about the next step to begin

  // For status = "workflow_complete"
  summary?: string;                    // Summary of completed workflow
  all_outputs?: string[];              // All outputs from all steps
}

interface QualityCriteriaResult {
  criterion: string;         // The quality criterion text
  passed: boolean;           // Whether this criterion passed
  feedback: string | null;   // Feedback if failed
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
   ↓
   Discover available jobs and workflows
   ↓
2. start_workflow(goal, job_name, workflow_name)
   ↓
   Get session_id, branch_name, first step instructions
   ↓
3. Execute step instructions, create outputs
   ↓
4. finished_step(outputs)
   ↓
   ├─ status = "needs_work" → Fix issues, goto 4
   ├─ status = "next_step" → Execute new instructions, goto 4
   └─ status = "workflow_complete" → Done!
```

---

## Quality Gates

Steps may define quality criteria that outputs must meet. When `finished_step` is called:

1. If the step has quality criteria and a quality gate agent is configured, outputs are evaluated
2. If any criteria fail, `status = "needs_work"` with feedback
3. If all criteria pass (or no criteria defined), workflow advances

To skip quality review (use sparingly):
- Provide `quality_review_override_reason` explaining why review is unnecessary

---

## Configuration

The MCP server is configured via `.deepwork/config.yml`:

```yaml
version: "1.0"
platforms:
  - claude

# Quality gate configuration (optional)
quality_gate:
  agent_review_command: "claude --print"  # Command to run quality gate agent
  default_timeout: 120                     # Timeout in seconds
  default_max_attempts: 3                  # Max attempts before failing
```

---

## Server CLI Options

```bash
deepwork serve [OPTIONS]

Options:
  --path PATH        Project root directory (default: current directory)
  --quality-gate CMD Command for quality gate agent (overrides config)
  --transport TYPE   Transport type: stdio or sse (default: stdio)
  --port PORT        Port for SSE transport (default: 8000)
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
| 1.0.0 | Initial MCP interface with `get_workflows`, `start_workflow`, `finished_step` |
