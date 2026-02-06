---
name: Review PR job efficiency improvements
last_updated: 2026-02-01
summarized_result: |
  The review_pr job used excessive tokens by sending full file contents to all
  experts instead of using the per-expert file segmentation from the relevance
  step. Also, quality validation sub-agents add overhead that may not be needed
  for simple checklist verification.
---

## Context

During execution of the `/review_pr` job on PR #192, the workflow completed successfully but used significantly more tokens and time than necessary.

## Problems Identified

### 1. Ignored per-expert file segmentation

The `check_relevance` step correctly identified which files each expert should review:
- deepwork-jobs: schema, parser, generator, CLI, templates, tests
- experts: same files (significant overlap in this case)

But the `deep_review` step ignored this segmentation and sent ALL files to BOTH experts. Each expert received ~1000+ lines of code when they should have received only their relevant subset.

### 2. Full file contents vs. targeted excerpts

Experts received full file contents when often they only needed:
- The diff (what changed)
- Specific sections relevant to their domain
- Perhaps function signatures for context

Sending full test files (500+ lines) to review production code changes is wasteful.

### 3. Quality validation sub-agent overhead

Each step spawned a Haiku sub-agent purely to verify a checklist of 3-5 criteria. This adds:
- Network round-trip latency
- Token overhead for the sub-agent context
- Complexity

For simple boolean criteria checks, the main agent could self-verify.

### 4. Redundant data fetching

The PR diff was fetched separately in both `check_relevance` and `deep_review` steps instead of being passed along or cached.

## Recommendations

### For step instructions:

1. **Use inline bash completion `$(command)`**: Instead of the orchestrating agent reading
   data and passing it to sub-agents, embed commands directly in prompts:
   ```
   $(gh pr diff)
   $(gh pr diff --name-only)
   ```
   This executes when the sub-agent spawns, avoiding token overhead in the main conversation.

2. **Use relevance segmentation**: The deep_review step should explicitly use the "Relevant files" list from each expert's relevance assessment to scope what content is sent to each expert.

3. **Prefer diffs over full files**: For review tasks, send the diff plus minimal context (function signatures, class definitions) rather than entire files.

4. **Skip validation sub-agents for simple criteria**: If quality criteria are simple boolean checks (e.g., "output file exists", "all experts invoked"), the main agent can verify these directly.

### For job design:

1. **Let sub-agents fetch their own data**: Using `$(command)` in prompts means sub-agents
   get fresh data directly without the orchestrator reading and forwarding it.

2. **Consider expert-specific prompts**: Generate different prompts for each expert containing only their relevant files, rather than one massive prompt for all.

## Key Takeaway

The experts system's value comes from specialized, focused review. Sending all content to all experts defeats this purpose and wastes tokens. Job steps that invoke multiple experts should segment the workload based on each expert's declared relevance.
