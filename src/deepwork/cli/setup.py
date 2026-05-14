"""CLI command: deepwork setup."""

import webbrowser
from pathlib import Path

import click


@click.command()
def setup() -> None:
    """Configure the current environment for DeepWork.

    Detects installed AI agent platforms and ensures their settings
    include the DeepWork package/plugin and platform permissions.
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
    pi_dir = Path.home() / ".pi" / "agent"
    if pi_dir.is_dir():
        from deepwork.setup.pi import pi_setup

        changes = pi_setup()
        if changes:
            click.echo("Pi CLI — updated ~/.pi/agent/settings.json:")
            for change in changes:
                click.echo(f"  • {change}")
        else:
            click.echo("Pi CLI — already configured, no changes needed.")

    if not claude_dir.is_dir() and not pi_dir.is_dir():
        click.echo("No supported AI agent platforms detected (~/.claude or ~/.pi/agent not found).")

    webbrowser.open("https://www.deepwork.md/success")
