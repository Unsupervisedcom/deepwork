"""Port command for moving jobs between local and global locations."""

import shutil
from pathlib import Path

import click
from rich.console import Console

from deepwork.utils.paths import (
    discover_all_jobs_dirs,
    ensure_global_jobs_dir,
    get_global_jobs_dir,
    get_local_jobs_dir,
    is_job_global,
)

console = Console()


class PortError(Exception):
    """Exception raised for port errors."""

    pass


@click.command()
@click.argument("job_name", type=str)
@click.option(
    "--to",
    type=click.Choice(["local", "global"], case_sensitive=False),
    required=True,
    help="Destination: local or global",
)
@click.option(
    "--path",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=".",
    help="Path to project directory (default: current directory)",
)
def port(job_name: str, to: str, path: Path) -> None:
    """
    Port a job between local and global locations.

    Examples:
        deepwork port my_job --to global
        deepwork port my_job --to local
    """
    try:
        _port_job(job_name, to.lower(), path)
    except PortError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort() from e
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        raise


def _port_job(job_name: str, destination: str, project_path: Path) -> None:
    """
    Port a job between local and global locations.

    Args:
        job_name: Name of the job to port
        destination: Target location ("local" or "global")
        project_path: Path to project directory

    Raises:
        PortError: If port fails
    """
    console.print(f"\n[bold cyan]Porting Job: {job_name}[/bold cyan]\n")

    # Find the job
    job_dirs_with_location = discover_all_jobs_dirs(project_path)
    source_job_dir = None
    source_location = None

    for job_dir, location in job_dirs_with_location:
        if job_dir.name == job_name:
            source_job_dir = job_dir
            source_location = location
            break

    if source_job_dir is None:
        raise PortError(
            f"Job '{job_name}' not found in local or global locations.\n"
            "Run 'deepwork sync' to see available jobs."
        )

    # Check if already in destination
    if source_location == destination:
        console.print(
            f"[yellow]⚠[/yellow] Job '{job_name}' is already in {destination} location"
        )
        return

    # Determine destination path
    if destination == "global":
        ensure_global_jobs_dir()
        dest_dir = get_global_jobs_dir() / job_name
        console.print(f"[yellow]→[/yellow] Moving from local to global...")
    else:  # destination == "local"
        local_jobs_dir = get_local_jobs_dir(project_path)
        local_jobs_dir.mkdir(parents=True, exist_ok=True)
        dest_dir = local_jobs_dir / job_name
        console.print(f"[yellow]→[/yellow] Moving from global to local...")

    # Check if destination already exists
    if dest_dir.exists():
        raise PortError(
            f"Job '{job_name}' already exists at destination: {dest_dir}\n"
            "Please remove or rename the existing job first."
        )

    # Copy the job directory
    try:
        shutil.copytree(source_job_dir, dest_dir)
        console.print(f"  [green]✓[/green] Copied to {dest_dir}")
    except Exception as e:
        raise PortError(f"Failed to copy job directory: {e}") from e

    # Remove the source directory
    try:
        shutil.rmtree(source_job_dir)
        console.print(f"  [green]✓[/green] Removed from {source_job_dir}")
    except Exception as e:
        # Try to clean up the destination if we can't remove source
        try:
            shutil.rmtree(dest_dir)
        except Exception:
            pass
        raise PortError(f"Failed to remove source directory: {e}") from e

    # Success message
    console.print()
    console.print(f"[bold green]✓ Job '{job_name}' ported to {destination}![/bold green]")
    console.print()
    console.print("[bold]Next steps:[/bold]")
    console.print("  • Run [cyan]deepwork sync[/cyan] to regenerate skills")
    console.print()
