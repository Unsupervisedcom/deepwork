"""Jobs command for DeepWork CLI."""

import shutil
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import click
from git import Repo
from rich.console import Console
from rich.table import Table

from deepwork.cli.sync import SyncError, sync_skills
from deepwork.core.parser import ParseError, parse_job_definition
from deepwork.utils.fs import ensure_dir, fix_permissions

console = Console()


class JobsError(Exception):
    """Exception raised for jobs command errors."""

    pass


def _is_github_url(source: str) -> bool:
    """
    Check if source is a GitHub URL.

    Args:
        source: Source path or URL

    Returns:
        True if source is a GitHub URL, False otherwise
    """
    try:
        parsed = urlparse(source)
        # Check for exact match on github.com or GitHub Enterprise subdomains
        is_github = (
            parsed.scheme in ("http", "https")
            and (parsed.netloc == "github.com" or parsed.netloc.endswith(".github.com"))
        )
        return is_github
    except ValueError:
        return False


def _get_deepwork_default_library() -> Path:
    """
    Get the default library/jobs path from the deepwork package.

    Returns:
        Path to library/jobs in deepwork package
    """
    # Try to find the library/jobs in the deepwork package
    deepwork_root = Path(__file__).parent.parent.parent.parent
    library_path = deepwork_root / "library" / "jobs"

    if library_path.exists():
        return library_path

    # Fallback: try to clone from GitHub
    raise JobsError(
        "Could not find library/jobs in deepwork package. "
        "Please specify a source path or URL."
    )


def _resolve_source(source: str | None) -> Path:
    """
    Resolve source to a local path, cloning if necessary.

    Args:
        source: Source path, URL, or None (default to deepwork library)

    Returns:
        Path to the jobs directory

    Raises:
        JobsError: If source cannot be resolved
    """
    if source is None:
        # Default to deepwork library/jobs
        return _get_deepwork_default_library()

    # Check if it's a local path
    source_path = Path(source)
    if source_path.exists():
        if source_path.is_dir():
            # If pointing to a repo root, look for jobs in standard locations
            if (source_path / ".deepwork" / "jobs").exists():
                return source_path / ".deepwork" / "jobs"
            if (source_path / "library" / "jobs").exists():
                return source_path / "library" / "jobs"
            # If pointing directly to a jobs directory
            return source_path
        raise JobsError(f"Source path exists but is not a directory: {source}")

    # Check if it's a GitHub URL
    if _is_github_url(source):
        # Clone to temporary directory
        console.print(f"[yellow]→[/yellow] Cloning repository from {source}...")
        tmp_dir = Path(tempfile.mkdtemp(prefix="deepwork_jobs_"))
        try:
            from git import GitCommandError

            Repo.clone_from(source, tmp_dir, depth=1)
            console.print("  [green]✓[/green] Repository cloned")

            # Look for jobs in standard locations (in order of priority)
            if (tmp_dir / ".deepwork" / "jobs").exists():
                return tmp_dir / ".deepwork" / "jobs"

            if (tmp_dir / "library" / "jobs").exists():
                return tmp_dir / "library" / "jobs"

            # Look for a jobs directory at the root
            if (tmp_dir / "jobs").exists():
                return tmp_dir / "jobs"

            # Clean up if jobs not found
            shutil.rmtree(tmp_dir, ignore_errors=True)
            raise JobsError(
                "Could not find jobs in cloned repository. "
                "Expected '.deepwork/jobs', 'library/jobs', or 'jobs' directory."
            )
        except GitCommandError as e:
            shutil.rmtree(tmp_dir, ignore_errors=True)
            raise JobsError(f"Failed to clone repository: {e}") from e
        except JobsError:
            # Re-raise our own errors
            raise
        except Exception as e:
            # Cleanup and wrap any other unexpected errors
            shutil.rmtree(tmp_dir, ignore_errors=True)
            raise JobsError(f"Unexpected error accessing repository: {e}") from e

    raise JobsError(
        f"Source not found: {source}\n"
        "Provide a local path or GitHub URL (e.g., https://github.com/owner/repo)"
    )


def _discover_jobs(jobs_path: Path) -> list[tuple[str, Path]]:
    """
    Discover all jobs in a directory.

    Args:
        jobs_path: Path to jobs directory

    Returns:
        List of (job_name, job_path) tuples
    """
    jobs: list[tuple[str, Path]] = []

    if not jobs_path.exists():
        return jobs

    for item in jobs_path.iterdir():
        if item.is_dir():
            job_yml = item / "job.yml"
            if job_yml.exists():
                jobs.append((item.name, item))

    return sorted(jobs, key=lambda x: x[0])


@click.group()
def jobs() -> None:
    """Manage jobs from libraries and repositories."""
    pass


