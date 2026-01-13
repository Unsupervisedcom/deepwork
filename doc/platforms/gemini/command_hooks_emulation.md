# Gemini CLI Command Hooks Emulation

## Overview

Gemini CLI doesn't natively support per-command hooks like Claude Code does. While Claude Code allows `stop_hooks` to be defined directly in command markdown frontmatter, Gemini only supports global/project-level hooks in `settings.json`.

This document describes DeepWork's solution for emulating command-level hooks in Gemini CLI using global hooks with command detection.

## The Problem

In Claude Code, jobs can define hooks per step that trigger at specific lifecycle events:

```yaml
# job.yml
steps:
  - id: define
    name: "Define Job"
    stop_hooks:  # Triggers when agent finishes
      - prompt: |
          Verify the output meets quality criteria...
```

These hooks are rendered into the command file's frontmatter and Claude Code respects them automatically.

Gemini CLI doesn't support this. Its TOML command files only support `prompt` and `description` fields. No hooks.

## The Solution

DeepWork provides a set of scripts that can be registered as **global** Gemini hooks (BeforeAgent/AfterAgent) which then:

1. Detect when a slash command is invoked
2. Look up the command's job.yml definition
3. Find any hooks defined for that step
4. Execute those hooks at the appropriate lifecycle point

### Architecture

```
src/deepwork/templates/gemini/scripts/command_hooks/
├── before_agent.sh          # BeforeAgent hook - detects commands
├── after_agent.sh           # AfterAgent hook - runs stop hooks
└── parse_command_hooks.py   # Shared logic for detection & execution
```

### Data Flow

```
┌─────────────────────┐
│ User runs /my:cmd   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────────────────────┐
│ BeforeAgent Hook (before_agent.sh)              │
│ 1. Receives user prompt from Gemini             │
│ 2. Detects slash command pattern (/job:step)   │
│ 3. Looks up job.yml for hooks                   │
│ 4. Saves state to .deepwork/.command_hook_state │
│ 5. Runs before_prompt hooks if any              │
└──────────┬──────────────────────────────────────┘
           │
           ▼
┌─────────────────────┐
│ Gemini Agent Works  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────────────────────┐
│ AfterAgent Hook (after_agent.sh)                │
│ 1. Reads state from .command_hook_state         │
│ 2. If slash command had after_agent hooks       │
│ 3. Runs those hooks (prompt or script)          │
│ 4. Clears state                                 │
└─────────────────────────────────────────────────┘
```

### State File

State is persisted between hooks in `.deepwork/.command_hook_state.json`:

```json
{
  "slash_command": "deepwork_jobs:define",
  "job_name": "deepwork_jobs",
  "step_id": "define",
  "job_yml_path": "/path/to/.deepwork/jobs/deepwork_jobs/job.yml",
  "hooks": {
    "before_prompt": [],
    "after_agent": [
      {
        "type": "prompt",
        "content": "Verify the output meets quality criteria..."
      }
    ]
  }
}
```

If no slash command is detected, `slash_command` is `null`.

## Installation

### 1. Copy Scripts to Project

The scripts are stored in DeepWork's template directory. To use them in a project:

```bash
# Create the scripts directory
mkdir -p .gemini/scripts/command_hooks

# Copy scripts (or symlink them)
cp -r $(python -c "import deepwork; print(deepwork.__path__[0])")/templates/gemini/scripts/command_hooks/* \
      .gemini/scripts/command_hooks/
```

### 2. Configure Gemini Hooks

Add the hooks to `.gemini/settings.json`:

```json
{
  "hooks": {
    "enabled": true,
    "BeforeAgent": [
      {
        "hooks": [
          {
            "name": "deepwork-command-hooks-before",
            "type": "command",
            "command": ".gemini/scripts/command_hooks/before_agent.sh",
            "timeout": 30000
          }
        ]
      }
    ],
    "AfterAgent": [
      {
        "hooks": [
          {
            "name": "deepwork-command-hooks-after",
            "type": "command",
            "command": ".gemini/scripts/command_hooks/after_agent.sh",
            "timeout": 30000
          }
        ]
      }
    ]
  }
}
```

### 3. Ensure Python is Available

The scripts require Python 3.8+ with the `deepwork` package installed (for finding job definitions) and `PyYAML` (for parsing job.yml).

## Script Details

### parse_command_hooks.py

The core logic module. Provides a CLI for:

**Detect Command**
```bash
# Detect slash command from prompt text
python parse_command_hooks.py detect --prompt "User said /deepwork_jobs:define"

# Or pipe JSON from Gemini hook:
echo '{"prompt": "/deepwork_jobs:define"}' | python parse_command_hooks.py detect
```

Output:
```json
{
  "slash_command": "deepwork_jobs:define",
  "job_name": "deepwork_jobs",
  "step_id": "define",
  "has_hooks": true
}
```

**Get Hooks**
```bash
# Get hooks for a lifecycle event
python parse_command_hooks.py get-hooks --event after_agent
```

