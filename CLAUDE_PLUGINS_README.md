# DeepWork Claude Code Plugins

This repository includes a Claude Code plugin marketplace with reusable plugins for AI-powered workflows.

## Available Plugins

| Plugin | Description |
|--------|-------------|
| **deepwork** | Framework for AI-powered multi-step workflows with quality gates |
| **learning-agents** | Auto-improving AI sub-agents that learn from their mistakes across sessions |

## Installation

### For this repository (local development)

Both plugins are configured via the marketplace in `.claude-plugin/marketplace.json` and enabled in `.claude/settings.json`. They load directly from their source directories, so any changes to plugin files are picked up without needing to reinstall from a remote marketplace.

No additional setup is needed — both plugins are enabled automatically when you work in this repo.

### For other projects (remote installation)

Run the following *in Claude*.

#### Add the marketplace
```
/plugin marketplace add https://github.com/Unsupervisedcom/deepwork
```

#### Install the deepwork plugin
```
/plugin install deepwork@deepwork-plugins
```

#### Install the learning-agents plugin
```
/plugin install learning-agents@deepwork-plugins
```

## Plugin Details

### deepwork

The deepwork plugin provides:
- **Skill**: `/deepwork` — starts or continues DeepWork workflows using MCP tools
- **MCP server**: Runs `uvx deepwork serve` to provide workflow management tools (`get_workflows`, `start_workflow`, `finished_step`, `abort_workflow`)
- **Hook**: SessionStart hook that checks DeepWork installation and Claude Code version

Source: `plugins/claude/`

### learning-agents

The learning-agents plugin provides auto-improving AI sub-agents. See [Learning Agents architecture](doc/learning_agents_architecture.md) for details.

Source: `learning_agents/`

## Learn More

- [Learning Agents architecture](doc/learning_agents_architecture.md)
- [Claude Code plugin docs](https://docs.anthropic.com/en/docs/claude-code/plugins)
