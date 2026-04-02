---
name: configure_reviews
description: "Set up DeepWork Reviews - automated code review rules using .deepreview config files"
---

# Configure DeepWork Reviews

Help the user set up automated code review rules for their project.

## How to Use

1. Read the `README_REVIEWS.md` file in this plugin directory for the complete reference on DeepWork Reviews
2. Look at existing `.deepreview` files in the project that might already cover part of what the user wants. Reuse existing rules and instructions when possible, including refactoring reusable inline instructions into `.deepwork/review/`
3. Ask any clarifications needed using AskUserQuestion. Skip if you are already clear on the need.
4. Create or update `.deepreview` YAML config files in the appropriate locations in the project
5. Test your change. Make a small change that should trigger the affected rule, then call `get_review_instructions` and verify that the output includes text referencing your new rule. Be sure to revert the change.
6. Summarize your changes.
7. Ask the user if they'd like you to run a review now using the `review` skill to try out the new configuration.

## Important

- Always read `README_REVIEWS.md` first if you have not in this conversation already - it contains the full configuration reference, examples, and glob pattern guide
- Help users think about where to place `.deepreview` files (project root for broad rules, subdirectories for scoped rules)
- Write practical review instructions that will produce actionable feedback
- **Minimize reviewer count.** Each review rule spawns a separate sub-agent with material overhead. Combine rules into a single rule whenever the joint instructions would not overload the reviewer's context.
