# DeepWork Hooks

This directory contains the cross-platform hook system for DeepWork. Hooks allow validating and controlling AI agent behavior during execution.

## Overview

The hook system provides:

1. **Platform-specific shell wrappers** that normalize input/output:
   - `claude_hook.sh` - For Claude Code
   - `gemini_hook.sh` - For Gemini CLI

2. **Common Python module** (`wrapper.py`) that handles:
   - Input normalization (event names, tool names, JSON structure)
   - Output denormalization (decision values, JSON structure)
   - Cross-platform compatibility

3. **Hook implementations**:
   - `policy_check.py` - Evaluates DeepWork policies on `after_agent` events

## Usage

### Registering Hooks

#### Claude Code (`.claude/settings.json`)

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "path/to/claude_hook.sh deepwork.hooks.policy_check"
          }
        ]
      }
    ]
  }
}
```

#### Gemini CLI (`.gemini/settings.json`)

```json
{
  "hooks": {
    "AfterAgent": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "path/to/gemini_hook.sh deepwork.hooks.policy_check"
          }
        ]
      }
    ]
  }
}
```

### Writing Custom Hooks

1. Create a new Python module in `deepwork/hooks/`:

```python
"""my_custom_hook.py - Example custom hook."""

import os
import sys

from deepwork.hooks.wrapper import (
    HookInput,
    HookOutput,
    NormalizedEvent,
    Platform,
    run_hook,
)


def my_hook(hook_input: HookInput) -> HookOutput:
    """Hook logic that works on any platform."""

    # Check the normalized event type
    if hook_input.event == NormalizedEvent.AFTER_AGENT:
        # Example: block if certain condition is met
        if some_condition():
            return HookOutput(
                decision="block",
                reason="Cannot complete until X is done"
            )

    elif hook_input.event == NormalizedEvent.BEFORE_TOOL:
        # Example: validate tool usage
        if hook_input.tool_name == "write_file":
            file_path = hook_input.tool_input.get("file_path", "")
            if "/secrets/" in file_path:
                return HookOutput(
                    decision="deny",
                    reason="Cannot write to secrets directory"
                )

    # Allow the action
    return HookOutput()


def main() -> None:
    """Entry point called by shell wrappers."""
    platform_str = os.environ.get("DEEPWORK_HOOK_PLATFORM", "claude")
    try:
        platform = Platform(platform_str)
    except ValueError:
        platform = Platform.CLAUDE

    exit_code = run_hook(my_hook, platform)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
```

2. Register the hook using the appropriate shell wrapper.

## Event Mapping

| DeepWork Normalized | Claude Code | Gemini CLI |
|---------------------|-------------|------------|
| `after_agent` | Stop | AfterAgent |
| `before_tool` | PreToolUse | BeforeTool |
| `after_tool` | PostToolUse | AfterTool |
| `before_prompt` | UserPromptSubmit | BeforeAgent |
| `session_start` | SessionStart | SessionStart |
| `session_end` | SessionEnd | SessionEnd |

## Tool Name Mapping

| Normalized | Claude Code | Gemini CLI |
|------------|-------------|------------|
| `write_file` | Write | write_file |
| `read_file` | Read | read_file |
| `edit_file` | Edit | edit_file |
| `shell` | Bash | shell |
| `glob` | Glob | glob |
| `grep` | Grep | grep |

## Decision Values

| Effect | Claude Code | Gemini CLI |
|--------|-------------|------------|
| Block action | `"block"` | `"deny"` (auto-converted) |
| Allow action | `"allow"` or `{}` | `"allow"` or `{}` |
| Deny tool use | `"deny"` | `"deny"` |

The wrapper automatically converts `"block"` to `"deny"` for Gemini CLI.

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success (allow action) |
| 2 | Blocking error (prevent action) |

## Testing

Run the hook wrapper tests:

```bash
pytest tests/unit/test_hook_wrapper.py -v
pytest tests/shell_script_tests/test_hook_wrappers.py -v
```

## Files

| File | Purpose |
|------|---------|
| `wrapper.py` | Cross-platform input/output normalization |
| `claude_hook.sh` | Shell wrapper for Claude Code |
| `gemini_hook.sh` | Shell wrapper for Gemini CLI |
| `policy_check.py` | Cross-platform policy evaluation hook |
