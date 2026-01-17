<!--
Last Updated: 2026-01-15
Source: https://geminicli.com/docs/hooks/
        https://geminicli.com/docs/hooks/writing-hooks/
        https://geminicli.com/docs/hooks/reference/
-->

# Gemini CLI Hooks System

## Overview

Gemini CLI hooks are scripts that execute at specific points in the agent's lifecycle. They enable intercepting and customizing behavior without modifying CLI source code.

**Note**: Hooks are marked as experimental in Gemini CLI.

## Configuration

Hooks are configured in `settings.json` at various levels:

1. System defaults: `/etc/gemini-cli/system-defaults.json`
2. User settings: `~/.gemini/settings.json`
3. Project settings: `.gemini/settings.json`
4. System settings: `/etc/gemini-cli/settings.json`
5. Extension hooks

### Configuration Format

```json
{
  "hooks": {
    "enabled": true,
    "AfterAgent": [
      {
        "matcher": "*",
        "hooks": [
          {
            "name": "policy-check",
            "type": "command",
            "command": ".gemini/hooks/policy_check.sh",
            "timeout": 60000,
            "description": "Evaluates DeepWork policies"
          }
        ]
      }
    ]
  }
}
```

### Configuration Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Recommended | Unique identifier for enable/disable commands |
| `type` | Yes | Hook type - currently only `"command"` supported |
| `command` | Yes | Path to script or command to execute |
| `description` | No | Human-readable description for `/hooks` panel |
| `timeout` | No | Timeout in milliseconds (default: 60000) |
| `matcher` | No | Pattern to filter when hook runs |

### Matchers

Matchers support:
- Exact match: `write_file`
- Regex: `write_file|replace`
- Wildcard: `*`

## Hook Events

### All Available Events

| Event | Description | Timing |
|-------|-------------|--------|
| `SessionStart` | Session initialization | When CLI starts or resumes |
| `SessionEnd` | Session cleanup | When CLI exits |
| `BeforeAgent` | Before agent processes input | After user prompt, before planning |
| `AfterAgent` | After agent completes | Agent loop finished |
| `BeforeModel` | Before LLM request | Can modify request |
| `AfterModel` | After LLM response | Can modify response |
| `BeforeToolSelection` | Before tool selection | Can filter available tools |
| `BeforeTool` | Before tool execution | Can block or modify |
| `AfterTool` | After tool execution | Can add context |
| `PreCompress` | Before context compression | Triggered by auto or manual |
| `Notification` | Permission/notification events | Various UI events |

### Event Comparison with Claude Code

| DeepWork Generic | Gemini CLI | Claude Code |
|------------------|------------|-------------|
| `after_agent` | `AfterAgent` | `Stop` |
| `before_tool` | `BeforeTool` | `PreToolUse` |
| `before_prompt` | `BeforeAgent` | `UserPromptSubmit` |

## Input Schema (stdin)

All hooks receive JSON via stdin with common base fields plus event-specific fields.

### Universal Base Fields

