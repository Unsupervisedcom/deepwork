---
name: "Quality Review System"
keywords:
  - quality
  - review
  - gate
  - criteria
  - evaluate
  - self-review
  - external
  - timeout
  - run_each
  - for_each
last_updated: "2026-02-18"
---

## Overview

The quality review system evaluates step outputs against criteria defined in `job.yml`. It runs after `finished_step` is called and before the workflow advances to the next step. If reviews fail, the agent gets `needs_work` status with feedback and must fix issues before retrying.

## Two Review Modes

### 1. External Runner Mode (`external_runner="claude"`)

- Uses Claude CLI as a subprocess to evaluate outputs
- The reviewer is a separate model invocation with structured JSON output
- Each review is an independent subprocess call
- `max_inline_files` defaults to 5 — files beyond this threshold are listed as paths only
- Dynamic timeout: `240 + 30 * max(0, file_count - 5)` seconds

### 2. Self-Review Mode (`external_runner=None`)

- Writes review instructions to `.deepwork/tmp/quality_review_<session>_<step>.md`
- Returns `needs_work` with instructions for the agent to spawn a subagent
- The subagent reads the file, evaluates criteria, and reports findings
- The agent fixes issues, then calls `finished_step` again with `quality_review_override_reason`
- `max_inline_files` defaults to 0 (always lists paths, never embeds content)

## Review Configuration in job.yml

Reviews are defined per-step in the `reviews` array:

```yaml
reviews:
  - run_each: step                    # Review all outputs together
    quality_criteria:
      "Criterion Name": "Question to evaluate"

  - run_each: step_instruction_files  # Review each file in this output separately
    additional_review_guidance: "Context for the reviewer"
    quality_criteria:
      "Complete": "The file is complete with no stubs"
```

### `run_each` Values

- `"step"` — Run one review covering all outputs together
- `"<output_name>"` — If the output has `type: files`, run a separate review per file. If `type: file`, run one review for that single file.

### `additional_review_guidance`

Free-text context passed to the reviewer. This is critical because reviewers don't have transcript access — they only see the output files and the criteria. Use this to tell reviewers what else to read for context.

## Consistency Points for PR Reviews

### 1. Criteria Must Be Evaluable Without Transcript

Reviewers see only: output files, quality criteria, additional_review_guidance, and author notes. They cannot see the conversation. If a criterion requires conversation context (e.g., "User confirmed satisfaction"), the step must write a summary file as an output that the reviewer can read.

### 2. Criteria Should Be Pragmatic

The reviewer instructions say: "If a criterion is not applicable to this step's purpose, pass it." But in practice, vague criteria cause confusion. Each criterion should clearly describe what "pass" looks like.

**Bad**: "Good formatting" (subjective, unclear)
**Good**: "The output uses markdown headers to organize sections" (specific, verifiable)

### 3. The Reviewer Can Contradict Itself

Known issue: The reviewer model can mark all individual criteria as passed but still set `overall: false`. The `additional_review_guidance` field helps mitigate this by giving the reviewer better context. When reviewing PR changes to criteria, check if guidance is also updated.

### 4. Timeout Awareness

- Each `run_each` review per file is a separate MCP call with its own timeout
- Many small files do NOT accumulate timeout risk (they run in parallel via `asyncio.gather`)
- A single large/complex file can cause its individual review to timeout
- The `quality_review_override_reason` parameter exists as an escape hatch when reviews timeout (120s MCP limit)

### 5. Max Quality Attempts

Default is 3 attempts (`max_quality_attempts`). After 3 failed attempts, the quality gate raises a `ToolError` and the workflow is blocked. This prevents infinite retry loops.

### 6. Output Specs Must Match Review Scope

If a review has `run_each: "step_instruction_files"`, that output name must exist in the step's `outputs` section with `type: files`. A mismatch means the review silently does nothing (the output name won't be found in the outputs dict, so no per-file reviews are generated).

### 7. JSON Schema Enforcement

External reviews must return structured JSON matching `QUALITY_GATE_RESPONSE_SCHEMA`:
```json
{
  "passed": boolean,
  "feedback": string,
  "criteria_results": [
    {"criterion": string, "passed": boolean, "feedback": string|null}
  ]
}
```

Changes to the schema must be reflected in both `quality_gate.py` (the schema definition) and the reviewer prompt instructions.

## Key Files

- `src/deepwork/mcp/quality_gate.py` — QualityGate class, review evaluation, payload building
- `src/deepwork/mcp/claude_cli.py` — Claude CLI wrapper for external reviews
- `src/deepwork/mcp/tools.py:364-481` — Quality gate integration in `finished_step`
- `src/deepwork/mcp/schemas.py` — QualityGateResult, ReviewResult, QualityCriteriaResult models
