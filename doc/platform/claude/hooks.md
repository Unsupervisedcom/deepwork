<!--
Last Updated: 2026-01-15
Source: https://code.claude.com/docs/en/hooks
-->

# Claude Code Hooks System

## Overview

Claude Code hooks are scripts that execute at specific points in Claude's workflow. They enable intercepting and controlling tool execution, validating user input, and performing custom actions.

## Configuration

Hooks are configured in JSON settings files with this precedence (lowest to highest):

1. `~/.claude/settings.json` - User settings
2. `.claude/settings.json` - Project settings
3. `.claude/settings.local.json` - Local project settings (not committed)
4. Managed policy settings

### Configuration Format

```json
{
  "hooks": {
    "EventName": [
      {
        "matcher": "ToolPattern",
        "hooks": [
          {
            "type": "command",
            "command": "your-command-here",
            "timeout": 60
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
| `matcher` | For tool events | Pattern to match tool names (regex, `*` wildcard) |
| `type` | Yes | `"command"` for bash or `"prompt"` for LLM evaluation |
| `command` | For type=command | Bash command to execute |
| `prompt` | For type=prompt | LLM prompt to evaluate |
| `timeout` | No | Timeout in seconds (default: 60) |

## Hook Events

### Tool-Related Events (require matcher)

| Event | Description | Timing |
|-------|-------------|--------|
| `PreToolUse` | Before tool execution | Can block or modify |
| `PermissionRequest` | When permission dialog shown | Can auto-approve/deny |
| `PostToolUse` | After tool completes | Can add context |

Common matchers: `Bash`, `Write`, `Edit`, `Read`, `WebFetch`, `Task`, `mcp__*`

### Workflow Events (no matcher needed)

| Event | Description |
|-------|-------------|
| `UserPromptSubmit` | When user submits a prompt |
| `Stop` | When main agent finishes responding |
| `SubagentStop` | When a subagent finishes |
| `PreCompact` | Before compact operation |
| `SessionStart` | When session starts/resumes |
| `SessionEnd` | When session ends |

### Notification Events

| Event | Matchers |
|-------|----------|
| `Notification` | `permission_prompt`, `idle_prompt`, `auth_success`, `elicitation_dialog` |

## Input Schema (stdin)

All hooks receive JSON via stdin:

```json
{
  "session_id": "abc123",
  "transcript_path": "/path/to/transcript.jsonl",
  "cwd": "/current/working/directory",
  "permission_mode": "default",
  "hook_event_name": "Stop",
  "tool_name": "ToolName",
  "tool_input": { /* tool-specific fields */ },
  "tool_use_id": "toolu_..."
}
```

### Common Input Fields

| Field | Type | Description |
|-------|------|-------------|
| `session_id` | string | Current session identifier |
| `transcript_path` | string | Path to session transcript JSONL |
| `cwd` | string | Current working directory |
| `permission_mode` | string | One of: `default`, `plan`, `acceptEdits`, `dontAsk`, `bypassPermissions` |
| `hook_event_name` | string | The event that triggered this hook |
| `tool_name` | string | Name of the tool (for tool events) |
| `tool_input` | object | Tool-specific input parameters |
| `tool_use_id` | string | Unique identifier for this tool use |

### Tool-Specific Input Examples

**Bash Tool:**
```json
{
  "tool_name": "Bash",
  "tool_input": {
    "command": "npm test",
    "description": "Run tests",
    "timeout": 120000
  }
}
```

**Write Tool:**
```json
{
  "tool_name": "Write",
  "tool_input": {
    "file_path": "/path/to/file.txt",
    "content": "file content"
  }
}
```

**Edit Tool:**
```json
{
  "tool_name": "Edit",
  "tool_input": {
    "file_path": "/path/to/file.txt",
    "old_string": "original text",
    "new_string": "replacement text",
    "replace_all": false
  }
}
```

**Read Tool:**
```json
{
  "tool_name": "Read",
  "tool_input": {
    "file_path": "/path/to/file.txt",
    "offset": 0,
    "limit": 100
  }
}
```

## Output Schema (stdout)

### Exit Codes

| Code | Meaning | Behavior |
|------|---------|----------|
| `0` | Success | stdout parsed as JSON |
| `2` | Blocking error | stderr shown as error, operation blocked |
| Other | Warning | stderr logged, operation continues |

### Common Output Fields

```json
{
  "continue": true,
  "stopReason": "Message shown when continue is false",
  "suppressOutput": true,
  "systemMessage": "Optional warning message",
  "decision": "block",
  "reason": "Explanation for blocking",
  "hookSpecificOutput": {
    "hookEventName": "EventName"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `continue` | boolean | `false` terminates agent loop |
| `stopReason` | string | Message when stopping |
| `suppressOutput` | boolean | Hide from transcript |
| `systemMessage` | string | Warning to display |
| `decision` | string | `"block"` to prevent action |
| `reason` | string | Explanation for decision |

### Event-Specific Output

#### Stop / SubagentStop

Block the agent from stopping:

```json
{
  "decision": "block",
  "reason": "You must complete task X before stopping"
}
```

Allow stopping (default):
```json
{}
```

#### UserPromptSubmit

Block the prompt:
```json
{
  "decision": "block",
  "reason": "Cannot process this type of request"
}
```

Add context (text output):
```bash
echo "Current time: $(date)"
exit 0
```

#### PreToolUse

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow",
    "permissionDecisionReason": "Auto-approved",
    "updatedInput": {
      "field_to_modify": "new value"
    }
  }
}
```

| permissionDecision | Effect |
|--------------------|--------|
| `"allow"` | Bypass permission, execute tool |
| `"deny"` | Block tool execution |
| `"ask"` | Show permission dialog |

#### PermissionRequest

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PermissionRequest",
    "decision": {
      "behavior": "allow",
      "updatedInput": {},
      "message": "Auto-approved",
      "interrupt": false
    }
  }
}
```

#### PostToolUse

```json
{
  "decision": "block",
  "reason": "Tool output indicates error",
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "Additional info for Claude"
  }
}
```

#### SessionStart

```json
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "Context to load at session start"
  }
}
```

## Environment Variables

| Variable | Availability | Description |
|----------|--------------|-------------|
| `CLAUDE_PROJECT_DIR` | All hooks | Absolute path to project root |
| `CLAUDE_ENV_FILE` | SessionStart only | File path for persisting env vars |
| `CLAUDE_CODE_REMOTE` | All hooks | `"true"` in web environment |

### Persisting Environment Variables

In SessionStart hooks only:

```bash
#!/bin/bash
if [ -n "$CLAUDE_ENV_FILE" ]; then
  echo 'export NODE_ENV=production' >> "$CLAUDE_ENV_FILE"
fi
exit 0
```

## DeepWork Event Mapping

| DeepWork Generic | Claude Code |
|------------------|-------------|
| `after_agent` | `Stop` |
| `before_tool` | `PreToolUse` |
| `before_prompt` | `UserPromptSubmit` |

## Key Behaviors

1. **Exit code 2** is the primary blocking mechanism
2. **JSON with `decision: "block"`** also blocks for Stop hooks
3. **stderr** on exit code 2 is shown to the agent
4. **stdout** on exit code 0 is parsed as JSON
5. **Plain text stdout** is added as context for some events
6. **Multiple hooks** matching the same event run in parallel
7. **Timeout** default is 60 seconds per hook
