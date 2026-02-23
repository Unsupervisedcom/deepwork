<!--
Last Updated: 2026-01-16
Source: https://docs.anthropic.com/en/docs/claude-code/settings
        https://docs.anthropic.com/en/docs/claude-code/slash-commands
-->

# Claude Code CLI Configuration

## Overview

Claude Code is Anthropic's official CLI for Claude, providing an agentic coding assistant that runs in your terminal. It uses markdown-based slash commands and JSON-based configuration files.

## Configuration Files

Claude Code uses JSON-based settings with a hierarchical precedence system.

### File Locations

Configuration is applied in this order (lowest to highest priority):

| Priority | File Type | Path |
|----------|-----------|------|
| 1 | Default values | Hardcoded |
| 2 | User settings | `~/.claude/settings.json` |
| 3 | Project settings | `.claude/settings.json` |
| 4 | Local settings | `.claude/settings.local.json` |
| 5 | Managed policy | Enterprise policies |

### Configuration Format

The `settings.json` file uses a flat JSON structure:

```json
{
  "permissions": {
    "allow": ["Bash(npm test)", "Read"],
    "deny": ["Bash(rm -rf)"]
  },
  "hooks": {
    "Stop": [...],
    "PreToolUse": [...]
  },
  "env": {
    "NODE_ENV": "development"
  }
}
```

Key configuration sections:

- **permissions**: Tool access control (allow/deny patterns)
- **hooks**: Lifecycle hook configurations
- **env**: Environment variables for the session
- **apiKeyHelper**: Custom API key provider script

## Custom Commands/Slash Commands

Custom commands allow you to create reusable prompts and workflows.

### Command Location

Commands are discovered from:

1. **Global commands**: `~/.claude/commands/` - Available across all projects
2. **Project commands**: `<project-root>/.claude/commands/` - Project-specific

Project commands override identically-named global commands.

### Command File Format

Commands use **Markdown format** with `.md` extension and YAML frontmatter.

### Metadata/Frontmatter

Commands support these frontmatter fields:

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `description` | No | String | One-line description shown in `/help` |
| `hooks` | No | Object | Lifecycle hooks for this command |

```markdown
---
description: Review code for security issues
hooks:
  Stop:
    - hooks:
        - type: prompt
          prompt: Verify all security issues are addressed
---

# security-review

Review the following code for security vulnerabilities:

$ARGUMENTS
```

### Argument Handling

#### 1. Argument Injection with `$ARGUMENTS`

The `$ARGUMENTS` placeholder is replaced with user-provided text:

```markdown
---
description: Explain a concept
---

Explain the following in simple terms: $ARGUMENTS
```

Usage: `/explain recursion`

#### 2. File Content Injection

Reference files by path in the command arguments:

```
/review src/main.js
```

Claude will read the file content automatically.

## Command Discovery

### Naming & Namespacing

Command names derive from file paths relative to the commands directory. Dots create namespaced commands:

| File Path | Command |
|-----------|---------|
| `~/.claude/commands/test.md` | `/test` |
| `.claude/commands/git.commit.md` | `/git.commit` |
| `.claude/commands/review.security.md` | `/review.security` |

### Discovery Order

1. Built-in commands (prefixed with `/`)
2. User global commands (`~/.claude/commands/`)
3. Project commands (`<project>/.claude/commands/`)

Project commands take precedence over global commands with the same name.

## Context Files (CLAUDE.md)

Context files provide persistent instructions to the model.

### Loading Hierarchy

1. **Global context**: `~/.claude/CLAUDE.md` - Instructions for all projects
2. **Project root**: `./CLAUDE.md` - Project-specific context
3. **Subdirectories**: `./subdir/CLAUDE.md` - Directory-specific context

The CLI concatenates all discovered files. Files in the current working directory and its ancestors are loaded.

## Platform-Specific Features

### Permission System

Claude Code uses a permission system for tool access:

```json
{
  "permissions": {
    "allow": [
      "Bash(npm *)",
      "Read",
      "Write(*.md)"
    ],
    "deny": [
      "Bash(rm -rf *)"
    ]
  }
}
```

Patterns support:
- Exact matches: `"Bash(npm test)"`
- Wildcards: `"Bash(npm *)"`
- Tool-only: `"Read"` (allows all Read operations)

### Session Management

- `claude` - Start new session
- `claude --resume` - Resume last session
- `claude --continue` - Continue with specific prompt

### Environment Variables

Set via settings or `.env` file:

```json
{
  "env": {
    "NODE_ENV": "development",
    "DEBUG": "true"
  }
}
```

### MCP Server Integration

Configure Model Context Protocol servers:

```json
{
  "mcpServers": {
    "my-server": {
      "command": "npx",
      "args": ["-y", "@my-org/mcp-server"]
    }
  }
}
```

## Key Differences from Gemini CLI

| Feature | Claude Code | Gemini CLI |
|---------|-------------|------------|
| Command format | Markdown | TOML |
| Command directory | `.claude/commands/` | `.gemini/commands/` |
| Context file | `CLAUDE.md` | `GEMINI.md` |
| Config format | JSON (`settings.json`) | JSON (`settings.json`) |
| Namespacing | Dot (`.`) | Colon (`:`) |
| Command-level hooks | Yes | No |
| Argument placeholder | `$ARGUMENTS` | `{{args}}` |

## DeepWork Integration

DeepWork integrates with Claude Code through the **plugin system**:

1. **Plugin installation** adds skills (`/deepwork`, `/deepwork:review`, `/deepwork:configure_reviews`), MCP server config, and hooks
2. **MCP server** (`uvx deepwork serve`) is the core runtime — all workflow state management happens through MCP tool calls
3. **Skills** invoke MCP tools (`get_workflows`, `start_workflow`, `finished_step`) to drive multi-step workflows
4. **Reviews** are configured via `.deepreview` files and run through `get_review_instructions` MCP tool

### Plugin Structure

```
plugins/claude/
├── .claude-plugin/plugin.json   # Plugin metadata
├── skills/
│   ├── deepwork/SKILL.md        # Main workflow skill
│   ├── review/SKILL.md          # Run automated reviews
│   └── configure_reviews/SKILL.md  # Set up review rules
├── hooks/hooks.json             # Hook configuration
└── .mcp.json                    # MCP server config (uvx deepwork serve)
```

## References

- [Claude Code Documentation](https://docs.anthropic.com/en/docs/claude-code)
- [Claude Code Settings](https://docs.anthropic.com/en/docs/claude-code/settings)
- [Claude Code Slash Commands](https://docs.anthropic.com/en/docs/claude-code/slash-commands)
