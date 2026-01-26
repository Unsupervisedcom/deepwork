#!/usr/bin/env python3
"""
Cross-platform hook entry point for DeepWork.

This module provides a cross-platform way to invoke DeepWork hooks
that works on Windows, macOS, and Linux without requiring bash.

Can be invoked directly:
    python -m deepwork.hooks.hook_entry rules_check

Or via the CLI:
    deepwork hook rules_check
"""

from __future__ import annotations

import sys


def main() -> int:
    """Main entry point for hook invocation."""
    # Import here to avoid circular imports and speed up module load
    from deepwork.cli.hook import hook

    # Get hook name from command line
    if len(sys.argv) < 2:
        print("Usage: python -m deepwork.hooks.hook_entry <hook_name>", file=sys.stderr)
        print("Example: python -m deepwork.hooks.hook_entry rules_check", file=sys.stderr)
        return 1

    hook_name = sys.argv[1]

    # Click expects sys.argv[0] to be the command name
    # We simulate: deepwork hook <hook_name>
    sys.argv = ["deepwork", hook_name]

    try:
        # Invoke the hook command with standalone_mode=False to get the return value
        result = hook.main(args=[hook_name], standalone_mode=False)
        return result if isinstance(result, int) else 0
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 0
    except Exception as e:
        print(f"Hook execution failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