@jobs.command(name="list")
@click.argument("source", required=False)
def list_jobs(source: str | None) -> None:
    """
    List available jobs from a repository.

    SOURCE can be:
    - A local path to a repository or jobs directory
    - A GitHub URL (e.g., https://github.com/owner/repo)
    - Omitted to use the deepwork library (default)

    Examples:
        deepwork jobs list
        deepwork jobs list /path/to/repo
        deepwork jobs list https://github.com/owner/repo
    """
    try:
        console.print("\n[bold cyan]Available Jobs[/bold cyan]\n")

        # Resolve source
        jobs_path = _resolve_source(source)

        if source is None:
            console.print("[dim]Source: deepwork library/jobs (default)[/dim]\n")
        else:
            console.print(f"[dim]Source: {source}[/dim]\n")

        # Discover jobs
        discovered_jobs = _discover_jobs(jobs_path)

        if not discovered_jobs:
            console.print("[yellow]No jobs found in source.[/yellow]")
            return

        # Parse and display jobs
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Name", style="green")
        table.add_column("Version", style="blue")
        table.add_column("Summary")

        for job_name, job_path in discovered_jobs:
            try:
                job_def = parse_job_definition(job_path)
                table.add_row(job_def.name, job_def.version, job_def.summary)
            except ParseError as e:
                # Expected error when job definition is invalid
                table.add_row(job_name, "[red]error[/red]", f"Failed to parse: {e}")

        console.print(table)
        console.print()
        console.print("[dim]To clone a job, run: deepwork jobs clone <job-name>[/dim]")
        console.print()

    except JobsError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort() from e
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        raise


@jobs.command()
@click.argument("job_name")
@click.argument("source", required=False)
@click.option(
    "--path",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=".",
    help="Path to target project directory (default: current directory)",
)
def clone(job_name: str, source: str | None, path: Path) -> None:
    """
    Clone a job from a repository to the current project.

    JOB_NAME is the name of the job to clone.

    SOURCE can be:
    - A local path to a repository or jobs directory
    - A GitHub URL (e.g., https://github.com/owner/repo)
    - Omitted to use the deepwork library (default)

    Examples:
        deepwork jobs clone commit
        deepwork jobs clone my-job /path/to/repo
        deepwork jobs clone my-job https://github.com/owner/repo
    """
    try:
        console.print("\n[bold cyan]Cloning Job[/bold cyan]\n")

        # Check if project has DeepWork installed
        project_path = Path(path).resolve()
        deepwork_dir = project_path / ".deepwork"

        if not deepwork_dir.exists():
            raise JobsError(
                "DeepWork not initialized in this project.\n"
                "Run 'deepwork install --platform <platform>' first."
            )

        # Resolve source
        console.print("[yellow]→[/yellow] Resolving source...")
        jobs_path = _resolve_source(source)

        if source is None:
            console.print("  [dim]Using deepwork library/jobs (default)[/dim]")
        else:
            console.print(f"  [dim]Using {source}[/dim]")

        # Find the job
        source_job_path = jobs_path / job_name
        if not source_job_path.exists():
            raise JobsError(
                f"Job '{job_name}' not found in source.\n"
                "Run 'deepwork jobs list' to see available jobs."
            )

        if not (source_job_path / "job.yml").exists():
            raise JobsError(
                f"Invalid job: {job_name} (missing job.yml)"
            )

        console.print(f"  [green]✓[/green] Found job '{job_name}'")

        # Validate job definition
        console.print("[yellow]→[/yellow] Validating job definition...")
        try:
            job_def = parse_job_definition(source_job_path)
            console.print(f"  [green]✓[/green] {job_def.name} v{job_def.version}")
        except ParseError as e:
            raise JobsError(f"Invalid job definition: {e}") from e

        # Check if job already exists
        target_job_path = deepwork_dir / "jobs" / job_name
        if target_job_path.exists():
            console.print(
                f"[yellow]⚠[/yellow] Job '{job_name}' already exists in project"
            )
            if not click.confirm("Overwrite existing job?", default=False):
                console.print("[dim]Clone cancelled.[/dim]")
                return
            shutil.rmtree(target_job_path)

        # Copy job to project
        console.print("[yellow]→[/yellow] Copying job to project...")
        ensure_dir(deepwork_dir / "jobs")
        shutil.copytree(source_job_path, target_job_path)
        fix_permissions(target_job_path)
        console.print(f"  [green]✓[/green] Copied to {target_job_path.relative_to(project_path)}")

        # Run sync
        console.print("\n[yellow]→[/yellow] Syncing skills...")

        try:
            sync_skills(project_path)
        except SyncError as e:
            console.print(f"[yellow]⚠[/yellow] Sync failed: {e}")
            console.print("[dim]Run 'deepwork sync' manually to generate skills.[/dim]")

        # Success
        console.print()
        console.print(f"[bold green]✓ Job '{job_name}' cloned successfully![/bold green]")
        console.print()
        console.print("[bold]Next steps:[/bold]")
        console.print(f"  1. Review the job definition: {target_job_path.relative_to(project_path)}/job.yml")
        console.print(f"  2. Use the job with: [cyan]/{job_def.name}[/cyan]")
        console.print()

    except JobsError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort() from e
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        raise
