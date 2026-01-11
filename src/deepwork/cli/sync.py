"""Sync command for DeepWork CLI."""

from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from deepwork.core.detector import PLATFORMS
from deepwork.core.generator import CommandGenerator
from deepwork.core.parser import parse_job_definition
from deepwork.utils.fs import ensure_dir
from deepwork.utils.yaml_utils import load_yaml

console = Console()


class SyncError(Exception):
    """Exception raised for sync errors."""

    pass


@click.command()
@click.option(
    "--path",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=".",
    help="Path to project directory (default: current directory)",
)
def sync(path: Path) -> None:
    """
    Sync DeepWork commands to all configured platforms.

    Regenerates all slash-commands for job steps and core commands based on
    the current job definitions in .deepwork/jobs/.
    """
    try:
        sync_commands(path)
    except SyncError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort() from e
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        raise


def sync_commands(project_path: Path) -> None:
    """
    Sync commands to all configured platforms.

    Args:
        project_path: Path to project directory

    Raises:
        SyncError: If sync fails
    """
    project_path = Path(project_path)
    deepwork_dir = project_path / ".deepwork"

    # Load config
    config_file = deepwork_dir / "config.yml"
    if not config_file.exists():
        raise SyncError(
            "DeepWork not initialized in this project.\n"
            "Run 'deepwork install --platform <platform>' first."
        )

    config = load_yaml(config_file)
    if not config or "platforms" not in config:
        raise SyncError("Invalid config.yml: missing 'platforms' field")

    platforms = config["platforms"]
    if not platforms:
        raise SyncError(
            "No platforms configured.\n"
            "Run 'deepwork install --platform <platform>' to add a platform."
        )

    console.print("[bold cyan]Syncing DeepWork Commands[/bold cyan]\n")

    # Discover jobs
    jobs_dir = deepwork_dir / "jobs"
    if not jobs_dir.exists():
        job_dirs = []
    else:
        job_dirs = [d for d in jobs_dir.iterdir() if d.is_dir() and (d / "job.yml").exists()]

    console.print(f"[yellow]→[/yellow] Found {len(job_dirs)} job(s) to sync")

    # Parse all jobs
    jobs = []
    for job_dir in job_dirs:
        try:
            job_def = parse_job_definition(job_dir)
            jobs.append(job_def)
            console.print(f"  [green]✓[/green] Loaded {job_def.name} v{job_def.version}")
        except Exception as e:
            console.print(f"  [red]✗[/red] Failed to load {job_dir.name}: {e}")

    # Sync each platform
    generator = CommandGenerator()
    stats = {"platforms": 0, "core_commands": 0, "job_commands": 0}

    for platform_name in platforms:
        if platform_name not in PLATFORMS:
            console.print(f"[yellow]⚠[/yellow] Unknown platform '{platform_name}', skipping")
            continue

        platform_config = PLATFORMS[platform_name]
        console.print(f"\n[yellow]→[/yellow] Syncing to {platform_config.display_name}...")

        platform_dir = project_path / platform_config.config_dir
        commands_dir = platform_dir / platform_config.commands_dir

        # Create commands directory
        ensure_dir(commands_dir)

        # Generate core commands
        console.print(f"  [dim]•[/dim] Generating core commands...")
        try:
            core_paths = generator.generate_core_commands(platform_config, platform_dir)
            stats["core_commands"] += len(core_paths)
            for path in core_paths:
                rel_path = path.relative_to(project_path)
                console.print(f"    [green]✓[/green] {rel_path}")
        except Exception as e:
            console.print(f"    [red]✗[/red] Failed to generate core commands: {e}")
            continue

        # Generate job commands
        if jobs:
            console.print(f"  [dim]•[/dim] Generating job commands...")
            for job in jobs:
                try:
                    job_paths = generator.generate_all_commands(job, platform_config, platform_dir)
                    stats["job_commands"] += len(job_paths)
                    console.print(f"    [green]✓[/green] {job.name} ({len(job_paths)} commands)")
                except Exception as e:
                    console.print(f"    [red]✗[/red] Failed for {job.name}: {e}")

        stats["platforms"] += 1

    # Summary
    console.print()
    console.print("[bold green]✓ Sync complete![/bold green]")
    console.print()

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Metric", style="cyan")
    table.add_column("Count", style="green")

    table.add_row("Platforms synced", str(stats["platforms"]))
    table.add_row("Core commands", str(stats["core_commands"]))
    table.add_row("Job commands", str(stats["job_commands"]))
    table.add_row("Total commands", str(stats["core_commands"] + stats["job_commands"]))

    console.print(table)
    console.print()
