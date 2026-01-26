# Claude Templates - Agent Notes

Notes for AI agents working on Claude Code jinja templates.

## Prompt-Based Stop Hooks - NOT WORKING

**IMPORTANT: Prompt-based stop hooks (`type: prompt` for Stop/SubagentStop events) do not currently work properly in Claude Code.**

Reference: https://github.com/anthropics/claude-code/issues/20221

### What This Means

- Do NOT use `type: prompt` hooks for Stop or SubagentStop events in templates
- The quality validation loop pattern that relies on prompt hooks will not function as expected
- Instead, instruct agents to use a sub-agent (e.g., Haiku) to review their work against quality criteria

### Workaround

Instead of prompt-based stop hooks, templates should include explicit instructions in the command content directing the agent to:

1. Have a sub-agent using Haiku review the work against the specified quality criteria
2. Fix any valid issues raised by the sub-agent
3. Have the sub-agent review again until all valid feedback is handled

### Future Reversal

If prompt-based stop hooks are fixed in Claude Code (check the issue above for updates), this guidance should be reversed and prompt hooks can be re-enabled in templates.

## Historical Context (Prompt Hooks - When They Work)

The following guidance applies IF prompt hooks start working again:

When writing prompt-based hooks (e.g., Stop hooks with `type: prompt`):

- **Do NOT include instructions on how to return responses** (e.g., "respond with JSON", "return `{"ok": true}`"). Claude Code's internal instructions already specify the expected response format for prompt hooks.
- Adding redundant response format instructions can cause conflicts or confusion with the built-in behavior. i.e. the hook will not block the agent from stopping.

Reference: https://github.com/anthropics/claude-code/issues/11786
