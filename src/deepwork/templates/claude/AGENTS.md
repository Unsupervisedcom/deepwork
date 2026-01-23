# Claude Templates - Agent Notes

Notes for AI agents working on Claude Code jinja templates.

## Prompt-Based Hooks

When writing prompt-based hooks (e.g., Stop hooks with `type: prompt`):

- **Do NOT include instructions on how to return responses** (e.g., "respond with JSON", "return `{"ok": true}`"). Claude Code's internal instructions already specify the expected response format for prompt hooks.
- Adding redundant response format instructions can cause conflicts or confusion with the built-in behavior.

Reference: https://github.com/anthropics/claude-code/issues/11786
