---
name: review
description: "Run DeepWork Reviews on the current branch — review changed files using .deepreview rules"
---

# DeepWork Review

Run automated code reviews on the current branch based on `.deepreview` config files.

## Routing

If the user is asking to **configure, create, or modify** review rules (e.g., "add a security review", "set up reviews for our API layer"), use the `configure_reviews` skill instead. This skill is for **running** reviews.

## How to Run

1. First, call `mcp__deepwork__get_configured_reviews` to see what review rules are configured. This returns each rule's name, description, and which `.deepreview` file defines it. If reviewing specific files, pass `only_rules_matching_files` to see only the rules that apply. Share a brief summary of the active rules with the user before proceeding.
2. Call the `mcp__deepwork__get_review_instructions` tool:
   - No arguments needed to review the current branch's changes (detects via git diff).
   - To review specific files, pass `files`: `mcp__deepwork__get_review_instructions(files=["src/app.py", "src/lib.py"])`
3. The output will list review tasks to invoke in parallel. Each task has `name`, `description`, `subagent_type`, and `prompt` fields — these map directly to the Task tool parameters. Launch all of them as parallel Task agents.
4. Collect the results from all review agents.

## Acting on Results

For each finding from the review agents:

- **Obviously good changes with no downsides** (e.g., fixing a typo, removing an unused import, adding a missing null check): make the change immediately without asking.
- **Everything else** (refactors, style changes, architectural suggestions, anything with trade-offs): use AskUserQuestion to ask the user about each finding **individually** — one question per finding. Do NOT batch unrelated findings into a single question. This lets the user make separate decisions on each item. For each question, provide several concrete fix approaches as options when there are reasonable alternatives (e.g., "Update the spec to match the code" vs "Update the code to match the spec" vs "Skip"). Be concise — quote the key finding, don't dump the full review.

## Iterate

After making any changes, run the review again by calling `mcp__deepwork__get_review_instructions` with no arguments.

Repeat the full cycle (run → act on results → run again) until a clean run produces no further actionable findings. Note that you don't have to run EVERY task the above outputs after the first time - you can just run the ones that match up to ones that had feedback last time. If you made very large changes, it may be a good idea to run the full reviews set.
