+++
name = "configure_reviews"
description = "Set up DeepWork Reviews — automated code review rules using .deepreview config files"
+++

# Configure DeepWork Reviews

Help the user set up automated code review rules for their project.

## How to Use

1. Read the `README_REVIEWS.md` file in the Claude plugin directory (`plugins/claude/README_REVIEWS.md`) for the complete reference on DeepWork Reviews
2. Look at existing `.deepreview` files in the project that might have something related to what the user wants to do. Reuse existing rules / instructions if possible, including refactoring inline instructions that need to be reused into their own files in the `.deepwork/review` directory
3. Ask the user for any needed clarifications. Skip if you are clear on the need.
4. Create or update `.deepreview` YAML config files in the appropriate locations in their project
5. Test your change. Make a small change that should trigger the affected rule, then call `mcp__deepwork__get_review_instructions` and verify that the output includes text referencing your new rule. Be sure to revert the change.
6. Summarize your changes.
7. Ask the user if they'd like you to run a review now using the `/review` skill to try out the new configuration.

## Important

- Always read `README_REVIEWS.md` first (if you have not in this conversation already) — it contains the full configuration reference, examples, and glob pattern guide
- Help users think about WHERE to place `.deepreview` files (project root for broad rules, subdirectories for scoped rules)
- Write practical review instructions that will produce actionable feedback
- **Minimize reviewer count.** Each review rule runs sequentially in Gemini CLI, so extra rules add execution time. Combine rules into a single rule whenever the joint instructions would not overload the reviewer's context. For example, running ruff and mypy on Python files should be one `python_lint` rule — not two separate rules — because the combined instructions are short and the file set is identical. Only split into separate rules when the instructions are long enough or distinct enough that merging them would degrade review quality.
