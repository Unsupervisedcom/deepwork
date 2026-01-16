"""DeepWork hooks package for policy enforcement and lifecycle events.

This package provides:

1. Cross-platform hook wrapper system:
   - wrapper.py: Normalizes input/output between Claude Code and Gemini CLI
   - claude_hook.sh: Shell wrapper for Claude Code hooks
   - gemini_hook.sh: Shell wrapper for Gemini CLI hooks

2. Hook implementations:
   - policy_check.py: Evaluates policies on after_agent events
   - evaluate_policies.py: Legacy policy evaluation (Claude-specific)

Usage with wrapper system:
    # Register hook in .claude/settings.json:
    {
      "hooks": {
        "Stop": [{
          "hooks": [{
            "type": "command",
            "command": ".deepwork/hooks/claude_hook.sh deepwork.hooks.policy_check"
          }]
        }]
      }
    }

    # Register hook in .gemini/settings.json:
    {
      "hooks": {
        "AfterAgent": [{
          "hooks": [{
            "type": "command",
            "command": ".gemini/hooks/gemini_hook.sh deepwork.hooks.policy_check"
          }]
        }]
      }
    }

Writing custom hooks:
    from deepwork.hooks.wrapper import (
        HookInput,
        HookOutput,
        NormalizedEvent,
        Platform,
        run_hook,
    )

    def my_hook(input: HookInput) -> HookOutput:
        if input.event == NormalizedEvent.AFTER_AGENT:
            if should_block():
                return HookOutput(decision="block", reason="Complete X first")
        return HookOutput()

    if __name__ == "__main__":
        import os, sys
        platform = Platform(os.environ.get("DEEPWORK_HOOK_PLATFORM", "claude"))
        sys.exit(run_hook(my_hook, platform))
"""

from deepwork.hooks.wrapper import (
    HookInput,
    HookOutput,
    NormalizedEvent,
    Platform,
    denormalize_output,
    normalize_input,
    run_hook,
)

__all__ = [
    "HookInput",
    "HookOutput",
    "NormalizedEvent",
    "Platform",
    "normalize_input",
    "denormalize_output",
    "run_hook",
]
