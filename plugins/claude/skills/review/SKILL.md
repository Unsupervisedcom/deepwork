---
name: review
description: "Run DeepWork Reviews on the current branch — review changed files using .deepreview rules"
---

# DeepWork Review

Run automated code reviews on the current branch based on `.deepreview` config files.

## Routing — Check Before Proceeding

**STOP and redirect** if either of these applies:

- User wants to **configure, create, or modify** review rules (e.g., "add a security review", "set up reviews for our API layer") → use the `configure_reviews` skill instead
- User wants to **add a doc-sync rule** (keep a documentation file in sync with source files) → run the `/deepwork` skill with the `deepwork_reviews` job's `add_document_update_rule` workflow

Only proceed past this section if the user wants to **run** reviews.

## How to Run

1. First, call `mcp__deepwork__get_configured_reviews` to see what review rules are configured. This returns each rule's name, description, and which `.deepreview` file defines it. If reviewing specific files, pass `only_rules_matching_files` to see only the rules that apply. Share a brief summary of the active rules with the user before proceeding.
   - **If no rules are configured**: Use AskUserQuestion to tell the user there are no `.deepreview` rules set up yet, and ask if they'd like the agent to auto-discover and suggest rules for this project. If they say yes, invoke the `/deepwork` skill with the `deepwork_reviews` job's `discover_rules` workflow (which sets up native reviews, skill migration, documentation rules, and language-specific code review). Stop here — do not proceed with running reviews if there are no rules.
2. Call the `mcp__deepwork__get_review_instructions` tool:
   - No arguments needed to review the current branch's changes (detects via git diff).
   - To review specific files, pass `files`: `mcp__deepwork__get_review_instructions(files=["src/app.py", "src/lib.py"])`
3. The output will list review tasks to invoke in parallel. Each task has `name`, `description`, `subagent_type`, and `prompt` fields — these map directly to the Task tool parameters. Launch all of them as parallel Task agents.
4. Collect the results from all review agents.

## Acting on Results

For each finding from the review agents:

- **Obviously good changes with no downsides** (e.g., fixing a typo, removing an unused import, adding a missing null check): make the change immediately without asking. When in doubt, ask.
- **Everything else** (refactors, style changes, architectural suggestions, anything with trade-offs): use AskUserQuestion to ask the user about each finding **individually** — one question per finding. Do NOT batch unrelated findings into a single question. This lets the user make separate decisions on each item. For each question, provide several concrete fix approaches as options when there are reasonable alternatives (e.g., "Update the spec to match the code" vs "Update the code to match the spec" vs "Skip"). Be concise — quote the key finding, don't dump the full review.

## Iterate

After making any changes, run the review again by calling `mcp__deepwork__get_review_instructions` with no arguments.

Repeat the full cycle (run → act on results → run again) until a clean run produces no further actionable findings. A clean run is one where all review agents return no findings, or all remaining findings have been explicitly skipped by the user. Note that you don't have to run EVERY task the above outputs after the first time - you can just run the ones that match up to ones that had feedback last time. If you made very large changes, it may be a good idea to run the full reviews set. Subsequent runs automatically skip reviews that already passed, as long as the reviewed files remain unchanged.
