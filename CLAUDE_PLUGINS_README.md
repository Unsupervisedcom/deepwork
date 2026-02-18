# DeepWork Claude Code Plugins

This repository includes a Claude Code plugin marketplace with reusable plugins for AI-powered workflows.

## Available Plugins

| Plugin | Description |
|--------|-------------|
| **learning-agents** | Auto-improving AI sub-agents that learn from their mistakes across sessions |

## Installation

```
# Add the marketplace
/plugin marketplace add https://github.com/Unsupervisedcom/deepwork

# Install the learning-agents plugin
/plugin install learning-agents@deepwork-plugins

# Verify installation
/plugin list
```

## Learn More

- [Learning Agents architecture](doc/learning_agents_architecture.md)
- [Claude Code plugin docs](https://docs.anthropic.com/en/docs/claude-code/plugins)
