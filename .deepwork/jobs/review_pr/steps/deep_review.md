# Deep Expert Review

## Objective

Have relevant domain experts perform thorough code review of the PR changes within their expertise. Each expert produces detailed written feedback with specific suggestions for improvement.

## Task

Invoke only the experts marked as RELEVANT in the previous step to perform detailed code review, producing actionable feedback.

### Process

1. **Read the relevance assessments**

   Read `pr_review/relevance_assessments.md` to identify:
   - Which experts were marked RELEVANT
   - Which files each expert should focus on
   - The PR number and branch

2. **Get the full PR diff**

   ```bash
   gh pr diff
   ```

   Also read the actual file contents for files each expert will review.

3. **Invoke relevant experts for deep review**

   For each RELEVANT expert, use the Task tool to spawn a sub-agent:
   - `subagent_type`: "expert"
   - `agent`: `[expert-name]`
   - `prompt`: Provide the expert with:
     - The full content of files in their domain
     - The diff for those files
     - Instructions to perform thorough code review

   **Expert prompt template**:
   ```
   Perform a detailed code review of these PR changes within your domain of expertise.

   Files to review:
   [full file contents]

   Changes (diff):
   [relevant portion of diff]

   Provide your review in this format:

   ## Summary
   Overall assessment of the changes (1-2 paragraphs)

   ## Issues Found
   For each issue:
   - **File**: path/to/file
   - **Line(s)**: [line numbers]
   - **Severity**: Critical / Major / Minor / Suggestion
   - **Issue**: Description of the problem
   - **Suggestion**: How to fix it

   ## Code Suggestions
   Specific code changes you recommend (include before/after snippets)

   ## Approval Status
   - APPROVED: No blocking issues
   - CHANGES_REQUESTED: Blocking issues must be addressed
   - COMMENTS: Suggestions only, no blockers
   ```

   **Note**: Invoke relevant experts in parallel for efficiency.

4. **Collect expert reviews**

   Wait for all expert reviews to complete. Save each to their dedicated review file.

5. **Create consolidated summary**

   After all reviews complete, summarize across experts:
   - Total issues by severity
   - Key themes across reviews
   - Overall approval status

## Output Format

### pr_review/[expert_name]/review.md

Create one file per relevant expert:

```markdown
# [Expert Name] Review

**PR**: #[number]
**Date**: [YYYY-MM-DD]
**Reviewer**: [expert-name] expert

## Summary

[Expert's overall assessment]

## Issues Found

### Issue 1
- **File**: path/to/file.py
- **Line(s)**: 45-52
- **Severity**: Major
- **Issue**: [Description]
- **Suggestion**: [How to fix]

### Issue 2
...

## Code Suggestions

### Suggestion 1: [Brief title]

**File**: path/to/file.py

Before:
```python
# problematic code
```

After:
```python
# suggested improvement
```

**Rationale**: [Why this change improves the code]

...

## Approval Status

[APPROVED / CHANGES_REQUESTED / COMMENTS]

[Additional notes on approval status]
```

### pr_review/review_summary.md (optional but recommended)

```markdown
# PR Review Summary

**PR**: #[number]
**Date**: [YYYY-MM-DD]

## Expert Reviews

| Expert | Status | Critical | Major | Minor |
|--------|--------|----------|-------|-------|
| [name] | CHANGES_REQUESTED | 0 | 2 | 3 |
| [name] | APPROVED | 0 | 0 | 1 |

## Key Themes

- [Theme 1 appearing across multiple reviews]
- [Theme 2]

## Overall Status

[CHANGES_REQUESTED if any expert requested changes, otherwise APPROVED]

## Next Steps

[If changes requested]: Run `/review_pr.improve_and_rereview` to address feedback
[If approved]: PR is ready to merge
```

## Quality Criteria

- Only experts marked as relevant were invoked
- Each expert produced written feedback in their review file
- Specific code change suggestions are included where applicable
- Issues include file, line numbers, severity, and suggestions
- Approval status is clearly stated by each expert
- When all criteria are met, include `<promise>Quality Criteria Met</promise>` in your response

## Context

This is the second phase of the expert-driven PR review workflow. Deep review only happens after relevance filtering to ensure expert time is well-spent. Each expert reviews independently, bringing their domain knowledge to identify issues others might miss.

The review files serve as input to the `improve_and_rereview` step if changes are requested. If all experts approve, the PR can proceed to merge.
