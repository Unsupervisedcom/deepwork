<!--
Last Updated: 2026-01-16
Source: https://docs.anthropic.com/en/docs/claude-code/hooks
        https://docs.anthropic.com/en/docs/claude-code/settings
-->

# Claude Code Hooks System (Command Definitions)

## Overview

Claude Code supports **command-level hooks** within slash command definitions. This is a key differentiator from platforms like Gemini CLI, where hooks are only configurable globally.

Hooks in command definitions allow per-command quality validation, input preprocessing, and output verification. These hooks are defined in the YAML frontmatter of markdown command files.

## Command-Level Hook Support

Claude Code slash commands (defined in `.md` files) support hooks in the YAML frontmatter:

- `hooks.Stop` - Triggered when the agent finishes responding
- `hooks.PreToolUse` - Triggered before a tool is used
- `hooks.UserPromptSubmit` - Triggered when the user submits a prompt

### Command File Format

```markdown
---
description: Brief description of the command
hooks:
  Stop:
    - hooks:
        - type: command
          command: "./scripts/validate.sh"
        - type: prompt
          prompt: |
            Validate the output meets criteria...
---

# Command Name

Instructions for the command...
```

### Hook Configuration Fields

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `hooks` | No | Object | Container for lifecycle hooks |
| `hooks.<Event>` | No | Array | Array of hook configurations for the event |
| `type` | Yes | String | `"command"` for shell scripts, `"prompt"` for LLM evaluation |
| `command` | For type=command | String | Path to shell script to execute |
| `prompt` | For type=prompt | String | Prompt for LLM to evaluate |
| `timeout` | No | Number | Timeout in seconds (default: 60) |

## Available Hook Events

### Stop

Triggered when the main agent finishes responding. Use for:
- Quality validation loops
- Output verification
- Completion criteria checking

```yaml
hooks:
  Stop:
    - hooks:
        - type: prompt
          prompt: |
            Verify all acceptance criteria are met.
            If met, respond: {}
            If not met, respond: {"decision": "block", "reason": "..."}
```

**Blocking behavior**: Return JSON with `{"decision": "block", "reason": "..."}` or exit code 2 with stderr message.

### PreToolUse

Triggered before the agent uses a tool. Use for:
- Tool input validation
- Security checks
- Pre-processing

```yaml
hooks:
  PreToolUse:
    - matcher: "Bash|Write|Edit"
      hooks:
        - type: command
          command: "./hooks/security-check.sh"
```

**Note**: PreToolUse hooks require a `matcher` field to specify which tools to intercept.

**Blocking behavior**: Return `{"hookSpecificOutput": {"permissionDecision": "deny"}}` or exit code 2.

### UserPromptSubmit

Triggered when the user submits a prompt. Use for:
- Input validation
- Context injection
- Session initialization

```yaml
hooks:
  UserPromptSubmit:
    - hooks:
        - type: command
          command: "./hooks/inject-context.sh"
```

**Blocking behavior**: Return `{"decision": "block", "reason": "..."}` or exit code 2.

## Hook Input/Output Contract

### Input (stdin)

All hooks receive JSON via stdin:

```json
{
  "session_id": "abc123",
  "transcript_path": "/path/to/transcript.jsonl",
  "cwd": "/current/working/directory",
  "permission_mode": "default",
  "hook_event_name": "Stop",
  "tool_name": "ToolName",
  "tool_input": {}
}
```

### Output (stdout)

Hooks return JSON via stdout:

```json
{}
```

Or to block:

```json
{
  "decision": "block",
  "reason": "Explanation of what needs to be done"
}
```

### Exit Codes

| Code | Meaning | Behavior |
|------|---------|----------|
| `0` | Success | stdout parsed as JSON |
| `2` | Blocking error | stderr shown, operation blocked |
| Other | Warning | stderr logged, continues |

## DeepWork Generic Event Mapping

DeepWork uses generic event names that map to Claude Code's platform-specific names:

| DeepWork Generic | Claude Code Event |
|------------------|-------------------|
| `after_agent` | `Stop` |
| `before_tool` | `PreToolUse` |
| `before_prompt` | `UserPromptSubmit` |

## Hook Types

### Command Hooks

Execute a shell script:

```yaml
hooks:
  Stop:
    - hooks:
        - type: command
          command: ".deepwork/jobs/my_job/hooks/validate.sh"
          timeout: 30
```

### Prompt Hooks

Use LLM evaluation:

```yaml
hooks:
  Stop:
    - hooks:
        - type: prompt
          prompt: |
            Evaluate whether the response meets all criteria.
            Respond with {} or {"decision": "block", "reason": "..."}
```

## Quality Validation Loop Pattern

Claude Code's Stop hooks enable iterative quality validation:

1. Agent completes its response
2. Stop hook evaluates quality criteria
3. If criteria not met, agent continues working
4. Loop repeats until criteria are satisfied

This pattern is unique to Claude Code among DeepWork-supported platforms.

### Implementation Example

```yaml
hooks:
  Stop:
    - hooks:
        - type: prompt
          prompt: |
            ## Quality Criteria
            1. All tests pass
            2. Code follows style guide
            3. Documentation updated

            Review the conversation. If ALL criteria met and
            <promise> tag present, respond: {}

            Otherwise respond: {"decision": "block", "reason": "..."}
```

## Comparison with Other Platforms

| Feature | Claude Code | Gemini CLI |
|---------|-------------|------------|
| Command-level hooks | Yes | No |
| Global hooks | Yes | Yes |
| Hook types | `command`, `prompt` | `command` only |
| Quality validation loops | Yes (Stop hooks) | No (workarounds only) |
| Per-command customization | Full | None |

## Implications for DeepWork

Since Claude Code fully supports command-level hooks:

1. **`stop_hooks` are fully supported** - Quality validation loops work as designed
2. **Job definitions** can use `hooks.after_agent` (maps to Stop)
3. **Platform adapter** implements all hook mappings
4. **Command templates** generate YAML frontmatter with hook configurations

## Environment Variables

Available to hook scripts:

| Variable | Description |
|----------|-------------|
| `CLAUDE_PROJECT_DIR` | Absolute path to project root |
| `CLAUDE_ENV_FILE` | Path to env file (SessionStart only) |
| `CLAUDE_CODE_REMOTE` | `"true"` in web environment |

## Limitations

1. **Prompt hooks are evaluated by the model** - May have latency
2. **Timeout default is 60 seconds** - Long-running hooks may fail
3. **Multiple hooks run in parallel** - Cannot depend on order
4. **Transcript path is JSONL** - Requires line-by-line parsing

## References

- [Claude Code Hooks Documentation](https://docs.anthropic.com/en/docs/claude-code/hooks)
- [Claude Code Settings](https://docs.anthropic.com/en/docs/claude-code/settings)
- DeepWork adapter: `src/deepwork/core/adapters.py`
