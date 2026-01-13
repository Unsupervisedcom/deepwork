<!--
Last Updated: 2026-01-13
Source: https://opencode.ai/docs/plugins/
        https://opencode.ai/docs/commands/
        https://dev.to/einarcesar/does-opencode-support-hooks-a-complete-guide-to-extensibility-k3p
        https://github.com/opencode-ai/opencode
-->

# OpenCode Hooks System (Command Definitions)

## Overview

**Important**: OpenCode does **NOT** support hooks within slash command definitions. Unlike Claude Code's `stop_hooks` that can be defined per-command in markdown frontmatter, OpenCode's hooks are implemented through a global plugin system.

This document describes the hooks system as it relates to custom commands, and clarifies what is and isn't available for command-level customization.

## Custom Command Hooks - NOT SUPPORTED

OpenCode custom commands (defined in `.md` files) only support these frontmatter fields:

- `description` (optional): Brief explanation shown in command list
- `agent` (optional): Agent to execute the command
- `model` (optional): Model override
- `subtask` (optional): Execute in separate child session

There are **no hook fields** available in the command definition format:
- No `pre_hooks` or `before_hooks`
- No `post_hooks` or `after_hooks`
- No `stop_hooks` or validation hooks
- No `on_complete` or lifecycle callbacks

## Plugin System (Global Hooks)

While not applicable to individual command definitions, OpenCode has a comprehensive plugin system that hooks into various events globally.

### Plugin Locations

Plugins are JavaScript/TypeScript modules placed in:

1. **Project plugins**: `.opencode/plugin/` - Project-specific
2. **Global plugins**: `~/.config/opencode/plugin/` - Available across projects

Or specified via npm packages in `opencode.json`:

```json
{
  "plugin": ["opencode-plugin-package", "@my-org/custom-plugin"]
}
```

### Available Hook Events

| Event | Trigger Point |
|-------|---------------|
| `command.executed` | After a command is executed |
| `file.edited` | When a file is edited |
| `file.watcher.updated` | When file watcher detects changes |
| `installation.updated` | When installation is updated |
| `lsp.client.diagnostics` | When LSP diagnostics are received |
| `lsp.updated` | When LSP state changes |
| `message.part.removed` | When a message part is removed |
| `message.part.updated` | When a message part is updated |
| `message.removed` | When a message is removed |
| `message.updated` | When a message is updated |
| `permission.replied` | When a permission request is answered |
| `permission.updated` | When permissions change |
| `server.connected` | When server connection is established |
| `session.created` | When a new session starts |
| `session.compacted` | When session context is compacted |
| `session.deleted` | When a session is deleted |
| `session.diff` | When session diff is calculated |
| `session.error` | When a session error occurs |
| `session.idle` | When session becomes idle |
| `session.status` | When session status changes |
| `session.updated` | When session is updated |
| `tool.execute.before` | Before a tool executes |
| `tool.execute.after` | After a tool executes |
| `tui.prompt.append` | When text is appended to prompt |
| `tui.command.execute` | When a TUI command executes |
| `tui.toast.show` | When a toast notification shows |
| `experimental.session.compacting` | Before LLM generates compaction summary |

### Plugin Structure

A basic plugin receives a context object and returns hooks:

```typescript
import { definePlugin } from "@opencode-ai/plugin"

export default definePlugin((ctx) => {
  return {
    "tool.execute.before": async (input) => {
      // Prevent reading .env files
      if (input.tool === "read" && input.args.filePath.includes(".env")) {
        throw new Error("Cannot read .env files")
      }
    },
    "tool.execute.after": async (input, output) => {
      // Auto-format after file edits
      if (input.tool === "write") {
        await ctx.$`prettier --write ${input.args.filePath}`
      }
    }
  }
})
```

### Hook Input/Output

- **Before hooks**: Can prevent actions by throwing errors
- **After hooks**: Can trigger post-execution tasks
- **Context object**: Provides access to `project`, `directory`, `worktree`, `client`, and Bun shell API (`$`)

## Workarounds for Command-Level Hooks

Since per-command hooks aren't supported, here are alternative approaches:

### 1. Shell Command Injection

Use backtick syntax in the prompt to execute validation/setup commands:

```markdown
---
description: Run with pre-check
---
`./scripts/pre-check.sh`

Now proceed with the task...
```

**Limitation**: This runs at prompt expansion time, not as a hook with control flow.

### 2. Global Plugins with Event Hooks

Create a plugin that hooks into `tool.execute.after` or `session.idle`:

```typescript
export default definePlugin((ctx) => {
  return {
    "session.idle": async () => {
      // Run tests after each interaction
      await ctx.$`npm test`
    }
  }
})
```

### 3. Prompt-Based Validation

Include validation instructions directly in the command prompt:

```markdown
---
description: Implement feature with tests
---
Implement the requested feature.

Before completing, ensure:
1. All tests pass (run: npm test)
2. No linting errors (run: npm run lint)

Only mark complete if all checks pass.
```

### 4. Subagent Isolation

Use `subtask: true` to isolate command execution:

```markdown
---
description: Risky operation
subtask: true
---
Perform this operation in isolation.
```

## Comparison with Other Platforms

| Feature | OpenCode | Claude Code | Gemini CLI |
|---------|----------|-------------|------------|
| Command-level hooks | No | Yes (`stop_hooks`) | No |
| Global hooks | Yes (plugin system) | Yes (hooks in settings) | Yes (settings.json) |
| Hook types | JS/TS plugins | `prompt`, `script` | `command` only |
| Hook events | 25+ events | Limited events | 11 events |
| Per-command customization | None | Full | None |
| Before/after tool hooks | Yes | No | Yes |

## Implications for DeepWork

Since OpenCode doesn't support command-level hooks:

1. **`stop_hooks` cannot be implemented** per-command as they are in Claude Code
2. **Quality validation loops** would need to be:
   - Embedded in the prompt instructions
   - Handled by global plugin hooks (e.g., `session.idle`)
   - Managed through explicit user confirmation
3. **Platform adapter** should set hook-related fields to `None`/`null`

## Limitations

1. **No command-level lifecycle hooks**: All hooks are global through plugins
2. **No hook filtering by command**: Cannot trigger hooks only for specific slash commands
3. **Plugin-only hooks**: No declarative hook configuration in JSON
4. **Bun runtime**: Plugins require Bun/Node.js runtime environment

## Future Considerations

OpenCode's plugin system is actively developed. Monitor the repository for:
- More granular hook events
- Potential command-level hook support
- Enhanced plugin API features

The plugin architecture is flexible enough that command-level hooks could potentially be added in future versions.
