---
name: configure-reviews
description: "Set up DeepWork Reviews using .deepreview config files"
---

# Configure DeepWork Reviews

Help the user set up automated review rules for their project.

## How to Use

1. Read `README_REVIEWS.md` in this package for the configuration reference.
2. Inspect existing `.deepreview` files and reuse existing rules or shared instruction files where possible.
3. Ask clarifying questions only when the need is unclear.
4. Create or update `.deepreview` YAML config files in the appropriate project locations.
5. Test the change by making a small triggering change, then call `get_review_instructions` and verify the output references the new rule. Revert the trigger change.
6. Summarize the changes.
7. Ask whether the user wants to run `/review`.

If direct MCP tools are not visible, use the `mcp` proxy tool: search for `get_review_instructions`, then call the returned tool name with JSON-string arguments.

## Important

- Always read `README_REVIEWS.md` first if you have not in this conversation.
- Place `.deepreview` files close to the files they govern.
- Write practical, actionable review instructions.
- Minimize reviewer count. Combine rules when the instructions are short and the file set is identical.