```json
{
  "session_id": "abc123",
  "transcript_path": "/path/to/transcript.json",
  "cwd": "/current/working/directory",
  "hook_event_name": "AfterAgent",
  "timestamp": "2026-01-15T10:30:00Z"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `session_id` | string | Current CLI session identifier |
| `transcript_path` | string | Path to session's JSON transcript |
| `cwd` | string | Current working directory |
| `hook_event_name` | string | Event name that fired this hook |
| `timestamp` | string | ISO 8601 timestamp |

### Event-Specific Input Fields

#### Tool Events (BeforeTool, AfterTool)

```json
{
  "tool_name": "write_file",
  "tool_input": {
    "file_path": "/path/to/file.txt",
    "content": "file content"
  },
  "tool_response": "File written successfully",
  "mcp_context": {
    "server": "my-mcp-server"
  }
}
```

| Field | Event | Description |
|-------|-------|-------------|
| `tool_name` | Both | Tool identifier (e.g., `write_file`) |
| `tool_input` | Both | Tool arguments |
| `tool_response` | AfterTool only | Output from execution |
| `mcp_context` | Optional | Server identity for MCP tools |

#### Agent Events (BeforeAgent, AfterAgent)

```json
{
  "prompt": "User's submitted prompt",
  "prompt_response": "Final model response",
  "stop_hook_active": false
}
```

| Field | Event | Description |
|-------|-------|-------------|
| `prompt` | Both | User's submitted prompt |
| `prompt_response` | AfterAgent only | Final model response |
| `stop_hook_active` | AfterAgent only | Whether stop hook is preventing exit |

#### Model Events (BeforeModel, AfterModel)

```json
{
  "llm_request": {
    "model": "gemini-2.5-pro",
    "messages": [
      {"role": "user", "content": "Hello"}
    ],
    "config": {
      "temperature": 0.7,
      "maxOutputTokens": 8192,
      "topP": 0.95,
      "topK": 40
    },
    "toolConfig": {
      "functionCallingConfig": {
        "mode": "AUTO",
        "allowedFunctionNames": ["read_file", "write_file"]
      }
    }
  },
  "llm_response": {
    "text": "Hello! How can I help?",
    "candidates": [
      {
        "content": {"role": "model", "parts": []},
        "finishReason": "STOP",
        "safetyRatings": []
      }
    ],
    "usageMetadata": {
      "promptTokenCount": 100,
      "candidatesTokenCount": 50
    }
  }
}
```

#### Session Events

```json
{
  "source": "startup",
  "reason": "exit"
}
```

| Field | Event | Values |
|-------|-------|--------|
| `source` | SessionStart | `startup`, `resume`, `clear` |
| `reason` | SessionEnd | `exit`, `clear`, `logout`, `prompt_input_exit`, `other` |

#### Notification Events

```json
{
  "notification_type": "ToolPermission",
  "message": "Allow write to file?",
  "details": {}
}
```

## Output Schema (stdout)

### Exit Codes

| Code | Meaning | Behavior |
|------|---------|----------|
| `0` | Success | stdout parsed as JSON; non-JSON treated as systemMessage |
| `2` | Blocking error | Operation interrupted; stderr shown to agent |
| Other | Warning | Execution continues; stderr logged as warning |

### Common Output Fields

```json
{
  "decision": "allow",
  "reason": "Explanation for decision",
  "systemMessage": "Message displayed to user",
  "continue": true,
  "stopReason": "Message when stopping",
  "suppressOutput": false,
  "hookSpecificOutput": {
    "hookEventName": "AfterAgent",
    "additionalContext": "Extra context for agent"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `decision` | string | `allow`, `deny`, `block`, `ask`, `approve` |
| `reason` | string | Explanation shown to agent on deny/block |
| `systemMessage` | string | Message displayed to user in terminal |
| `continue` | boolean | `false` terminates agent loop immediately |
| `stopReason` | string | User-facing message when stopping |
| `suppressOutput` | boolean | Hide execution from transcript |
| `hookSpecificOutput` | object | Event-specific data container |

### Event-Specific Output

#### AfterAgent (equivalent to Claude's Stop)

Block the agent from completing:
```json
{
  "decision": "deny",
  "reason": "Policy X requires attention before completing"
}
```

Or use `continue: false` to force stop:
```json
{
  "continue": false,
  "stopReason": "Critical error detected"
}
```

Allow completion (default):
```json
{}
```

#### BeforeTool

Block tool execution:
```json
{
  "decision": "deny",
  "reason": "Security policy violation"
}
```

Allow and modify input:
```json
{
  "decision": "allow",
  "hookSpecificOutput": {
    "hookEventName": "BeforeTool",
    "additionalContext": "Proceeding with modified parameters"
  }
}
```

#### AfterTool

Add context after tool execution:
```json
{
  "hookSpecificOutput": {
    "hookEventName": "AfterTool",
    "additionalContext": "Note: File was formatted after write"
  }
}
```

#### BeforeAgent

Block user prompt:
```json
{
  "decision": "deny",
  "reason": "This type of request is not allowed"
}
```

Add context:
```json
{
  "hookSpecificOutput": {
    "hookEventName": "BeforeAgent",
    "additionalContext": "Current branch: main, Last commit: abc123"
  }
}
```

#### BeforeModel

Modify the LLM request:
```json
{
  "hookSpecificOutput": {
    "hookEventName": "BeforeModel",
    "llm_request": {
      "messages": [
        {"role": "system", "content": "Additional instructions..."}
      ]
    }
  }
}
```

Return synthetic response (skip model call):
```json
{
  "hookSpecificOutput": {
    "hookEventName": "BeforeModel",
    "llm_response": {
      "text": "Cached response",
      "candidates": [{"content": {"role": "model", "parts": []}}]
    }
  }
}
```

#### BeforeToolSelection

Filter available tools:
```json
{
  "hookSpecificOutput": {
    "hookEventName": "BeforeToolSelection",
    "toolConfig": {
      "functionCallingConfig": {
        "mode": "ANY",
        "allowedFunctionNames": ["read_file", "write_file", "shell"]
      }
    }
  }
}
```

Or output comma-separated tool names:
```bash
echo "read_file,write_file,shell"
exit 0
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GEMINI_PROJECT_DIR` | Absolute path to project root |

## Blocking Mechanisms

### Exit Code 2

The primary blocking mechanism. stderr content is shown to the agent.

```bash
#!/bin/bash
echo "Security violation: API key detected in file" >&2
exit 2
```

### Decision Field

For events that support it:

```json
{
  "decision": "deny",
  "reason": "Explanation for why action is blocked"
}
```

### Accepted Decision Values

| Value | Effect |
|-------|--------|
| `allow` | Permit the action |
| `deny` | Block the action |
| `block` | Block the action (alias for deny) |
| `ask` | Prompt user for confirmation |
| `approve` | Auto-approve (for permission events) |

## Performance Notes

- Hooks add latency to the execution pipeline
- Default timeout is 60 seconds (60000ms)
- Hooks exceeding timeout are terminated and logged as warnings
- Set appropriate timeouts based on hook complexity

## Migration from Claude Code

Gemini CLI includes a migration utility:

```bash
/hooks migrate
```

This converts:
- Event names (Stop → AfterAgent, PreToolUse → BeforeTool)
- Environment variables (CLAUDE_PROJECT_DIR → GEMINI_PROJECT_DIR)
- Tool names (Write → write_file, Bash → shell)
