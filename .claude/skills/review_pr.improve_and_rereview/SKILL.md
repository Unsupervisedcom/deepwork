---
name: review_pr.improve_and_rereview
description: "Applies expert feedback to improve the PR, then re-runs expert reviews. Cycles until no further feedback or 3 iterations. Use after deep review completes."
user-invocable: false

---

# review_pr.improve_and_rereview

**Step 3/3** in **full** workflow

> Full PR review: relevance check, deep review, and improvement cycles

> Coordinates expert-driven PR review with iterative improvement cycles until all feedback is addressed.

## Prerequisites (Verify First)

Before proceeding, confirm these steps are complete:
- `/review_pr.deep_review`

## Instructions

**Goal**: Applies expert feedback to improve the PR, then re-runs expert reviews. Cycles until no further feedback or 3 iterations. Use after deep review completes.

# Improve and Re-Review

## Objective

Iteratively improve the PR based on expert feedback, then re-run expert reviews until all feedback is addressed or a maximum of 3 iterations is reached.

## Task

Apply improvements based on expert review feedback, get user approval, then have the same experts re-review. Repeat until experts report no further issues.

### Process

1. **Read expert reviews**

   Read all review files from `pr_review/[expert_name]/review.md` to understand:
   - What issues each expert identified
   - What code changes they suggested
   - Their approval status

2. **Consolidate and prioritize feedback**

   Group feedback by:
   - **Critical/Major issues**: Must be addressed
   - **Minor issues**: Should be addressed
   - **Suggestions**: Nice to have

   Present a summary to the user:
   ```
   ## Feedback Summary

   ### Critical/Major Issues (must fix)
   1. [Issue from expert X]: [description]
   2. [Issue from expert Y]: [description]

   ### Minor Issues (should fix)
   1. [Issue]: [description]

   ### Suggestions (optional)
   1. [Suggestion]: [description]

   ## Proposed Changes

   I recommend making these changes:
   1. [Change 1]: [what and why]
   2. [Change 2]: [what and why]

   Do you approve these changes?
   ```

3. **Get user approval**

   **IMPORTANT**: Do not make changes without explicit user approval.

   Wait for user to:
   - Approve the proposed changes
   - Modify which changes to apply
   - Skip certain suggestions with justification

4. **Apply approved changes**

   Make the code changes the user approved:
   - Use the Edit tool to modify files
   - Follow the expert's code suggestions where applicable
   - Ensure changes are coherent and don't break other code

5. **Re-run expert reviews**

   After applying changes, invoke the same relevant experts again:
   - Use the Task tool with `subagent_type`: "expert"
   - Provide the updated file contents and diff
   - Ask them to review the changes and identify any remaining issues

   **Expert re-review prompt**:
   ```
   This is a re-review of PR changes after addressing your previous feedback.

   Previous issues you raised:
   [list their issues from last review]

   Changes made:
   [summary of changes applied]

   Updated files:
   [full file contents]

   Please review and report:
   1. Are your previous issues addressed?
   2. Any new issues introduced?
   3. Updated approval status
   ```

6. **Evaluate results**

   After re-review:
   - If ALL experts now approve (or only have minor suggestions): **Stop - review complete**
   - If any expert still has Critical/Major issues: **Continue to next iteration**
   - If this was iteration 3: **Stop - maximum iterations reached**

7. **Create iteration summary**

   Document what happened in this iteration.

### Iteration Loop

Repeat steps 2-7 until:
- All experts report no further blocking feedback, OR
- 3 iterations have been completed

## Output Format

### pr_review/iteration_[n]/summary.md

Create one file per iteration:

