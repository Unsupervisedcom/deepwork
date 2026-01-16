# Gemini CLI Platform Learnings

This document captures behaviors, quirks, and insights discovered while implementing DeepWork's Gemini CLI adapter.

## Add Your Learnings Here

When you discover something about Gemini CLI behavior that isn't obvious from documentation, add it to the appropriate section below.

---

## Hook System

### AfterAgent vs Stop

- **`AfterAgent` is the equivalent of Claude's `Stop`** - Fires when agent loop completes
- **`decision: "deny"` blocks completion** - Different from Claude's `"block"`
- **Both `deny` and `block` work** - Gemini accepts either value
- **`continue: false` is an alternative** - Forces immediate termination

### Tool Name Differences

- **Gemini uses snake_case tool names** - `write_file` not `Write`
- **Shell command is `shell`** - Not `Bash`
- **Read file is `read_file`** - Not `Read`

### Transcript Format

- **Transcript is JSON, not JSONL** - Different from Claude's line-delimited format
- **Structure differs from Claude** - Need to parse differently

## Configuration Differences

### Hooks in Settings

- **Hooks are global only** - No per-command hooks in TOML files
- **settings.json controls all hooks** - Unlike Claude's frontmatter support
- **`enabled` flag controls hooks** - Can globally enable/disable

### Environment Variables

- **`GEMINI_PROJECT_DIR`** - Equivalent to `CLAUDE_PROJECT_DIR`
- **No `GEMINI_ENV_FILE`** - Cannot persist env vars like Claude's SessionStart

## JSON Format Differences

### Input Schema

- **Includes `timestamp` field** - ISO 8601 format, not in Claude
- **`tool_response` in AfterTool** - Claude doesn't provide this directly
- **`stop_hook_active` in AfterAgent** - Indicates if another hook is blocking

### Output Schema

- **`hookSpecificOutput` is optional** - Can just return decision/reason
- **Plain text stdout becomes `systemMessage`** - When exit code is 0
- **`additionalContext` field** - For injecting context into agent

## Migration Notes

### Converting Claude Hooks

- **Use `/hooks migrate` command** - Built-in conversion utility
- **Event names change** - Stop→AfterAgent, PreToolUse→BeforeTool
- **Tool names change** - Need to update matchers
- **Decision values change** - `"block"` → `"deny"`

### Wrapper Script Approach

When supporting both platforms:

1. Use platform-specific shell wrapper
2. Normalize input JSON
3. Run common Python logic
4. Denormalize output JSON

---

## Date Log

| Date | Finding | Author |
|------|---------|--------|
| 2026-01-15 | Initial documentation created from web research | Claude |