**Run Hooks**
```bash
# Execute hooks for an event
python parse_command_hooks.py run-hooks --event after_agent --transcript-path /path/to/transcript.jsonl
```

Output:
```json
{
  "executed": 1,
  "success": true,
  "results": [
    {
      "type": "prompt",
      "success": true,
      "output": "[Prompt hook content ready for injection]",
      "inject_prompt": "Verify the output meets quality criteria..."
    }
  ],
  "inject_prompt": "Verify the output meets quality criteria..."
}
```

**Get/Clear State**
```bash
# View current state
python parse_command_hooks.py get-state

# Clear state
python parse_command_hooks.py clear
```

### before_agent.sh

Called by Gemini's BeforeAgent hook. Responsibilities:

1. Read JSON input from stdin (Gemini hook format)
2. Call `parse_command_hooks.py detect` to find slash commands
3. If command found with hooks, save state
4. Run any `before_prompt` hooks
5. Exit with appropriate code

### after_agent.sh

Called by Gemini's AfterAgent hook. Responsibilities:

1. Read JSON input from stdin (may contain transcript path)
2. Call `parse_command_hooks.py get-state` to check for saved command
3. If command had `after_agent` hooks, run them
4. Output prompt content for quality validation
5. Clear state
6. Exit with appropriate code

## Hook Types

### Prompt Hooks

Inline prompts or prompt files that get injected back into the conversation:

```yaml
# In job.yml
stop_hooks:
  - prompt: |
      Verify the output meets these criteria:
      1. Has all required sections
      2. No placeholder text
      If met, respond with <promise>QUALITY_COMPLETE</promise>
```

When executed, the prompt content is output by the after_agent hook, which Gemini will show to the user/agent as context.

### Script Hooks

Shell scripts that run programmatic validation:

```yaml
# In job.yml
stop_hooks:
  - script: hooks/validate_output.sh
```

Scripts receive:
- Environment variable `TRANSCRIPT_PATH` with session transcript location
- Current working directory is project root

Exit codes:
- `0`: Success
- `2`: Blocking error (operation may be blocked)
- Other: Warning (logged, continues)

## Supported Lifecycle Events

| Event | Trigger Point | Use Case |
|-------|--------------|----------|
| `before_prompt` | After user submits, before agent processes | Session setup, context injection |
| `after_agent` | After agent finishes responding | Quality validation, output verification |

Note: The `before_tool` event is not currently emulated as it requires tool-level interception which Gemini's global hooks don't support well.

## Limitations

### 1. No Tool-Level Hooks

Claude's `PreToolUse` hooks can intercept individual tool calls. Gemini's global hooks fire at the agent loop level, not per-tool. The `before_tool` event is not emulated.

### 2. Prompt Injection Timing

The `after_agent` hook runs *after* the agent has finished. Unlike Claude's stop hooks which can force the agent to continue working, Gemini's implementation shows the validation prompt but relies on the user to instruct the agent to continue if needed.

### 3. State File Dependency

The solution relies on filesystem state (`.deepwork/.command_hook_state.json`). This works for single-session workflows but may have edge cases with parallel sessions.

### 4. Python Dependency

Requires Python 3.8+ with PyYAML. The scripts won't work in environments without Python.

## Comparison with Claude Code

| Capability | Claude Code | Gemini (Emulated) |
|------------|-------------|-------------------|
| Per-command hooks | Native | Emulated via global hooks |
| stop_hooks | Native | Emulated via AfterAgent |
| before_prompt | Native | Emulated via BeforeAgent |
| before_tool | Native (PreToolUse) | Not supported |
| Prompt injection | Direct in frontmatter | Via hook output |
| Script hooks | Native | Emulated |
| Automatic continuation | Yes (loop until quality) | No (manual) |

## Troubleshooting

### Hooks Not Firing

1. Check that scripts are executable: `chmod +x .gemini/scripts/command_hooks/*.sh`
2. Verify `settings.json` hook configuration
3. Check that `hooks.enabled` is `true` in settings.json
4. Look for errors in Gemini CLI output

### Command Not Detected

1. Verify slash command format: `/job_name:step_id` or `/job_name/step_id`
2. Check that job.yml exists at `.deepwork/jobs/{job_name}/job.yml`
3. Run detection manually: `python parse_command_hooks.py detect --prompt "your prompt"`

### State File Issues

1. Check `.deepwork/.command_hook_state.json` for contents
2. Clear state manually: `python parse_command_hooks.py clear`
3. Ensure `.deepwork/` directory exists

## Future Improvements

1. **Automatic Installation**: Have `deepwork sync` automatically set up the Gemini hooks
2. **Better Prompt Injection**: Explore Gemini CLI APIs for more seamless prompt injection
3. **Tool Hook Emulation**: Investigate if BeforeTool hooks could be mapped
4. **Multi-Session Support**: Use session IDs in state file names
