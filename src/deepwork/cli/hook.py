"""Hook command for DeepWork CLI.

This command runs hook scripts, allowing hooks to use the `deepwork` CLI
instead of `python -m deepwork.hooks.*`, which works regardless of how
deepwork was installed (flake, pipx, uv, etc.).

Usage:
    deepwork hook <hook_name>

This is meant to be called from hook wrapper scripts (claude_hook.sh, gemini_hook.sh).
"""

import importlib
import sys

import click


class HookError(Exception):
    """Exception raised for hook errors."""

    pass


@click.command()
@click.argument("hook_name")
def hook(hook_name: str) -> None:
    """
    Run a DeepWork hook by name.

    HOOK_NAME: Name of the hook to run (e.g., 'my_hook')

    This command imports and runs the hook module from deepwork.hooks.{hook_name}.
    The hook receives stdin input and outputs to stdout, following the hook protocol.

    Examples:
        deepwork hook my_hook
        echo '{}' | deepwork hook my_hook
    """
    try:
        # Import the hook module
        # If the hook_name contains a dot, treat it as a full module path
        # Otherwise, assume it's a hook in the deepwork.hooks package
        if "." in hook_name:
            module_name = hook_name
        else:
            module_name = f"deepwork.hooks.{hook_name}"
        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError:
            raise HookError(
                f"Hook '{hook_name}' not found. Available hooks are in the deepwork.hooks package."
            ) from None

        # Run the hook's main function if it exists
        if hasattr(module, "main"):
            sys.exit(module.main())
        else:
            raise HookError(f"Hook module '{module_name}' does not have a main() function")

    except HookError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error running hook: {e}", err=True)
        sys.exit(1)
