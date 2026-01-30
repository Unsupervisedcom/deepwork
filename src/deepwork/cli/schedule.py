"""Schedule command for DeepWork CLI."""

from pathlib import Path

import click
from rich.console import Console

from deepwork.cli.runners import ScheduleError, ScheduleRunner
from deepwork.utils.git import is_git_repo

console = Console()


@click.group()
def schedule() -> None:
    """Manage scheduled DeepWork jobs."""
    pass


@schedule.command()
@click.argument("task_name")
@click.argument("command")
@click.option(
    "--interval",
    "-i",
    default="daily",
    help="Schedule interval (systemd: 'daily', 'weekly', 'hourly'; launchd: seconds)",
)
@click.option(
    "--path",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=".",
    help="Path to project directory (default: current directory)",
)
def add(task_name: str, command: str, interval: str, path: Path) -> None:
    """Schedule a task to run periodically.

    TASK_NAME is a unique name for this scheduled task.
    COMMAND is the command to run (e.g., 'deepwork sync').
    """
    try:
        _add_schedule(task_name, command, interval, path)
    except ScheduleError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort() from e


def _add_schedule(task_name: str, command: str, interval: str, project_path: Path) -> None:
    """Add a scheduled task.

    Args:
        task_name: Name of the scheduled task
        command: Command to execute
        interval: Schedule interval
        project_path: Path to the project directory

    Raises:
        ScheduleError: If scheduling fails
    """
    console.print(f"\n[bold cyan]Scheduling DeepWork task: {task_name}[/bold cyan]\n")

    if not is_git_repo(project_path):
        raise ScheduleError("Not a Git repository. DeepWork requires a Git repository.")

    deepwork_dir = project_path / ".deepwork"
    if not deepwork_dir.exists():
        console.print(
            "[yellow]Warning:[/yellow] DeepWork not installed in this project. "
            "The scheduled command may not work correctly."
        )

    runner = ScheduleRunner.detect_runner()
    if runner is None:
        raise ScheduleError(
            "Unsupported system. DeepWork scheduling requires systemd (Linux) or launchd (macOS)."
        )

    console.print(f"[yellow]→[/yellow] Detected system: {runner.name}")
    console.print(f"[yellow]→[/yellow] Installing {runner.display_name}...")
    runner.install(task_name, command, project_path, interval)

    console.print()
    console.print(f"[bold green]✓ Task '{task_name}' scheduled successfully![/bold green]")
    console.print()


@schedule.command()
@click.argument("task_name")
@click.option(
    "--path",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=".",
    help="Path to project directory (default: current directory)",
)
def remove(task_name: str, path: Path) -> None:
    """Remove a scheduled task.

    TASK_NAME is the name of the task to unschedule.
    """
    try:
        _remove_schedule(task_name, path)
    except ScheduleError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort() from e


def _remove_schedule(task_name: str, project_path: Path) -> None:
    """Remove a scheduled task.

    Args:
        task_name: Name of the scheduled task to unschedule
        project_path: Path to the project directory

    Raises:
        ScheduleError: If unscheduling fails
    """
    console.print(f"\n[bold cyan]Removing scheduled task: {task_name}[/bold cyan]\n")

    runner = ScheduleRunner.detect_runner()
    if runner is None:
        raise ScheduleError(
            "Unsupported system. DeepWork scheduling requires systemd (Linux) or launchd (macOS)."
        )

    console.print(f"[yellow]→[/yellow] Detected system: {runner.name}")
    console.print(f"[yellow]→[/yellow] Removing {runner.display_name}...")
    runner.uninstall(task_name)

    console.print()
    console.print(f"[bold green]✓ Task '{task_name}' unscheduled successfully![/bold green]")
    console.print()


@schedule.command()
def list() -> None:
    """List all scheduled DeepWork tasks."""
    console.print("\n[bold cyan]Scheduled DeepWork Tasks[/bold cyan]\n")

    runner = ScheduleRunner.detect_runner()
    if runner is None:
        console.print("[yellow]No scheduled tasks (unsupported system)[/yellow]")
        return

    console.print(f"System: {runner.name}\n")
    runner.list_tasks()
