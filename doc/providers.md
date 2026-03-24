# Providers

DeepWork's core (job discovery, review pipeline, MCP server) is platform-agnostic. Platform-specific behavior lives in thin adapter layers: **formatters** for review output, **skills** for user-facing commands, and **hooks** for lifecycle events. This document describes the current provider landscape and how to set up each one.

## Claude Code (full support)

Claude Code is the primary supported platform with plugin-based delivery.

### What ships

| Component | Description |
|-----------|-------------|
| Skills | `/deepwork`, `/review`, `/configure_reviews` |
| Hooks | Post-commit reminder, post-compact context restore, startup context |
| MCP server | Bundled via `.mcp.json` — starts automatically |
| Reviews | Parallel dispatch via Task/Agent tool |

### Setup

Install the plugin from the marketplace:

```
/plugin marketplace add https://github.com/Unsupervisedcom/deepwork
/plugin install deepwork@deepwork-plugins
```

No further configuration is required. The plugin registers skills, hooks, and the MCP server automatically.

## Gemini CLI (partial support)

Gemini CLI supports DeepWork workflows and sequential reviews. Hooks are not yet implemented.

### What ships

| Component | Description |
|-----------|-------------|
| Skills | `/deepwork`, `/review`, `/configure_reviews` (TOML custom commands) |
| Hooks | Not yet supported |
| MCP server | Manual configuration required |
| Reviews | Sequential execution (no parallel subagent dispatch) |

### Setup

#### 1. Configure the MCP server

Add the DeepWork MCP server to your project's `.gemini/settings.json`:

```json
{
  "mcpServers": {
    "deepwork": {
      "command": "uvx",
      "args": ["deepwork", "serve", "--platform", "gemini"]
    }
  }
}
```

Or to your global `~/.gemini/settings.json` if you want it available across all projects.

#### 2. Install skills as custom commands

Copy the TOML skill files from `plugins/gemini/skills/` into your Gemini commands directory:

```bash
# Project-level (version-controlled)
cp -r plugins/gemini/skills/* .gemini/commands/

# Or global
cp -r plugins/gemini/skills/* ~/.gemini/commands/
```

Each skill becomes a slash command: `/deepwork`, `/review`, `/configure_reviews`.

### Review limitations

- Reviews execute sequentially — Gemini CLI has no equivalent to Claude Code's Agent/Task tool for parallel subagent dispatch.
- The `agent` persona field in `.deepreview` rules is ignored (Gemini CLI does not support named agent types).
- No post-commit hooks to remind you to run reviews after committing.

## Other MCP-compatible CLIs

Any AI CLI that supports the Model Context Protocol can use DeepWork's core functionality by configuring the MCP server manually. The MCP server exposes all workflow and review tools regardless of platform.

### Minimum requirements

1. **MCP client support** — the CLI must be able to connect to an MCP server via stdio transport.
2. **File read/write** — the agent needs filesystem access to read instruction files and write work products.
3. **Git access** — review detection relies on `git diff` against the merge base.

### Generic MCP setup

Point your CLI's MCP configuration at:

```
command: uvx
args: ["deepwork", "serve", "--platform", "<platform-name>"]
```

If no formatter exists for `<platform-name>`, the server returns an error. Use `claude` or `gemini` as the platform value, or add a custom formatter (see below).

## Adding a new provider

To add first-class support for a new AI CLI platform:

1. **Formatter** — add a `format_for_<platform>()` function in `src/deepwork/review/formatter.py` and register it in the `FORMATTERS` dict in `src/deepwork/review/mcp.py`.
2. **Skills** — create skill files in `plugins/<platform>/skills/` matching the platform's command format.
3. **MCP config** — document how to configure the MCP server for the platform.
4. **Hooks** (optional) — implement hook wrappers in `src/deepwork/hooks/` if the platform supports lifecycle hooks.
5. **Tests** — add formatter tests in `tests/unit/review/test_formatter.py`.
