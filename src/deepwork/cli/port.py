"""Port command for moving jobs between scopes and sources."""

import shutil
from pathlib import Path

import click
from rich.console import Console
from rich.prompt import Prompt

from deepwork.utils.fs import ensure_dir, fix_permissions
from deepwork.utils.job_location import JobScope, get_jobs_dir
from deepwork.utils.xdg import ensure_global_jobs_dir

console = Console()


class PortError(Exception):
    """Exception raised for port errors."""

    pass


@click.command()
@click.option(
    "--path",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=".",
    help="Path to project directory (default: current directory)",
)
def port(path: Path) -> None:
    """
    Port a DeepWork job between local and global scopes.

    Allows you to move a job from local project storage to global storage
    (or vice versa), or import jobs from other sources.
    """
    try:
        _port_job(path)
    except PortError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort() from e
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        raise


def _port_job(project_path: Path) -> None:
    """
    Port a job between scopes or from other sources.

    Args:
        project_path: Path to project directory

    Raises:
        PortError: If porting fails
    """
    console.print("\n[bold cyan]DeepWork Job Porting[/bold cyan]\n")

    # Step 1: Ask where to port FROM
    console.print("[yellow]→[/yellow] Select source location:")
    console.print("  1. Local project (.deepwork/jobs/)")
    console.print("  2. Global user config (~/.config/deepwork/jobs/)")
    console.print("  3. Standard DeepWork library (src/deepwork/standard_jobs/)")
    console.print("  4. GitHub remote (not yet implemented)")
    console.print()

    source_choice = Prompt.ask(
        "Source", choices=["1", "2", "3", "4"], default="1", show_choices=False
    )

    # Determine source directory
    if source_choice == "1":
        source_dir = get_jobs_dir(project_path, JobScope.LOCAL)
        source_name = "local project"
    elif source_choice == "2":
        source_dir = get_jobs_dir(project_path, JobScope.GLOBAL)
        source_name = "global user config"
    elif source_choice == "3":
        # Find standard jobs in the installed package
        import deepwork.standard_jobs

        standard_jobs_dir = Path(deepwork.standard_jobs.__file__).parent
        source_dir = standard_jobs_dir
        source_name = "standard library"
    else:  # choice == "4"
        raise PortError(
            "GitHub remote import is not yet implemented. "
            "Please manually clone the job or request this feature."
        )

    if not source_dir.exists():
        raise PortError(f"Source directory does not exist: {source_dir}")

    # Step 2: List available jobs in source
    console.print(f"\n[yellow]→[/yellow] Available jobs in {source_name}:")
    available_jobs = [
        d for d in source_dir.iterdir() if d.is_dir() and (d / "job.yml").exists()
    ]

    if not available_jobs:
        raise PortError(f"No jobs found in {source_name}")

    for i, job_dir in enumerate(available_jobs, 1):
        console.print(f"  {i}. {job_dir.name}")

    console.print()
    job_index = Prompt.ask(
        "Select job number",
        choices=[str(i) for i in range(1, len(available_jobs) + 1)],
        default="1",
        show_choices=False,
    )

    selected_job = available_jobs[int(job_index) - 1]
    job_name = selected_job.name

    console.print(f"\n[green]✓[/green] Selected: {job_name}")

    # Step 3: Ask where to port TO
    console.print("\n[yellow]→[/yellow] Select destination:")
    console.print("  1. Local project (.deepwork/jobs/)")
    console.print("  2. Global user config (~/.config/deepwork/jobs/)")
    console.print()

    dest_choice = Prompt.ask("Destination", choices=["1", "2"], default="1", show_choices=False)

    # Determine destination directory
    if dest_choice == "1":
        dest_scope = JobScope.LOCAL
        dest_name = "local project"
    else:
        dest_scope = JobScope.GLOBAL
        dest_name = "global user config"
        ensure_global_jobs_dir()

    dest_dir = get_jobs_dir(project_path, dest_scope)
    ensure_dir(dest_dir)

    dest_job_path = dest_dir / job_name

    # Step 4: Check if destination already exists
    if dest_job_path.exists():
        console.print(f"\n[yellow]⚠[/yellow] Job '{job_name}' already exists in {dest_name}")
        overwrite = Prompt.ask("Overwrite?", choices=["y", "n"], default="n")
        if overwrite.lower() != "y":
            console.print("[dim]Porting cancelled.[/dim]")
            return
        shutil.rmtree(dest_job_path)

    # Step 5: Copy the job
    console.print(f"\n[yellow]→[/yellow] Copying job to {dest_name}...")

    try:
        shutil.copytree(selected_job, dest_job_path)
        fix_permissions(dest_job_path)
        console.print(f"  [green]✓[/green] Job copied to {dest_job_path}")
    except Exception as e:
        raise PortError(f"Failed to copy job: {e}") from e

    # Step 6: Success message
    console.print()
    console.print(f"[bold green]✓ Successfully ported {job_name} to {dest_name}![/bold green]")
    console.print()
    console.print("[bold]Next steps:[/bold]")
    console.print("  1. Run [cyan]deepwork sync[/cyan] to regenerate skills")
    console.print(
        f"  2. The job is now available in {dest_name} ({dest_job_path.relative_to(project_path) if dest_scope == JobScope.LOCAL else dest_job_path})"
    )
    console.print()
