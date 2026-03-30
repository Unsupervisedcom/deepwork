"""Internal Codex hook entrypoints for DeepWork."""

from __future__ import annotations

import sys

import click

from deepwork.codex_hooks import CodexHookSetupError, run_codex_hook


@click.command(name="codex-hook", hidden=True)
@click.argument("hook_name", type=click.Choice(["session_start", "post_tool_use"]))
def codex_hook(hook_name: str) -> None:
    """Run a DeepWork Codex hook and emit the JSON response expected by Codex."""
    raw_input = sys.stdin.read() if not sys.stdin.isatty() else ""
    try:
        click.echo(run_codex_hook(hook_name, raw_input))
    except CodexHookSetupError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
