"""DeepWork hooks package for rules enforcement and lifecycle events.

This package provides:

1. Cross-platform hook system (Windows, macOS, Linux):
   - wrapper.py: Normalizes input/output between Claude Code and Gemini CLI
   - All hooks use Python modules for cross-platform compatibility

2. Hook implementations:
   - rules_check.py: Evaluates rules on after_agent events
   - user_prompt_submit.py: Captures work tree state on prompt submission
   - capture_prompt.py: Git work tree state capture utility

Usage:
    # Hooks are registered in .claude/settings.json by `deepwork sync`:
    {
      "hooks": {
        "Stop": [{
          "hooks": [{
            "type": "command",
            "command": "deepwork hook rules_check"
          }]
        }],
        "UserPromptSubmit": [{
          "hooks": [{
            "type": "command",
            "command": "deepwork hook user_prompt_submit"
          }]
        }]
      }
    }

The `deepwork hook <name>` command works on all platforms regardless
of how deepwork was installed (pip, pipx, uv, Windows EXE, etc.).

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
