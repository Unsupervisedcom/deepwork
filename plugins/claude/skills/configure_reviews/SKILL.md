---
name: configure_reviews
description: "Set up DeepWork Reviews — automated code review rules using .deepreview config files"
---

# Configure DeepWork Reviews

Help the user set up automated code review rules for their project.

## How to Use

1. Read the `README_REVIEWS.md` file in this plugin directory for the complete reference on DeepWork Reviews
2. Look at existing `.deepreview` files in the project that might have something related to what the user wants to do. Reuse existing rules / instructions if possible, including refactoring inline instructions that need to be reused into their own files in the `.deepwork/review` directory
3. Ask any clarifications needed using AskUserQuestion. Skip if you are clear on the need.
4. Create or update `.deepreview` YAML config files in the appropriate locations in their project
5. Test your change. Make a small change that should trigger the affected rule, then run `deepwork review --instructions-for claude` and verify that the text includes output referencing your new rule. Be sure to revert the change.
6. Summarize your changes.

## Important

- Always read `README_REVIEWS.md` first (if you have not in this conversation already) — it contains the full configuration reference, examples, and glob pattern guide
- Help users think about WHERE to place `.deepreview` files (project root for broad rules, subdirectories for scoped rules)
- Write practical review instructions that will produce actionable feedback
