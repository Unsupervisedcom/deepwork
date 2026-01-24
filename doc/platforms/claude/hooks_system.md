<!--
Last Updated: 2026-01-23
Source: https://docs.anthropic.com/en/docs/claude-code/hooks
        https://docs.anthropic.com/en/docs/claude-code/settings
-->

# Claude Code Hooks System (Command Definitions)

## Overview

Claude Code supports **command-level hooks** within slash command definitions. This is a key differentiator from platforms like Gemini CLI, where hooks are only configurable globally.

Hooks in command definitions allow per-command quality validation, input preprocessing, and output verification. These hooks are defined in the YAML frontmatter of markdown command files.

## Known Issues

### Prompt-Based Stop Hooks Not Working

**IMPORTANT**: Prompt-based hooks (`type: prompt`) for Stop and SubagentStop events do not currently work properly.

Reference: https://github.com/anthropics/claude-code/issues/20221

**Impact**:
- Quality validation loops using prompt hooks will not block the agent as expected
- The agent may finish without the prompt hook properly evaluating the response

**Workaround**:
For quality validation, instead of using prompt-based stop hooks, include explicit instructions in the command content directing the agent to:
1. Spawn a sub-agent (e.g., using Haiku model) to review work against quality criteria
2. Fix any valid issues raised by the sub-agent
3. Have the sub-agent review again until all valid feedback is handled

**Command-type hooks still work**: If you need automated validation via Stop hooks, use `type: command` hooks that run shell scripts.

**Future**: If this issue is resolved, prompt-based stop hooks can be re-enabled. Check the GitHub issue for updates.

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

**NOTE**: Prompt-based stop hooks (`type: prompt`) do not currently work. See [Known Issues](#prompt-based-stop-hooks-not-working) above.

For command-type hooks:

```yaml
hooks:
  Stop:
    - hooks:
        - type: command
          command: ".deepwork/jobs/my_job/hooks/validate.sh"
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
{
  "ok": true
}
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

**NOTE**: Prompt hooks for Stop/SubagentStop events do not currently work. See [Known Issues](#prompt-based-stop-hooks-not-working).

Prompt hooks may work for other event types (e.g., PreToolUse, UserPromptSubmit), but this has not been fully tested.

```yaml
# Example for non-Stop events (untested)
hooks:
  UserPromptSubmit:
    - hooks:
        - type: prompt
          prompt: |
            Validate the user's prompt before processing.
```

## Quality Validation Loop Pattern

**NOTE**: This pattern using prompt-based Stop hooks does not currently work. See [Known Issues](#prompt-based-stop-hooks-not-working).

### Alternative: Sub-Agent Review

Instead of relying on prompt hooks, include explicit instructions in your command content:

```markdown
## Quality Validation

Before completing this step, you MUST have your work reviewed.

**Quality Criteria**:
1. All tests pass
2. Code follows style guide
3. Documentation updated

**Review Process**:
1. Once you believe your work is complete, spawn a sub-agent using Haiku to review your work against the quality criteria above
2. The sub-agent should examine your outputs and verify each criterion is met
3. If the sub-agent identifies valid issues, fix them
4. Have the sub-agent review again until all valid feedback has been addressed
5. Only mark the step complete when the sub-agent confirms all criteria are satisfied
```

### Command-Type Hooks (Still Work)

If you need automated validation, use command-type hooks that run shell scripts:

```yaml
hooks:
  Stop:
    - hooks:
        - type: command
          command: ".deepwork/jobs/my_job/hooks/validate.sh"
```

## Comparison with Other Platforms

| Feature | Claude Code | Gemini CLI |
|---------|-------------|------------|
| Command-level hooks | Yes | No |
| Global hooks | Yes | Yes |
| Hook types | `command`, `prompt`* | `command` only |
| Quality validation loops | Via sub-agent review** | No (workarounds only) |
| Per-command customization | Full | None |

*Prompt hooks for Stop/SubagentStop events do not currently work (see [Known Issues](#prompt-based-stop-hooks-not-working))
**Prompt-based Stop hooks are not working; use sub-agent review pattern instead

## Implications for DeepWork

Due to the prompt-based Stop hooks not working:

1. **Prompt-based `stop_hooks` are NOT generated** - Templates filter out prompt hooks for Stop events
2. **Quality validation** uses explicit sub-agent review instructions in command content
3. **Command-type hooks still work** - Script-based hooks for Stop events are generated as expected
4. **Job definitions** can still use `hooks.after_agent` for script hooks (maps to Stop)
5. **Platform adapter** implements all hook mappings (but prompt Stop hooks are skipped in templates)

## Environment Variables

Available to hook scripts:

| Variable | Description |
|----------|-------------|
| `CLAUDE_PROJECT_DIR` | Absolute path to project root |
| `CLAUDE_ENV_FILE` | Path to env file (SessionStart only) |
| `CLAUDE_CODE_REMOTE` | `"true"` in web environment |

## Limitations

1. **Prompt hooks for Stop/SubagentStop do not work** - See [Known Issues](#prompt-based-stop-hooks-not-working)
2. **Timeout default is 60 seconds** - Long-running hooks may fail
3. **Multiple hooks run in parallel** - Cannot depend on order
4. **Transcript path is JSONL** - Requires line-by-line parsing

## References

- [Claude Code Hooks Documentation](https://docs.anthropic.com/en/docs/claude-code/hooks)
- [Claude Code Settings](https://docs.anthropic.com/en/docs/claude-code/settings)
- DeepWork adapter: `src/deepwork/core/adapters.py`
