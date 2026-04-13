# LA-REQ-001: Plugin Structure and Metadata

## Overview

The learning-agents plugin is a Claude Code plugin distributed via the DeepWork marketplace. This document specifies the requirements for plugin packaging, metadata, and top-level directory layout.

## Requirements

### LA-REQ-001.1: Plugin Manifest

The plugin MUST provide a `.claude-plugin/plugin.json` file at the plugin root containing:
- `name` set to `"learning-agents"`
- `description` as a non-empty string
- `version` in semver format (e.g., `"0.1.0"`)
- `author.name` as a non-empty string
- `repository` as a valid URL string

### LA-REQ-001.2: Marketplace Registration

The plugin MUST be registered in the repository's `.claude-plugin/marketplace.json` under the `plugins` array with:
- `name` matching the plugin manifest name (`"learning-agents"`)
- `source` pointing to the plugin root directory relative to the repository root
- `category` set to `"learning"`

### LA-REQ-001.3: Plugin Root Directory Layout

The plugin root directory MUST contain the following subdirectories:
- `.claude-plugin/` -- plugin manifest
- `agents/` -- agent definition files used by the plugin itself
- `doc/` -- reference documentation for the plugin's domain concepts
- `hooks/` -- hook definitions and scripts
- `scripts/` -- executable utility scripts
- `skills/` -- skill definitions

### LA-REQ-001.4: Hooks Configuration

The plugin MUST provide a `hooks/hooks.json` file that declares:
- A `PostToolUse` hook with matcher `"Task"` that executes `post_task.sh`
- A `Stop` hook with empty matcher (`""`) that executes `session_stop.sh`

### LA-REQ-001.5: Hook Script References

Hook commands in `hooks.json` MUST reference scripts using `${CLAUDE_PLUGIN_ROOT}` as the base path prefix so they resolve correctly regardless of installation location.

### LA-REQ-001.6: Hook Scripts Exit Code

All hook scripts (`post_task.sh`, `session_stop.sh`) MUST always exit with code 0 to ensure they are non-blocking. A hook script MUST NOT cause the host CLI session to fail.

### LA-REQ-001.7: Hook Scripts Output Format

All hook scripts MUST write valid JSON to stdout. When there is nothing to communicate, the script MUST output `{}`. When there is a message, the script MUST output a JSON object with a `systemMessage` string field.

### LA-REQ-001.8: Meta-Agent Definition

The plugin MUST provide an `agents/learning-agent-expert.md` file that defines a meta-agent with expertise in the LearningAgent system. This agent definition MUST include dynamic context injection commands (using `!` backtick syntax) that load all reference documentation from `${CLAUDE_PLUGIN_ROOT}/doc/`.
