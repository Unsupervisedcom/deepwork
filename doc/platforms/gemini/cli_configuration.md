<!--
Last Updated: 2026-01-12
Source: https://google-gemini.github.io/gemini-cli/docs/get-started/configuration.html
        https://geminicli.com/docs/cli/custom-commands/
        https://github.com/google-gemini/gemini-cli
-->

# Gemini CLI Configuration

## Overview

Gemini CLI is an open-source AI agent from Google that brings Gemini directly into your terminal for coding, problem-solving, and task management. It uses a reason-and-act (ReAct) loop with built-in tools and supports Model Context Protocol (MCP) servers for extensibility.

## Configuration Files

Gemini CLI uses JSON-based configuration with a hierarchical precedence system.

### File Locations

Configuration is applied in this order (lowest to highest priority):

| Priority | File Type | Linux/macOS | Windows |
|----------|-----------|-------------|---------|
| 1 | Default values | Hardcoded | Hardcoded |
| 2 | System defaults | `/etc/gemini-cli/system-defaults.json` | `C:\ProgramData\gemini-cli\system-defaults.json` |
| 3 | User settings | `~/.gemini/settings.json` | `~/.gemini/settings.json` |
| 4 | Project settings | `.gemini/settings.json` | `.gemini/settings.json` |
| 5 | System settings | `/etc/gemini-cli/settings.json` | `C:\ProgramData\gemini-cli\settings.json` |
| 6 | Environment variables | System or `.env` file | System or `.env` file |
| 7 | Command-line arguments | Runtime flags | Runtime flags |

### Configuration Format

The `settings.json` uses nested category objects. A JSON schema is available at:
`https://raw.githubusercontent.com/google-gemini/gemini-cli/main/schemas/settings.schema.json`

Key configuration categories include:

- **general**: Core behavior (vimMode, preferredEditor, checkpointing)
- **model**: Model selection, session turn limits, compression thresholds
- **context**: Context file discovery and filtering
- **tools**: Sandbox configuration, tool discovery, hooks enablement
- **mcp**: Model Context Protocol server configurations
- **security**: YOLO mode, tool approval, folder trust
- **hooks**: Hook system activation and event-specific hook arrays

## Custom Commands/Skills

Custom commands allow you to create personalized shortcuts for your most-used prompts.

### Command Location

Commands are discovered from two locations with specific precedence:

1. **Global commands**: `~/.gemini/commands/` - Available across all projects
2. **Project commands**: `<project-root>/.gemini/commands/` - Project-specific, can be version-controlled

Project commands override identically-named global commands.

### Command File Format

Commands use **TOML format** with `.toml` extension.

### Metadata/Frontmatter

Commands support two fields:

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `prompt` | Yes | String | The prompt sent to Gemini (single or multi-line) |
| `description` | No | String | One-line description shown in `/help` menu |

```toml
# Example: ~/.gemini/commands/refactor/pure.toml
# Invoked via: /refactor:pure

description = "Refactors code into pure functions."

prompt = """
Please analyze the code I've provided in the current context.
Refactor it into a pure function.

Your response should include:
1. The refactored, pure function code block.
2. A brief explanation of the key changes you made.
"""
```

### Argument Handling

Custom commands support several methods for dynamic content:

#### 1. Argument Injection with `{{args}}`

When `{{args}}` appears in the prompt, it's replaced with user-provided text:

```toml
prompt = "Review the following code: {{args}}"
```

- Outside shell blocks: Arguments inject raw as typed
- Inside `!{...}` blocks: Arguments are automatically shell-escaped

#### 2. Shell Command Execution with `!{...}`

Execute shell commands and inject their output:

```toml
prompt = """
Here are the staged changes:
!{git diff --staged}

Please review and suggest a commit message.
"""
```

#### 3. File Content Injection with `@{...}`

Embed file or directory content:

```toml
prompt = """
Review this configuration:
@{config/settings.json}
"""
```

Features:
- Supports multimodal input (images, PDFs, audio, video)
- Directory traversal respects `.gitignore` and `.geminiignore`

## Command Discovery

### Naming & Namespacing

Command names derive from file paths relative to the commands directory. Subdirectories create namespaced commands using colons:

| File Path | Command |
|-----------|---------|
| `~/.gemini/commands/test.toml` | `/test` |
| `<project>/.gemini/commands/git/commit.toml` | `/git:commit` |
| `<project>/.gemini/commands/review/pr.toml` | `/review:pr` |

### Discovery Order

1. User global commands (`~/.gemini/commands/`)
2. Project commands (`<project>/.gemini/commands/`)

Project commands take precedence over global commands with the same name.

## Context Files (GEMINI.md)

Context files provide persistent instructions to the model:

### Loading Hierarchy

1. **Global context**: `~/.gemini/GEMINI.md` - Instructions for all projects
2. **Project root & ancestors**: Searches from current directory up to `.git` or home
3. **Subdirectories**: Scans below current working directory (limit: 200 dirs)

The CLI concatenates all discovered files with origin separators. Use `/memory refresh` to reload and `/memory show` to inspect.

### Modular Imports

Supports `@path/to/file.md` syntax for including other files.

## Platform-Specific Features

### Shell History

Per-project shell history stored at: `~/.gemini/tmp/<project_hash>/shell_history`

### Sandboxing

Enable via:
- `--sandbox` flag
- `GEMINI_SANDBOX` environment variable
- `tools.sandbox` setting in settings.json

Custom Dockerfile support at `.gemini/sandbox.Dockerfile`.

### MCP Server Integration

Configure MCP servers in settings.json:

```json
{
  "mcpServers": {
    "my-server": {
      "command": "npx",
      "args": ["-y", "@my-org/mcp-server"],
      "includeTools": ["tool1", "tool2"]
    }
  }
}
```

## Key Differences from Claude Code

| Feature | Gemini CLI | Claude Code |
|---------|------------|-------------|
| Command format | TOML | Markdown |
| Command directory | `.gemini/commands/` | `.claude/commands/` |
| Context file | `GEMINI.md` | `CLAUDE.md` |
| Config format | JSON (`settings.json`) | JSON/YAML |
| Namespacing | Colon (`:`) | Dot (`.`) |
