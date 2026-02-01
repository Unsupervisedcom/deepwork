---
name: review_pr.check_relevance
description: "Invokes all available experts in parallel to assess if PR changes are relevant to their domain. Use at the start of a PR review."
user-invocable: false

---

# review_pr.check_relevance

**Step 1/3** in **full** workflow

> Full PR review: relevance check, deep review, and improvement cycles

> Coordinates expert-driven PR review with iterative improvement cycles until all feedback is addressed.


## Instructions

**Goal**: Invokes all available experts in parallel to assess if PR changes are relevant to their domain. Use at the start of a PR review.

# Check Expert Relevance

## Objective

Invoke all available experts in parallel to determine which ones have relevant expertise for the PR changes. This filtering step ensures only applicable experts spend time on detailed review.

## Task

Assess which domain experts can meaningfully contribute to reviewing the current PR by having each expert examine the changes and report their relevance.

### Process

1. **Get PR information**

   Determine the PR to review:
   ```bash
   # If pr_number input provided, use it
   # Otherwise, get PR for current branch
   gh pr view --json number,title,headRefName
   ```

   Get the changed files:
   ```bash
   gh pr diff --name-only
   ```

   Get the actual diff for context:
   ```bash
   gh pr diff
   ```

2. **Discover available experts**

   List all experts in the project:
   ```bash
   ls -1 .deepwork/experts/
   ```

   Read each expert's `discovery_description` from their `expert.yml` to understand their domain.

3. **Invoke experts in parallel**

   For each expert, use the Task tool to spawn a sub-agent:
   - `subagent_type`: "expert"
   - `agent`: `[expert-name]` (the folder name with underscores as dashes)
   - `prompt`: Provide the expert with:
     - The list of changed files
     - A summary of the diff (or key portions)
     - Ask them to determine if changes fall within their domain of expertise

   **Expert prompt template**:
   ```
   Review this PR to determine if the changes are relevant to your domain of expertise.

   Changed files:
   [list of files]

   Key changes:
   [summary or excerpts from diff]

   Respond with:
   1. RELEVANT or NOT_RELEVANT
   2. Brief justification (1-2 sentences)
   3. If relevant, which specific files/changes you can review
   ```

   **Important**: Invoke ALL experts in parallel to minimize latency.

4. **Collect and summarize responses**

   Wait for all expert responses. Compile into the output file.

## Output Format

### pr_review/relevance_assessments.md

Create this file with the assessment results:

```markdown
# PR Relevance Assessment

**PR**: #[number] - [title]
**Branch**: [branch_name]
**Date**: [YYYY-MM-DD]

## Changed Files

- path/to/file1.py
- path/to/file2.ts
- ...

## Expert Assessments

### [expert-name-1]
**Status**: RELEVANT / NOT_RELEVANT
**Justification**: [expert's reasoning]
**Relevant files**: [if applicable]

### [expert-name-2]
**Status**: RELEVANT / NOT_RELEVANT
**Justification**: [expert's reasoning]
**Relevant files**: [if applicable]

...

## Summary

**Relevant experts**: [list of expert names marked RELEVANT]
**Next step**: Run `/review_pr.deep_review` with these experts
```

## Quality Criteria

- All experts in `.deepwork/experts/` were invoked in parallel
- Each expert provided a yes/no relevance determination with justification
- Relevant experts are clearly identified for the next step
- PR metadata (number, title, branch) is captured
- Changed files are listed for reference
- When all criteria are met, include `<promise>Quality Criteria Met</promise>` in your response

## Context

This is the first phase of the expert-driven PR review workflow. By checking relevance first, we avoid wasting expert review time on changes outside their domain. The parallel invocation ensures this filtering step completes quickly even with many experts.

The output file serves as input to the `deep_review` step, which will only invoke experts marked as RELEVANT.


### Job Context

A multi-phase workflow for comprehensive pull request review using domain experts.

The workflow operates in three phases:
1. **Relevance Check**: All available experts examine the PR changes in parallel to determine
   if any changes fall within their domain of expertise.
2. **Deep Review**: Experts who found relevant changes perform detailed code review, producing
   written feedback and specific code change suggestions.
3. **Improvement Cycle**: The PR is improved based on feedback, then re-reviewed by the same
   experts. This cycle repeats until all experts report no further feedback or 3 iterations
   are reached.

Produces:
- Relevance assessments from all experts
- Detailed review feedback with code suggestions
- Iteratively improved PR code

Requires: PR branch checked out, `gh` CLI available for PR metadata


## Required Inputs

**User Parameters** - Gather from user before starting:
- **pr_number**: Optional PR number (defaults to current branch's PR)


## Work Branch

Use branch format: `deepwork/review_pr-[instance]-YYYYMMDD`

- If on a matching work branch: continue using it
- If on main/master: create new branch with `git checkout -b deepwork/review_pr-[instance]-$(date +%Y%m%d)`

## Outputs

**Required outputs**:
- `pr_review/relevance_assessments.md`

## Guardrails

- Do NOT skip prerequisite verification if this step has dependencies
- Do NOT produce partial outputs; complete all required outputs before finishing
- Do NOT proceed without required inputs; ask the user if any are missing
- Do NOT modify files outside the scope of this step's defined outputs

## Quality Validation

**Before completing this step, you MUST have your work reviewed against the quality criteria below.**

Use a sub-agent (Haiku model) to review your work against these criteria:

**Criteria (all must be satisfied)**:
1. All experts in .deepwork/experts/ were invoked in parallel
2. Each expert provided a yes/no relevance determination with justification
3. Relevant experts are clearly identified for the next step
**Review Process**:
1. Once you believe your work is complete, spawn a sub-agent using Haiku to review your work against the quality criteria above
2. The sub-agent should examine your outputs and verify each criterion is met
3. If the sub-agent identifies valid issues, fix them
4. Have the sub-agent review again until all valid feedback has been addressed
5. Only mark the step complete when the sub-agent confirms all criteria are satisfied

## On Completion

1. Verify outputs are created
2. Inform user: "full step 1/3 complete, outputs: pr_review/relevance_assessments.md"
3. **Continue workflow**: Use Skill tool to invoke `/review_pr.deep_review`

---

**Reference files**: `.deepwork/jobs/review_pr/job.yml`, `.deepwork/jobs/review_pr/steps/check_relevance.md`