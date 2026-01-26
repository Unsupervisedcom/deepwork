"""Rules command for DeepWork CLI."""

import click
from rich.console import Console

from deepwork.core.rules_queue import RulesQueue

console = Console()


@click.group()
def rules() -> None:
    """Manage DeepWork rules and queue."""
    pass


@rules.command(name="clear_queue")
def clear_queue() -> None:
    """
    Clear all entries from the rules queue.

    Removes all JSON files from .deepwork/tmp/rules/queue/.
    This is useful for resetting the queue between tests or after
    manual verification of rule states.
    """
    queue = RulesQueue()
    count = queue.clear()

    if count == 0:
        console.print("[yellow]Queue is already empty[/yellow]")
    else:
        console.print(f"[green]Cleared {count} queue entry/entries[/green]")