```markdown
# Iteration [n] Summary

**Date**: [YYYY-MM-DD]
**Iteration**: [n] of 3 max

## Feedback Addressed

### From [expert-name]
- [Issue 1]: [How it was addressed]
- [Issue 2]: [How it was addressed / Why it was skipped]

### From [expert-name-2]
...

## Changes Made

1. **[file.py]**: [What was changed]
2. **[other.ts]**: [What was changed]

## Re-Review Results

| Expert | Previous Status | New Status | Remaining Issues |
|--------|-----------------|------------|------------------|
| [name] | CHANGES_REQUESTED | APPROVED | 0 |
| [name] | CHANGES_REQUESTED | COMMENTS | 1 minor |

## Outcome

[One of:]
- **COMPLETE**: All experts approved. PR ready to merge.
- **CONTINUING**: [n] blocking issues remain. Proceeding to iteration [n+1].
- **MAX_ITERATIONS**: Reached 3 iterations. [n] issues remain unresolved.

## Remaining Issues (if any)

1. [Issue]: [Why not addressed / Plan for addressing]
```

### Final Summary (after last iteration)

Update or create `pr_review/final_summary.md`:

```markdown
# PR Review Final Summary

**PR**: #[number]
**Total Iterations**: [n]
**Final Status**: [APPROVED / PARTIAL / UNRESOLVED]

## Review Timeline

| Iteration | Date | Issues Addressed | Remaining |
|-----------|------|------------------|-----------|
| 1 | [date] | 5 | 3 |
| 2 | [date] | 3 | 0 |

## Expert Final Status

| Expert | Final Status |
|--------|--------------|
| [name] | APPROVED |
| [name] | APPROVED |

## Key Improvements Made

1. [Improvement 1]
2. [Improvement 2]

## Unresolved Items (if any)

[List any items not addressed and why]

## Next Steps

[What to do with the PR now]
```

## Quality Criteria

- User approved suggested improvements before they were applied
- Re-reviews were run after each improvement iteration
- Cycle stopped when all experts reported no further feedback OR after 3 iterations
- Final iteration summary documents the outcome
- All changes are tracked and attributed to expert feedback
- When all criteria are met, include `<promise>Quality Criteria Met</promise>` in your response

## Context

This is the final phase of the expert-driven PR review workflow. The iterative approach ensures feedback is actually addressed, not just acknowledged. The 3-iteration limit prevents infinite loops while allowing reasonable time for improvements.

User approval at each step keeps humans in control - experts suggest, but humans decide what changes to make. This respects developer autonomy while benefiting from expert review.


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


**Files from Previous Steps** - Read these first:
- `pr_review/[expert_name]/review.md` (from `deep_review`)

## Work Branch

Use branch format: `deepwork/review_pr-[instance]-YYYYMMDD`

- If on a matching work branch: continue using it
- If on main/master: create new branch with `git checkout -b deepwork/review_pr-[instance]-$(date +%Y%m%d)`

## Outputs

**Required outputs**:
- `pr_review/iteration_[n]/summary.md`

## Guardrails

- Do NOT skip prerequisite verification if this step has dependencies
- Do NOT produce partial outputs; complete all required outputs before finishing
- Do NOT proceed without required inputs; ask the user if any are missing
- Do NOT modify files outside the scope of this step's defined outputs

## Quality Validation

**Before completing this step, you MUST have your work reviewed against the quality criteria below.**

Use a sub-agent (Haiku model) to review your work against these criteria:

**Criteria (all must be satisfied)**:
1. User approved suggested improvements before they were applied
2. Re-reviews were run after each improvement iteration
3. Cycle stopped when all experts reported no further feedback OR after 3 iterations
4. Final iteration summary documents the outcome
**Review Process**:
1. Once you believe your work is complete, spawn a sub-agent using Haiku to review your work against the quality criteria above
2. The sub-agent should examine your outputs and verify each criterion is met
3. If the sub-agent identifies valid issues, fix them
4. Have the sub-agent review again until all valid feedback has been addressed
5. Only mark the step complete when the sub-agent confirms all criteria are satisfied

## On Completion

1. Verify outputs are created
2. Inform user: "full step 3/3 complete, outputs: pr_review/iteration_[n]/summary.md"
3. **full workflow complete**: All steps finished. Consider creating a PR to merge the work branch.

---

**Reference files**: `.deepwork/jobs/review_pr/job.yml`, `.deepwork/jobs/review_pr/steps/improve_and_rereview.md`