<!--
Last Updated: 2026-01-12
Source: https://geminicli.com/docs/hooks/
        https://geminicli.com/docs/cli/custom-commands/
        https://github.com/google-gemini/gemini-cli
-->

# Gemini CLI Hooks System (Command Definitions)

## Overview

**Important**: Gemini CLI does **NOT** support hooks within slash command definitions. Unlike Claude Code's `stop_hooks` that can be defined per-command in markdown frontmatter, Gemini CLI's hooks are configured globally or at the project level in `settings.json`.

This document describes the hooks system as it relates to custom commands, and clarifies what is and isn't available for command-level customization.

## Custom Command Hooks - NOT SUPPORTED

Gemini CLI custom commands (defined in `.toml` files) only support two fields:

- `prompt` (required): The prompt text
- `description` (optional): Description shown in help

There are **no hook fields** available in the TOML command definition format:
- No `pre_hooks` or `before_hooks`
- No `post_hooks` or `after_hooks`
- No `stop_hooks` or validation hooks
- No `on_complete` or lifecycle callbacks

## Global Hooks System (For Reference)

While not applicable to individual command definitions, Gemini CLI does have a global hooks system that triggers at various points in the agent lifecycle.

### Available Hook Events

| Event | Trigger Point |
|-------|---------------|
| `SessionStart` | Session begins |
| `SessionEnd` | Session closes |
| `BeforeAgent` | Post-prompt, pre-planning |
| `AfterAgent` | Agent loop completion |
| `BeforeModel` | Before LLM request |
| `AfterModel` | After LLM response |
| `BeforeToolSelection` | Pre-tool selection |
| `BeforeTool` | Before tool execution |
| `AfterTool` | After tool execution |
| `PreCompress` | Before context compression |
| `Notification` | Permission/notification events |

### Hook Configuration (Global/Project Level)

Hooks are defined in `settings.json`, not in command files:

```json
{
  "hooks": {
    "enabled": true,
    "BeforeTool": [
      {
        "matcher": "write_file|replace",
        "hooks": [
          {
            "name": "security-check",
            "type": "command",
            "command": "./hooks/validate.sh",
            "timeout": 30000
          }
        ]
      }
    ],
    "AfterTool": [
      {
        "matcher": "FileEdit",
        "hooks": [
          {
            "name": "format-code",
            "type": "command",
            "command": "./hooks/prettier.sh"
          }
        ]
      }
    ]
  }
}
```

### Hook Input/Output Contract

- **Communication**: JSON via stdin; exit codes + stdout/stderr responses
- **Exit Codes**:
  - `0` = Success (output shown/injected)
  - `2` = Blocking error (stderr shown, operation may be blocked)
  - Other = Non-blocking warning (logged, continues)

## Workarounds for Command-Level Hooks

Since per-command hooks aren't supported, here are alternative approaches:

### 1. Shell Command Injection

Use `!{...}` in the prompt to execute validation/setup commands:

```toml
prompt = """
!{./scripts/pre-check.sh}

Now proceed with the task...
"""
```

**Limitation**: This runs at prompt expansion time, not as a hook with control flow.

### 2. Global Hooks with Matchers

Configure global hooks that pattern-match on specific conditions:

```json
{
  "hooks": {
    "AfterAgent": [
      {
        "hooks": [
          {
            "name": "run-tests",
            "type": "command",
            "command": "./scripts/run-tests.sh"
          }
        ]
      }
    ]
  }
}
```

### 3. Prompt-Based Validation

Include validation instructions directly in the prompt:

```toml
prompt = """
Before completing this task, ensure:
1. All tests pass (run: npm test)
2. No linting errors (run: npm run lint)

Only mark the task complete if all checks pass.
"""
```

## Comparison with Other Platforms

| Feature | Gemini CLI | Claude Code |
|---------|------------|-------------|
| Command-level hooks | No | Yes (`stop_hooks` in frontmatter) |
| Global hooks | Yes (settings.json) | Yes (CLAUDE.md hooks) |
| Hook types | `command` only | `prompt`, `script` |
| Hook events | 11 events | 1 event (`stop`) |
| Per-command customization | None | Full |

## Implications for DeepWork

Since Gemini CLI doesn't support command-level hooks:

1. **`stop_hooks` cannot be implemented** per-command as they are in Claude Code
2. **Quality validation loops** would need to be:
   - Embedded in the prompt instructions
   - Handled by global AfterAgent hooks
   - Managed through explicit user confirmation
3. **Platform adapter** should set hook-related fields to `None`/`null`

## Limitations

1. **No command-level lifecycle hooks**: All hooks are global/project-scoped
2. **No hook filtering by command**: Cannot trigger hooks only for specific slash commands
3. **Experimental status**: The entire hooks system is marked as experimental
4. **Command type only**: No plugin/npm-based hooks yet (planned for future)

## Future Considerations

Based on GitHub issues, there are proposals for:
- Extension-level hooks (`hooks/hooks.json` convention)
- More granular hook matchers
- Plugin-based hook types

Monitor the Gemini CLI repository for updates to the hooks system that might enable command-level hooks in the future.
