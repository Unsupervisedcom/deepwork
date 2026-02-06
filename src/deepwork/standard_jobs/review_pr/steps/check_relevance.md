# Check Expert Relevance

## Objective

Invoke all available experts in parallel to determine which ones have relevant expertise for the PR changes. This filtering step ensures only applicable experts spend time on detailed review.

## Task

Assess which domain experts can meaningfully contribute to reviewing the current PR by having each expert examine the changes and report their relevance.

### Process

1. **Get PR metadata**

   Get basic PR info for the output file:
   ```bash
   gh pr view --json number,title,headRefName
   ```

   This is needed for the output file header. The diff and file list will be
   embedded directly in expert prompts using inline command expansion.

2. **Discover available experts**

   List all experts in the project:
   ```bash
   ls -1 .deepwork/experts/
   ```

   Read each expert's `discovery_description` from their `expert.yml` to understand their domain.

3. **Invoke experts in parallel**

   For each expert, use the Task tool to spawn a sub-agent:
   - `subagent_type`: "experts"
   - `prompt`: Use the template below with inline command expansion

   **IMPORTANT - Use inline bash completion for efficiency**:

   Use `$(command)` syntax in the prompt to embed command output directly when
   the sub-agent is spawned. This avoids reading large diffs into the main
   conversation context.

   **Expert prompt template** (note the `$(...)` syntax):
   ```
   Review this PR to determine if the changes are relevant to your domain of expertise.

   ## Changed Files

   $(gh pr diff --name-only)

   ## Diff Summary (first 200 lines)

   $(gh pr diff | head -200)

   ## Your Task

   Based on your specific domain knowledge, respond with:
   1. RELEVANT or NOT_RELEVANT
   2. Brief justification (1-2 sentences) explaining why this does or does not fall within your expertise
   3. If relevant, which specific files/changes you can review from your expert perspective
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
