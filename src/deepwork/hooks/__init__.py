"""DeepWork hooks package for rules enforcement and lifecycle events.

This package provides:

1. Cross-platform hook wrapper system:
   - wrapper.py: Normalizes input/output between Claude Code and Gemini CLI
   - claude_hook.sh: Shell wrapper for Claude Code hooks
   - gemini_hook.sh: Shell wrapper for Gemini CLI hooks

2. Hook implementations:
   - rules_check.py: Evaluates rules on after_agent events

Usage with wrapper system:
    # Register hook in .claude/settings.json:
    {
      "hooks": {
        "Stop": [{
          "hooks": [{
            "type": "command",
            "command": ".deepwork/hooks/claude_hook.sh rules_check"
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
            "command": ".gemini/hooks/gemini_hook.sh rules_check"
          }]
        }]
      }
    }

The shell wrappers call `deepwork hook <hook_name>` which works regardless
of how deepwork was installed (pipx, uv, nix flake, etc.).

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

    def main():
        import os, sys
        platform = Platform(os.environ.get("DEEPWORK_HOOK_PLATFORM", "claude"))
        sys.exit(run_hook(my_hook, platform))

    if __name__ == "__main__":
        main()
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
