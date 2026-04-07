"""CLI command: deepwork setup."""

from pathlib import Path

import click


@click.command()
def setup() -> None:
    """Configure the current environment for DeepWork.

    Detects installed AI agent platforms and ensures their settings
    include the DeepWork marketplace, plugin, and MCP permissions.
    """
    claude_dir = Path.home() / ".claude"
    if claude_dir.is_dir():
        from deepwork.setup.claude import claude_setup

        changes = claude_setup()
        if changes:
            click.echo("Claude Code — updated ~/.claude/settings.json:")
            for change in changes:
                click.echo(f"  • {change}")
        else:
            click.echo("Claude Code — already configured, no changes needed.")
    else:
        click.echo("No supported AI agent platforms detected (~/.claude not found).")
