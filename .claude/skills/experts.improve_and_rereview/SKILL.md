---
name: experts.improve_and_rereview
description: "Apply expert feedback and re-run reviews until no further feedback or 3 iterations"
user-invocable: false

---

# experts.improve_and_rereview

**Step 3/3** in **review_pr** workflow

> Coordinate expert-driven PR review with iterative improvement cycles

## Prerequisites (Verify First)

Before proceeding, confirm these steps are complete:
- `/experts.deep_review`

## Instructions

**Goal**: Apply expert feedback and re-run reviews until no further feedback or 3 iterations

# Improve and Re-Review

## Objective

Iteratively improve the PR based on expert feedback, then re-run expert reviews until all feedback is addressed or a maximum of 3 iterations is reached.

## Task

Apply improvements based on expert review feedback, get user approval, then have the same experts re-review. Repeat until experts report no further issues.

### Process

1. **Read expert reviews**

   Read all review files from `pr_review/[expert_name]/review.md` to understand:
   - What issues each expert identified within their domain
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
   - Use the Task tool with `subagent_type`: "experts"
   - Provide the updated file contents and diff
   - Ask them to re-review from their domain perspective

   **Expert re-review prompt**:
   ```
   This is a re-review of PR changes after addressing your previous feedback.

   Your domain: [brief description from discovery_description]

   Previous issues you raised within your domain:
   [list their issues from last review]

   Changes made:
   [summary of changes applied]

   Updated files:
   [full file contents]

   From your expert perspective, please review and report:
   1. Are your previous domain-specific issues addressed?
   2. Any new issues introduced within your domain?
   3. Updated approval status for your domain
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

**IMPORTANT**: List ALL issues from expert reviews - none may be silently omitted.

### From [expert-name]
| Issue | Severity | Status | Resolution |
|-------|----------|--------|------------|
| [Issue 1] | Major | FIXED | [How it was fixed] |
| [Issue 2] | Minor | SKIPPED | [Explicit reason: false positive / deferred / user declined] |
| [Issue 3] | Suggestion | FIXED | [How it was fixed] |

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

## Issue Resolution Summary

| Expert | Total Issues | Fixed | Skipped (with reason) |
|--------|--------------|-------|----------------------|
| [name] | 4 | 3 | 1 (false positive) |
| [name] | 2 | 2 | 0 |

## Unresolved Items (if any)

For each unresolved item, document:
- Issue description
- Why it wasn't fixed
- Plan for addressing (if applicable)

## Next Steps

[What to do with the PR now]
```

## Quality Criteria

- **Complete issue accounting**: Every issue from expert reviews is either:
  - Fixed (with description of the fix), OR
  - Explicitly skipped with documented justification (e.g., "false positive", "deferred to future PR", "user declined")
- **No silent omissions**: The feedback summary must list ALL issues from expert reviews, not a subset
- User approved suggested improvements before they were applied
- Re-reviews were run after each improvement iteration
- Cycle stopped when all experts reported no further feedback OR after 3 iterations
- Final iteration summary documents the outcome for every issue
- All changes are tracked and attributed to expert feedback

## Context

This is the final phase of the expert-driven PR review workflow. The iterative approach ensures feedback is actually addressed, not just acknowledged. The 3-iteration limit prevents infinite loops while allowing reasonable time for improvements.

User approval at each step keeps humans in control - experts suggest, but humans decide what changes to make. This respects developer autonomy while benefiting from expert review.


### Workflow Context

Orchestrate a comprehensive PR review using domain experts:
1. Check which experts have relevant expertise for the PR changes
2. Have relevant experts perform deep code review
3. Iteratively improve the PR based on feedback until all experts approve


## Required Inputs


**Files from Previous Steps** - Read these first:
- `pr_review/{expert_name}/review.md` (from `deep_review`)

## Work Branch

Use branch format: `deepwork/experts-review_pr-[instance]-YYYYMMDD`

- If on a matching work branch: continue using it
- If on main/master: create new branch with `git checkout -b deepwork/experts-review_pr-[instance]-$(date +%Y%m%d)`

## Outputs

**Required outputs**:
- `pr_review/iteration_{n}/summary.md`
- `pr_review/final_summary.md`

## Guardrails

- Do NOT skip prerequisite verification if this step has dependencies
- Do NOT produce partial outputs; complete all required outputs before finishing
- Do NOT proceed without required inputs; ask the user if any are missing
- Do NOT modify files outside the scope of this step's defined outputs

## On Completion

1. Verify outputs are created
2. Inform user: "review_pr step 3/3 complete, outputs: pr_review/iteration_{n}/summary.md, pr_review/final_summary.md"
3. **review_pr workflow complete**: All steps finished. Consider creating a PR to merge the work branch.

---

**Reference files**: `.deepwork/experts/experts/workflows/review_pr/workflow.yml`, `.deepwork/experts/experts/workflows/review_pr/steps/improve_and_rereview.md`