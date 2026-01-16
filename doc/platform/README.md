# Platform Documentation

This directory contains internal documentation about how different AI CLI platforms behave in ways that matter for DeepWork's hook system and adapter implementations.

## Purpose

These documents capture:

1. **Hook System Behavior** - Input/output formats, blocking mechanisms, event types
2. **Environment Variables** - What each platform provides to hook scripts
3. **Quirks and Edge Cases** - Platform-specific behaviors discovered during development
4. **Learnings** - Insights gained from implementing and testing adapters

## Adding Learnings

**IMPORTANT**: As you work on platform-specific code, document learnings here!

When you discover something about how a platform behaves that isn't obvious from official documentation, add it to the relevant platform's folder. Examples:

- "Gemini CLI's AfterAgent hook doesn't receive transcript_path when the session was resumed"
- "Claude Code's Stop hook JSON must have `decision: block` exactly, not `deny`"
- "Exit code 2 blocks in both platforms but stderr handling differs"

## Directory Structure

```
doc/platform/
├── README.md           # This file
├── claude/
│   ├── hooks.md        # Claude Code hooks system documentation
│   └── learnings.md    # Discovered behaviors and quirks
└── gemini/
    ├── hooks.md        # Gemini CLI hooks system documentation
    └── learnings.md    # Discovered behaviors and quirks
```

## Platform Comparison Summary

| Feature | Claude Code | Gemini CLI |
|---------|-------------|------------|
| Event: After agent | `Stop` | `AfterAgent` |
| Event: Before tool | `PreToolUse` | `BeforeTool` |
| Event: Before prompt | `UserPromptSubmit` | `BeforeAgent` |
| Project dir env var | `CLAUDE_PROJECT_DIR` | `GEMINI_PROJECT_DIR` |
| Block exit code | `2` | `2` |
| Block decision | `"block"` | `"deny"` or `"block"` |
| Input format | JSON via stdin | JSON via stdin |
| Output format | JSON via stdout | JSON via stdout |

## Related Files

- `src/deepwork/core/adapters.py` - Platform adapter implementations
- `src/deepwork/hooks/` - Hook wrapper scripts
- `doc/platforms/` - External platform documentation (configuration, commands)
