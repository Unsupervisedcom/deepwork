<!--
Last Updated: 2026-01-13
Source: https://opencode.ai/docs/
        https://opencode.ai/docs/cli/
        https://opencode.ai/docs/commands/
        https://opencode.ai/docs/config/
        https://github.com/opencode-ai/opencode
-->

# OpenCode CLI Configuration

## Overview

OpenCode is an open-source AI coding agent built for the terminal. Implemented in Go, it provides a Text User Interface (TUI) for intelligent code assistance. OpenCode supports multiple LLM providers through the AI SDK and Models.dev, with 75+ providers available out of the box.

## Configuration Files

OpenCode uses JSON-based configuration with support for JSONC (JSON with Comments). Configuration files are **merged together, not replaced**, with later sources overriding earlier ones only for conflicting keys.

### File Locations

Configuration is applied in this order (lowest to highest priority):

| Priority | Source | Location |
|----------|--------|----------|
| 1 | Remote config | `.well-known/opencode` |
| 2 | Global config | `~/.config/opencode/opencode.json` |
| 3 | Custom config | `OPENCODE_CONFIG` environment variable path |
| 4 | Project config | `opencode.json` in project root |
| 5 | .opencode directory | `.opencode/` directory contents |
| 6 | Inline config | `OPENCODE_CONFIG_CONTENT` environment variable |

### Configuration Format

OpenCode accepts both JSON and JSONC formats. The schema is defined at:
`https://opencode.ai/config.json`

Core configuration options include:

| Option | Purpose |
|--------|---------|
| `model` | Primary LLM model to use |
| `small_model` | Lightweight model for tasks like title generation |
| `provider` | Provider configuration with timeout and cache settings |
| `theme` | Visual theme selection |
| `autoupdate` | Enable/disable automatic updates (or set to `"notify"`) |
| `agent` | Define custom agents |
| `default_agent` | Set the primary agent |
| `command` | Define custom commands |
| `tools` | Enable/disable specific tools |
| `permission` | Require approval for operations |
| `mcp` | Configure Model Context Protocol servers |
| `plugin` | Load extensions from npm or local files |

Example configuration:

```json
{
  "model": "anthropic/claude-sonnet-4-20250514",
  "small_model": "anthropic/claude-haiku-4-20250514",
  "theme": "dark",
  "tools": {
    "write": true,
    "bash": true
  },
  "permission": {
    "bash": "ask"
  }
}
```

## Custom Commands/Skills

Custom commands are reusable prompt templates that can be invoked with `/command-name` in the TUI.

### Command Location

Commands are discovered from two primary locations:

1. **Project commands**: `.opencode/command/` - Project-specific, can be version-controlled
2. **Global commands**: `~/.config/opencode/command/` - Available across all projects

Commands can also be defined directly in `opencode.json`:

```json
{
  "command": {
    "test": {
      "template": "Run all tests and report results",
      "description": "Execute test suite"
    }
  }
}
```

### Command File Format

Commands use **Markdown format** with YAML frontmatter.

### Metadata/Frontmatter

Commands support these frontmatter fields:

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `description` | No | String | Brief explanation shown in command list |
| `agent` | No | String | Agent to execute the command (e.g., `build`, `plan`) |
| `model` | No | String | Model override in `provider/model` format |
| `subtask` | No | Boolean | Execute in a separate child session |

```markdown
---
description: Run tests with coverage
agent: build
model: anthropic/claude-sonnet-4-20250514
subtask: true
---
Run all tests with coverage reporting.
Show a summary of results.
```

### Placeholders and Arguments

Command templates support several placeholder types:

#### Positional Arguments

- `$ARGUMENTS` - All arguments passed to the command
- `$1`, `$2`, `$3` - Individual positional arguments

#### Named Arguments

Use `$NAME` format (uppercase letters, numbers, underscores, must start with letter):

```markdown
---
description: Refactor a function
---
Refactor the function $FUNCTION_NAME in file $FILE_PATH
```

#### Shell Command Injection

Execute shell commands and inject output using backtick syntax:

```markdown
---
description: Review staged changes
---
Review these staged changes:
`git diff --staged`
```

#### File References

Include file content using `@filename` notation:

```markdown
---
description: Review configuration
---
Review this configuration file:
@config/settings.json
```

## Command Discovery

### Naming Convention

Command names derive from file paths relative to the command directory. Subdirectories create hierarchical names using forward slashes:

| File Path | Command |
|-----------|---------|
| `.opencode/command/test.md` | `/test` |
| `.opencode/command/review/security.md` | `/review/security` |
| `.opencode/command/refactor/extract.md` | `/refactor/extract` |

### Discovery Order

1. Global commands (`~/.config/opencode/command/`)
2. Project commands (`.opencode/command/`)

Project commands override global commands with the same name.

### Inline Model Override

Override the model at invocation time without modifying the command file:

```
/plan{model:anthropic/claude-sonnet-4} design auth system
```

Priority: inline `{model:...}` > frontmatter `model:` field.

## Context Files (AGENTS.md)

OpenCode uses `AGENTS.md` files for persistent project instructions:

- Generated via `/init` command
- Should be committed to version control
- Helps the agent understand project structure and coding patterns

## Platform-Specific Features

### Agents

OpenCode includes built-in agents:

- **Build**: Primary agent with full tool access (default)
- **Plan**: Primary agent with restricted permissions for analysis
- **General**: Subagent for research and multi-step tasks
- **Explore**: Subagent for fast codebase exploration

Custom agents can be defined in `.opencode/agent/` or `~/.config/opencode/agent/`.

### LSP Integration

Language Server Protocol support for code intelligence:

```json
{
  "lsp": {
    "go": {
      "command": "gopls"
    },
    "typescript": {
      "command": "typescript-language-server",
      "args": ["--stdio"]
    }
  }
}
```

### MCP Server Integration

Configure Model Context Protocol servers:

```json
{
  "mcp": {
    "my-server": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@my-org/mcp-server"],
      "env": {}
    }
  }
}
```

### Variable Substitution in Config

Reference environment variables: `{env:VARIABLE_NAME}`

Include file contents: `{file:path/to/file}`

## Key Differences from Claude Code

| Feature | OpenCode | Claude Code |
|---------|----------|-------------|
| Command format | Markdown with YAML frontmatter | Markdown with YAML frontmatter |
| Command directory | `.opencode/command/` | `.claude/commands/` |
| Context file | `AGENTS.md` | `CLAUDE.md` |
| Config format | JSON/JSONC (`opencode.json`) | JSON/YAML |
| Namespacing | Forward slash (`/`) | Colon (`:`) |
| Global config | `~/.config/opencode/` | `~/.claude/` |
| Argument placeholder | `$ARGUMENTS`, `$1`, `$2` | `$ARGUMENTS` |
