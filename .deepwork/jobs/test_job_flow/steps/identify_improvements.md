# Investigate Code and Propose Improvements

## Objective

Read the friction report from step 2, investigate the DeepWork system code to understand the root causes, and propose concrete improvements to reduce job creation friction.

## Task

Turn the observed friction points into actionable engineering recommendations by tracing each problem to its source in the codebase.

### Process

1. **Read the friction report**
   - Read `.deepwork/tmp/job_creation_friction.md` carefully
   - List each friction point and categorize by type (error, UX, missing feature, documentation gap, etc.)

2. **Investigate the new_job workflow**
   - Read the `new_job` workflow definition in `.deepwork/jobs/deepwork_jobs/job.yml`
   - Read the step instruction files in `.deepwork/jobs/deepwork_jobs/steps/`
   - For each friction point, trace it to the specific instruction, template, or workflow configuration that caused it

3. **Investigate the system code**
   - Look at the MCP server code in `src/deepwork/` — particularly the workflow execution, quality review, and step management code
   - Check template files in `.deepwork/jobs/deepwork_jobs/templates/`
   - Look at the `make_new_job.sh` script and any other tooling
   - Identify code-level causes of friction (e.g., missing validation, unclear error messages, timeout issues)

4. **Develop recommendations**
   For each friction point, propose one or more concrete improvements:
   - **What to change**: Specific file(s) and the nature of the change
   - **Why it helps**: How this addresses the friction point
   - **Effort estimate**: Small (< 1 hour), Medium (1-4 hours), Large (4+ hours)
   - **Risk**: What could go wrong with this change

5. **Prioritize recommendations**
   - Rank by impact-to-effort ratio
   - Group into "quick wins" vs "larger investments"
   - Note any dependencies between recommendations

## Output Format

### recommendations

A markdown file at `.deepwork/tmp/improvement_recommendations.md`.

**Structure**:
```markdown
# DeepWork Job Creation Improvement Recommendations

## Executive Summary
[2-3 sentences on the biggest opportunities for improvement]

## Quick Wins (Small effort, meaningful impact)

### 1. [Recommendation title]
- **Addresses friction point**: [reference to friction report item]
- **What to change**: [specific file(s) and description of change]
- **Why it helps**: [expected impact]
- **Effort**: Small
- **Risk**: [what could go wrong]

## Medium Investments

### 2. [Recommendation title]
...

## Larger Investments

### 3. [Recommendation title]
...

## Not Recommended
[Any ideas considered but rejected, and why]

## Implementation Order
[Suggested sequence for implementing the recommendations, noting dependencies]
```

## Context

This is the final step of the test_job_flow. Its output is a decision document for the user — they will review these recommendations and decide which ones to implement. The quality of this output determines whether the entire test_job_flow exercise produces actionable value. Be thorough but practical; the user wants recommendations they can act on, not a theoretical analysis.
