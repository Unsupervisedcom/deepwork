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
3. **While review agents run**, check for a changelog and open PR (see below).
4. Collect the results from all review agents.

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
