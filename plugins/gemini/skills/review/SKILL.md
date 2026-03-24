+++
name = "review"
description = "Run DeepWork Reviews on the current branch — review changed files using .deepreview rules"
+++

# DeepWork Review

Run automated code reviews on the current branch based on `.deepreview` config files.

## Routing — Check Before Proceeding

**STOP and redirect** if either of these applies:

- User wants to **configure, create, or modify** review rules (e.g., "add a security review", "set up reviews for our API layer") → use the `configure_reviews` skill instead
- User wants to **add a doc-sync rule** (keep a documentation file in sync with source files) → call `start_workflow` with `job_name="deepwork_reviews"` and `workflow_name="add_document_update_rule"`

Only proceed past this section if the user wants to **run** reviews.

## How to Run

1. First, call `mcp__deepwork__get_configured_reviews` to see what review rules are configured. This returns each rule's name, description, and which `.deepreview` file defines it. If reviewing specific files, pass `only_rules_matching_files` to see only the rules that apply. Share a brief summary of the active rules with the user before proceeding.
   - **If no rules are configured**:
     1. Tell the user there are no `.deepreview` rules set up yet and ask if they'd like you to auto-discover and suggest rules for this project.
     2. If yes, invoke the `/deepwork` skill with the `deepwork_reviews` job's `discover_rules` workflow (which sets up native reviews, skill migration, documentation rules, and language-specific code review).
     3. Stop here — do not proceed with running reviews if there are no rules.
2. Call the `mcp__deepwork__get_review_instructions` tool:
   - **No arguments** to review the current branch's changes (auto-detects via git diff against the main branch).
   - **With `files`** to review only specific files: `mcp__deepwork__get_review_instructions(files=["src/app.py", "src/lib.py"])`. When provided, only reviews whose include/exclude patterns match the given files will be returned. Use this when the user asks to review a particular file or set of files rather than the whole branch.
3. The output will list review tasks to execute **sequentially**. For each numbered review:
   1. Read the instruction file referenced in the review entry.
   2. Follow the instructions to perform the review on the specified files.
   3. Record your findings before moving to the next review.
4. Collect all findings from all reviews.

## Acting on Results

For each finding:

- **Obviously good changes with no downsides** (e.g., fixing a typo, removing an unused import, adding a missing null check): make the change immediately without asking. When in doubt, ask.
- **Everything else** (refactors, style changes, architectural suggestions, anything with trade-offs):
  1. Ask the user about each finding **individually**. Do not group issues together unless they are the same issue occurring in multiple files; otherwise, ask about each issue separately. This lets the user make separate decisions on each item.
  2. For each question, provide several concrete fix approaches as options when there are reasonable alternatives (e.g., "Update the spec to match the code" vs "Update the code to match the spec" vs "Skip").
  3. If a finding seems minor or debatable, include an option to suppress that error in the future — such as a clarification to the rule if it is too narrow.
  4. Be concise — quote the key finding, don't dump the full review.

## Iterate

After making any changes:

1. Call `mcp__deepwork__get_review_instructions` again (with the same `files` argument if the original review was file-scoped, otherwise no arguments).
2. Repeat the cycle (run → act on results → run again) until a clean run — one where all reviews return no findings, or all remaining findings have been explicitly skipped by the user.
3. On subsequent runs, you only need to re-run reviews that had findings last time — skip reviews that were clean.
4. If you made very large changes, consider re-running the full review set.
5. Reviews that already passed are automatically skipped as long as reviewed files remain unchanged.
