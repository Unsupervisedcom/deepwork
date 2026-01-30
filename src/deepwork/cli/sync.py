"""Sync command for DeepWork CLI."""

from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from deepwork.core.adapters import AgentAdapter
from deepwork.core.generator import SkillGenerator
from deepwork.core.hooks_syncer import collect_job_hooks, sync_hooks_to_platform
from deepwork.core.parser import parse_job_definition
from deepwork.utils.fs import ensure_dir
from deepwork.utils.paths import discover_all_jobs_dirs
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
    Sync DeepWork skills to all configured platforms.

    Regenerates all skills for job steps and core skills based on
    the current job definitions in .deepwork/jobs/.
    """
    try:
        sync_skills(path)
    except SyncError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort() from e
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        raise


def sync_skills(project_path: Path) -> None:
    """
    Sync skills to all configured platforms.

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

    console.print("[bold cyan]Syncing DeepWork Skills[/bold cyan]\n")

    # Discover jobs from both local and global locations
    job_dirs_with_location = discover_all_jobs_dirs(project_path)
    job_dirs = [job_dir for job_dir, _ in job_dirs_with_location]

    # Report discovered jobs by location
    local_count = sum(1 for _, loc in job_dirs_with_location if loc == "local")
    global_count = sum(1 for _, loc in job_dirs_with_location if loc == "global")
    
    console.print(f"[yellow]→[/yellow] Found {len(job_dirs)} job(s) to sync")
    if local_count > 0:
        console.print(f"  [dim]•[/dim] {local_count} local job(s)")
    if global_count > 0:
        console.print(f"  [dim]•[/dim] {global_count} global job(s)")

    # Parse all jobs
    jobs = []
    failed_jobs: list[tuple[str, str]] = []
    for job_dir in job_dirs:
        try:
            job_def = parse_job_definition(job_dir)
            jobs.append(job_def)
            console.print(f"  [green]✓[/green] Loaded {job_def.name} v{job_def.version}")
        except Exception as e:
            console.print(f"  [red]✗[/red] Failed to load {job_dir.name}: {e}")
            failed_jobs.append((job_dir.name, str(e)))

    # Fail early if any jobs failed to parse
    if failed_jobs:
        console.print()
        console.print("[bold red]Sync aborted due to job parsing errors:[/bold red]")
        for job_name, error in failed_jobs:
            console.print(f"  • {job_name}: {error}")
        raise SyncError(f"Failed to parse {len(failed_jobs)} job(s)")

    # Collect hooks from all jobs (both local and global)
    job_hooks_list = collect_job_hooks(project_path)
    if job_hooks_list:
        console.print(f"[yellow]→[/yellow] Found {len(job_hooks_list)} job(s) with hooks")

    # Sync each platform
    generator = SkillGenerator()
    stats = {"platforms": 0, "skills": 0, "hooks": 0}

    for platform_name in platforms:
        try:
            adapter_cls = AgentAdapter.get(platform_name)
        except Exception:
            console.print(f"[yellow]⚠[/yellow] Unknown platform '{platform_name}', skipping")
            continue

        adapter = adapter_cls(project_path)
        console.print(f"\n[yellow]→[/yellow] Syncing to {adapter.display_name}...")

        platform_dir = project_path / adapter.config_dir
        skills_dir = platform_dir / adapter.skills_dir

        # Create skills directory
        ensure_dir(skills_dir)

        # Generate skills for all jobs
        all_skill_paths: list[Path] = []
        if jobs:
            console.print("  [dim]•[/dim] Generating skills...")
            for job in jobs:
                try:
                    job_paths = generator.generate_all_skills(
                        job, adapter, platform_dir, project_root=project_path
                    )
                    all_skill_paths.extend(job_paths)
                    stats["skills"] += len(job_paths)
                    console.print(f"    [green]✓[/green] {job.name} ({len(job_paths)} skills)")
                except Exception as e:
                    console.print(f"    [red]✗[/red] Failed for {job.name}: {e}")

        # Sync hooks to platform settings
        if job_hooks_list:
            console.print("  [dim]•[/dim] Syncing hooks...")
            try:
                hooks_count = sync_hooks_to_platform(project_path, adapter, job_hooks_list)
                stats["hooks"] += hooks_count
                if hooks_count > 0:
                    console.print(f"    [green]✓[/green] Synced {hooks_count} hook(s)")
            except Exception as e:
                console.print(f"    [red]✗[/red] Failed to sync hooks: {e}")

        # Sync required permissions to platform settings
        console.print("  [dim]•[/dim] Syncing permissions...")
        try:
            perms_count = adapter.sync_permissions(project_path)
            if perms_count > 0:
                console.print(f"    [green]✓[/green] Added {perms_count} base permission(s)")
            else:
                console.print("    [dim]•[/dim] Base permissions already configured")
        except Exception as e:
            console.print(f"    [red]✗[/red] Failed to sync permissions: {e}")

        # Add skill permissions for generated skills (if adapter supports it)
        if all_skill_paths and hasattr(adapter, "add_skill_permissions"):
            try:
                skill_perms_count = adapter.add_skill_permissions(project_path, all_skill_paths)
                if skill_perms_count > 0:
                    console.print(
                        f"    [green]✓[/green] Added {skill_perms_count} skill permission(s)"
                    )
            except Exception as e:
                console.print(f"    [red]✗[/red] Failed to sync skill permissions: {e}")

        stats["platforms"] += 1

    # Summary
    console.print()
    console.print("[bold green]✓ Sync complete![/bold green]")
    console.print()

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Metric", style="cyan")
    table.add_column("Count", style="green")

    table.add_row("Platforms synced", str(stats["platforms"]))
    table.add_row("Total skills", str(stats["skills"]))
    if stats["hooks"] > 0:
        table.add_row("Hooks synced", str(stats["hooks"]))

    console.print(table)
    console.print()
