# DeepWork Claude Code Plugin

This directory contains the Claude Code plugin distribution for DeepWork.

## About

DeepWork is a framework for enabling AI agents to perform complex, multi-step work tasks. This plugin provides seamless integration with Claude Code through namespaced skills and automated hooks.

## Installation

### Using Plugin Directory Flag (Development/Testing)

```bash
claude --plugin-dir /path/to/deepwork
```

### From GitHub Repository

```bash
# Install from GitHub
claude plugin install https://github.com/Unsupervisedcom/deepwork
```

### From Local Clone

```bash
# Clone the repository
git clone https://github.com/Unsupervisedcom/deepwork
cd deepwork

# Install as plugin
claude plugin install .
```

## Plugin Structure

```
deepwork/
├── .claude-plugin/
│   └── plugin.json         # Plugin manifest
├── commands/
│   ├── install/COMMAND.md  # /deepwork:install command
│   └── sync/COMMAND.md     # /deepwork:sync command
├── skills/
│   ├── install/SKILL.md    # Agent skill for auto-detection
│   └── sync/SKILL.md       # Agent skill for auto-sync
└── hooks/
    └── hooks.json          # Event hooks configuration
```

## Available Commands

After installation, the following skills are available:

### `/deepwork:install`
Install DeepWork in a project. Adds AI platform support and syncs commands for configured platforms.

**Usage:**
```
/deepwork:install
```

This will:
- Check for Git repository
- Auto-detect available AI platforms
- Create `.deepwork/` directory structure
- Install core job definitions
- Generate platform-specific skills
- Configure hooks for rules enforcement

### `/deepwork:sync`
Sync DeepWork job definitions to platform-specific skills.

**Usage:**
```
/deepwork:sync
```

This will:
- Read configuration from `.deepwork/config.yml`
- Scan all jobs in `.deepwork/jobs/`
- Generate skills for each configured platform
- Update hooks in platform settings

## Hooks

The plugin automatically configures the following hooks:

- **SessionStart**: Version check
- **UserPromptSubmit**: Rules queue management
- **Stop/SubagentStop**: Rules validation

## Requirements

- Python 3.11 or higher
- Git repository
- DeepWork CLI tool installed (`pip install deepwork`)

## Prerequisites

Before using the plugin, install the DeepWork CLI tool:

```bash
# Using pipx (recommended)
pipx install deepwork

# Or using pip
pip install deepwork

# Or using uv
uv tool install deepwork
```

## Next Steps

1. Use `/deepwork:install` to set up DeepWork in your project
2. Define your first job with `/deepwork_jobs.define`
3. Implement the job with `/deepwork_jobs.implement`
4. Run job steps with `/your_job_name.step_name`

## Documentation

- [Main README](../README.md)
- [Architecture](../doc/architecture.md)
- [Contributing](../CONTRIBUTING.md)
- [License](../LICENSE.md)

## Support

- Issues: https://github.com/Unsupervisedcom/deepwork/issues
- Documentation: https://github.com/Unsupervisedcom/deepwork#readme

## License

Business Source License 1.1 (BSL 1.1)

See [LICENSE.md](../LICENSE.md) for details.

## Testing the Plugin Locally

To test the plugin structure before distribution:

```bash
# From the DeepWork repository root
claude --plugin-dir /path/to/deepwork

# In Claude Code, test the commands:
/deepwork:install --help
/deepwork:sync --help
```

You should see the commands available with the `deepwork:` namespace prefix.

## Plugin Development Notes

### Directory Structure Requirements

Claude Code plugins must follow this structure:
- `.claude-plugin/plugin.json` (required) - Plugin manifest
- `commands/` (optional) - User-invocable slash commands
- `skills/` (optional) - Agent Skills invoked automatically
- `hooks/` (optional) - Event hooks configuration
- `.mcp.json` (optional) - MCP server configurations
- `.lsp.json` (optional) - LSP server configurations

### Command Files

Command files in `commands/[name]/COMMAND.md`:
- Are user-invocable as `/plugin-name:command-name`
- Should NOT have YAML frontmatter
- Should be descriptive markdown with usage examples

### Skill Files

Skill files in `skills/[name]/SKILL.md`:
- Have YAML frontmatter with `name` and `description`
- Are invoked automatically by Claude based on context
- Should include clear usage guidelines

### Hooks Configuration

The `hooks/hooks.json` file configures event handlers:
- **SessionStart**: Run when Claude Code session begins
- **UserPromptSubmit**: Run when user submits a prompt
- **Stop/SubagentStop**: Run when agent completes a task
- **PreToolUse**: Run before tool invocation
- **PostToolUse**: Run after tool invocation

