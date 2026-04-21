# PLUG-REQ-004: Full Convo Memory Plugin

## Overview

The `full-convo-memory` plugin is a small Claude Code plugin shipped via the DeepWork marketplace. It provides a `search_conversation` skill and a companion `search_conversation.sh` script that run `jq` against the current Claude Code session's jsonl transcript so the agent can recall earlier turns without rereading the whole conversation. The script auto-detects the log file for both top-level sessions and sub-agents, filters out synthetic compaction-summary messages, and ends its output with a pointer line naming the exact log file path (so a caller can fall back to a semantic search via an Explore sub-agent when `jq` matching is insufficient).

## Requirements

### PLUG-REQ-004.1: Plugin Manifest

1. The plugin MUST provide a manifest at `plugins/full-convo-memory/.claude-plugin/plugin.json`.
2. The manifest `name` field MUST be `"full-convo-memory"`.
3. The manifest MUST include non-empty `description`, `version`, `author.name`, and `repository` fields.

### PLUG-REQ-004.2: Marketplace Registration

1. The plugin MUST be registered under the `plugins` array of `.claude-plugin/marketplace.json`.
2. The marketplace entry's `name` field MUST be `"full-convo-memory"`.
3. The marketplace entry's `source` field MUST be `"./plugins/full-convo-memory"`.
4. The marketplace entry MUST include `description`, `version`, `author`, `category`, `keywords`, `repository`, and `license` fields.

### PLUG-REQ-004.3: Plugin Root Directory Layout

1. The plugin root `plugins/full-convo-memory/` MUST contain `.claude-plugin/plugin.json`, `scripts/search_conversation.sh`, and `skills/search_conversation/SKILL.md`.

### PLUG-REQ-004.4: Search Script Existence and Shebang

1. The script MUST exist at `plugins/full-convo-memory/scripts/search_conversation.sh`.
2. The script MUST have the executable bit set for the owner.
3. The script's first line MUST be `#!/usr/bin/env bash`.

### PLUG-REQ-004.5: Zero-Argument Guard

1. When invoked with no positional arguments (and no `--log-file` option consumed), the script MUST print a usage message to stderr and exit with status `2` rather than invoking `jq` with no filter.

### PLUG-REQ-004.6: jq Dependency Check

1. If `jq` is not present on `PATH`, the script MUST write an error message to stderr and exit with status `127`.

### PLUG-REQ-004.7: Explicit Log-File Override

1. When invoked with `--log-file <path>` as the first argument, the script MUST use `<path>` as the log file and MUST remove both tokens from the argument list before forwarding the remainder to `jq`.
2. If `--log-file` is supplied without a path argument, the script MUST exit non-zero with an error message to stderr.

### PLUG-REQ-004.8: Sub-Agent Log-File Resolution

1. When `--log-file` is not provided and both `CLAUDE_CODE_SESSION_ID` and `CLAUDE_CODE_AGENT_ID` environment variables are set to non-empty values, the script MUST first try to resolve the log file to `$HOME/.claude/projects/<encoded-cwd>/$CLAUDE_CODE_SESSION_ID/subagents/agent-$CLAUDE_CODE_AGENT_ID.jsonl`, where `<encoded-cwd>` is `$PWD` with every `/` replaced by `-` (leading `-` preserved).
2. If the sub-agent path does not exist, resolution MUST fall through to PLUG-REQ-004.9.

### PLUG-REQ-004.9: Top-Level Session Log-File Resolution

1. When `--log-file` is not provided and the sub-agent path (PLUG-REQ-004.8) did not resolve but `CLAUDE_CODE_SESSION_ID` is set to a non-empty value, the script MUST try to resolve the log file to `$HOME/.claude/projects/<encoded-cwd>/$CLAUDE_CODE_SESSION_ID.jsonl`.
2. If the top-level path does not exist, resolution MUST fall through to PLUG-REQ-004.10.

### PLUG-REQ-004.10: Fallback Log-File Resolution

1. When neither `--log-file` nor the env-var paths yield an existing file, the script MUST select the most-recently-modified `*.jsonl` file located directly (non-recursively) inside `$HOME/.claude/projects/<encoded-cwd>/` as the log file.

### PLUG-REQ-004.11: Unresolvable Log File

1. If none of the strategies in PLUG-REQ-004.7 through PLUG-REQ-004.10 yield an existing file, the script MUST print a diagnostic to stderr that includes the values inspected for `CLAUDE_CODE_SESSION_ID`, `CLAUDE_CODE_AGENT_ID`, and the computed project directory, and MUST exit with status `1`.

### PLUG-REQ-004.12: Compaction-Summary Filter

1. Before running the caller's `jq` expression, the script MUST pre-filter transcript lines with the equivalent of `jq 'select(.isCompactSummary != true)'` so that entries with `isCompactSummary: true` are dropped and never reach the caller's filter.

### PLUG-REQ-004.13: jq Pass-Through

1. After the compaction pre-filter, the script MUST forward all remaining positional arguments to `jq` verbatim, supporting any `jq` flag or filter the caller provides.

### PLUG-REQ-004.14: Exit Code Propagation

1. The script's exit code MUST be the exit code of the caller's `jq` invocation (the right-hand side of the filter pipeline).
2. The pre-filter `jq` exit code MUST NOT propagate to the script's exit code.

### PLUG-REQ-004.15: Trailing Pointer Line

1. After running the `jq` pipeline, the script MUST print a final line to stdout of the form `If you want a more semantic search of the history, start an Explore agent and tell it what to look for in <LOG_FILE>`, where `<LOG_FILE>` is the absolute path of the resolved log file.
2. The trailing pointer line MUST be printed regardless of whether the caller's `jq` produced any matches.

### PLUG-REQ-004.16: Skill Location and Frontmatter

1. The skill MUST exist at `plugins/full-convo-memory/skills/search_conversation/SKILL.md`.
2. The skill's YAML frontmatter `name` field MUST be `"search_conversation"` (matching its directory name).
3. The skill's YAML frontmatter MUST include a non-empty `description` field.

### PLUG-REQ-004.17: Skill Documentation Content

1. The skill body MUST document the script path using the `${CLAUDE_PLUGIN_ROOT}` variable.
2. The skill body MUST state that any `jq` arguments are passed through verbatim.
3. The skill body MUST describe the log-file auto-detection order, explicitly covering the sub-agent case so a sub-agent invoking the skill searches its own transcript.
4. The skill body MUST state that compaction-summary messages are excluded automatically.
5. The skill body MUST include at least one worked `jq` example.
6. The skill body MUST direct the agent to use the printed log-file path with an Explore sub-agent when `jq` matching is insufficient.
