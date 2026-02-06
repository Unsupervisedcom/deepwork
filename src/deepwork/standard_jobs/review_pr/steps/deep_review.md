# Deep Expert Review

## Objective

Have relevant domain experts perform thorough code review of the PR changes **specifically within their area of expertise**. Each expert produces detailed written feedback with specific suggestions for improvement, drawing on their domain knowledge.

## Task

Invoke only the experts marked as RELEVANT in the previous step to perform detailed code review, producing actionable feedback focused on their specific domain.

### Process

1. **Read the relevance assessments**

   Read `pr_review/relevance_assessments.md` to identify:
   - Which experts were marked RELEVANT
   - Which specific files each expert identified as relevant to their domain
   - The PR number and branch

2. **Invoke relevant experts for deep review**

   For each RELEVANT expert, use the Task tool to spawn a sub-agent:
   - `subagent_type`: "experts"
   - `prompt`: Use the template below with inline command expansion

   **IMPORTANT - Use inline bash completion for efficiency**:

   Instead of reading the diff yourself and passing it to each expert, use `$(command)`
   syntax in the prompt. This embeds the command output directly when the sub-agent
   is spawned, avoiding token overhead in the main conversation.

   **Expert prompt template** (note the `$(...)` syntax):
   ```
   Perform a detailed code review of these PR changes **focusing specifically on your domain of expertise**.

   IMPORTANT: Only comment on aspects that fall within your area of expertise. Do not provide
   general code review feedback on things outside your domain - other experts will cover those areas.
   Use your specialized knowledge to identify issues that a generalist reviewer might miss.

   Your domain: [brief description from discovery_description]

   Files you identified as relevant to your domain:
   [list from relevance assessment]

   ## PR Diff

   $(gh pr diff)

   ## Your Task

   Review the diff above, focusing ONLY on files and changes relevant to your domain.
   Ignore changes outside your expertise - other experts will cover those.

   From your expert perspective, provide your review in this format:

   ## Summary
   Overall assessment of the changes as they relate to your domain (1-2 paragraphs).
   What is this PR doing in terms of your area of expertise?

   ## Issues Found
   For each issue within your domain:
   - **File**: path/to/file
   - **Line(s)**: [line numbers]
   - **Severity**: Critical / Major / Minor / Suggestion
   - **Issue**: Description of the problem from your expert perspective
   - **Suggestion**: How to fix it, drawing on your domain knowledge

   ## Code Suggestions
   Specific code changes you recommend based on your expertise (include before/after snippets).
   Explain why this change is better from your domain's perspective.

   ## Approval Status
   - APPROVED: No blocking issues within your domain
   - CHANGES_REQUESTED: Blocking issues in your domain must be addressed
   - COMMENTS: Suggestions only within your domain, no blockers
   ```

   **Note**: Invoke relevant experts in parallel for efficiency.

3. **Collect expert reviews**

   Wait for all expert reviews to complete. Save each to their dedicated review file.

4. **Create consolidated summary**

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

[Expert's overall assessment from their domain perspective]

## Issues Found

### Issue 1
- **File**: path/to/file.py
- **Line(s)**: 45-52
- **Severity**: Major
- **Issue**: [Description from expert perspective]
- **Suggestion**: [How to fix, using domain knowledge]

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

**Rationale**: [Why this change improves the code from this expert's perspective]

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

| Expert | Domain | Status | Critical | Major | Minor |
|--------|--------|--------|----------|-------|-------|
| [name] | [domain] | CHANGES_REQUESTED | 0 | 2 | 3 |
| [name] | [domain] | APPROVED | 0 | 0 | 1 |

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
- Feedback is focused on each expert's specific domain of expertise
- Specific code change suggestions are included where applicable
- Issues include file, line numbers, severity, and suggestions
- Approval status is clearly stated by each expert
- When all criteria are met, include `<promise>Quality Criteria Met</promise>` in your response

## Context

This is the second phase of the expert-driven PR review workflow. Deep review only happens after relevance filtering to ensure expert time is well-spent. Each expert reviews independently from their unique domain perspective, bringing specialized knowledge to identify issues that generalist reviewers might miss.

The key to effective expert review is **focus**: each expert should only comment on aspects within their domain, trusting that other experts will cover other areas. This produces higher-quality, more actionable feedback than generic reviews.

The review files serve as input to the `improve_and_rereview` step if changes are requested. If all experts approve, the PR can proceed to merge.
