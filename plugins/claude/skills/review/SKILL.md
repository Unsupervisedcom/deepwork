---
name: review
description: "Run DeepWork Reviews on the current branch — review changed files using .deepreview rules"
---

# DeepWork Review

Run automated code reviews on the current branch based on `.deepreview` config files.

## Routing — Check Before Proceeding

**STOP and redirect** if either of these applies:

- User wants to **configure, create, or modify** review rules (e.g., "add a security review", "set up reviews for our API layer") → use the `configure_reviews` skill instead
- User wants to **add a doc-sync rule** (keep a documentation file in sync with source files) → call `start_workflow` with `job_name="deepwork_reviews"` and `workflow_name="add_document_update_rule"`

Only proceed past this section if the user wants to **run** reviews.

## How to Run

1. Call the `mcp__deepwork__get_review_instructions` tool directly:
   - **No arguments** to review the current branch's changes (auto-detects via git diff against the main branch).
   - **With `files`** to review only specific files: `mcp__deepwork__get_review_instructions(files=["src/app.py", "src/lib.py"])`. When provided, only reviews whose include/exclude patterns match the given files will be returned. Use this when the user asks to review a particular file or set of files rather than the whole branch.
   - **If the result says no rules are configured**: Ask the user if they'd like to auto-discover and set up rules. If yes, invoke the `/deepwork` skill with the `deepwork_reviews` job's `discover_rules` workflow. Stop here — do not proceed with running reviews if there are no rules.
2. The output will list review tasks to invoke in parallel. Each task has `name`, `description`, `subagent_type`, and `prompt` fields — these map directly to the Task tool parameters. Launch all of them as parallel Task agents.
3. **Alongside the review agents**, also launch the three code-quality agents below (see "Code Quality Agents"). Launch them in the same parallel batch as the review tasks from step 2.
4. **While all agents run**, check for a changelog and open PR (see below).
5. Collect the results from all agents (both review tasks and code-quality agents).

## Code Quality Agents

Run `git diff` against the main branch to get the full diff. Pass the diff to each of these three agents, launched in parallel alongside the review tasks above. Each agent should be a `general-purpose` subagent.

### Agent 1: Code Reuse

For each change:
1. Search for existing utilities and helpers that could replace newly written code. Look for similar patterns elsewhere in the codebase — common locations are utility directories, shared modules, and files adjacent to the changed ones.
2. Flag any new function that duplicates existing functionality. Suggest the existing function to use instead.
3. Flag any inline logic that could use an existing utility — hand-rolled string manipulation, manual path handling, custom environment checks, ad-hoc type guards, and similar patterns are common candidates.

### Agent 2: Code Quality

Review the same changes for hacky patterns:
1. Redundant state: state that duplicates existing state, cached values that could be derived, observers/effects that could be direct calls
2. Parameter sprawl: adding new parameters to a function instead of generalizing or restructuring existing ones
3. Copy-paste with slight variation: near-duplicate code blocks that should be unified with a shared abstraction
4. Leaky abstractions: exposing internal details that should be encapsulated, or breaking existing abstraction boundaries
5. Stringly-typed code: using raw strings where constants, enums (string unions), or branded types already exist in the codebase
6. Unnecessary comments: comments explaining WHAT the code does (well-named identifiers already do that), narrating the change, or referencing the task/caller — delete; keep only non-obvious WHY (hidden constraints, subtle invariants, workarounds)

### Agent 3: Efficiency

Review the same changes for efficiency:
1. Unnecessary work: redundant computations, repeated file reads, duplicate network/API calls, N+1 patterns
2. Missed concurrency: independent operations run sequentially when they could run in parallel
3. Hot-path bloat: new blocking work added to startup or per-request/per-render hot paths
4. Recurring no-op updates: state/store updates inside polling loops, intervals, or event handlers that fire unconditionally — add a change-detection guard so downstream consumers aren't notified when nothing changed
5. Unnecessary existence checks: pre-checking file/resource existence before operating (TOCTOU anti-pattern) — operate directly and handle the error
6. Memory: unbounded data structures, missing cleanup, event listener leaks
7. Overly broad operations: reading entire files when only a portion is needed, loading all items when filtering for one

## Changelog & PR Description Check

Run this concurrently with the review agents (step 2 above) — don't wait for reviews to finish first.

1. Check if the project has a changelog file (e.g., `CHANGELOG.md`, `CHANGELOG`, `CHANGES.md`).
2. If a changelog exists and there are commits on the current branch beyond the main branch:
   - Read the changelog and the branch's commit log (`git log main..HEAD --oneline`).
   - Verify the changelog's unreleased/current section accurately reflects what the branch does. If entries are missing, outdated, or inaccurate, update the changelog.
3. If a PR is open for the current branch (check with `gh pr view`):
   - If you updated the changelog, also verify the PR description matches. Update it with `gh pr edit` if needed.
   - If the changelog was already accurate, skip the PR description check.

## Acting on Results

For each finding from the review agents:

- **Obviously good changes with no downsides** (e.g., fixing a typo, removing an unused import, adding a missing null check): make the change immediately without asking. When in doubt, ask.
- **Everything else** (refactors, style changes, architectural suggestions, anything with trade-offs):
  1. Use AskUserQuestion to ask the user about each finding **individually**. Do not group issues together unless they are the same issue occurring in multiple files; otherwise, use AskUserQuestion to ask about each issue separately. This lets the user make separate decisions on each item.
  2. For each question, provide several concrete fix approaches as options when there are reasonable alternatives (e.g., "Update the spec to match the code" vs "Update the code to match the spec" vs "Skip").
  3. If a finding seems minor or debatable, include an option to suppress that error in the future — such as a clarification to the rule if it is too narrow, or a comment on the offending content if comments work in that context.
  4. Be concise — quote the key finding, don't dump the full review.

When a finding is dismissed (user chooses "Skip" or you determine it's not actionable for this PR), call `mcp__deepwork__mark_review_as_passed` with the review's ID so it won't re-run on subsequent iterations.

## Iterate

After making any changes:

1. Call `mcp__deepwork__get_review_instructions` with `files` set to **only the files you edited** during this iteration. This scopes the re-review to your changes rather than re-reviewing the entire branch.
2. Repeat the cycle (run → act on results → run again) until a clean run — one where all review agents return no findings, or all remaining findings have been explicitly skipped by the user.
3. On subsequent runs, you only need to re-run tasks that had findings last time — skip tasks that were clean.
4. Reviews that already passed are automatically skipped as long as reviewed files remain unchanged.
