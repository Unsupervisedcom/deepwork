"""Sync command for DeepWork CLI."""

import shutil
from dataclasses import dataclass, field
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from deepwork.core.adapters import AgentAdapter
from deepwork.core.generator import SkillGenerator
from deepwork.core.hooks_syncer import collect_job_hooks, sync_hooks_to_platform
from deepwork.core.jobs import get_job_folders
from deepwork.core.parser import parse_job_definition
from deepwork.utils.fs import ensure_dir
from deepwork.utils.yaml_utils import load_yaml

console = Console()


class SyncError(Exception):
    """Exception raised for sync errors."""

    pass


@dataclass
class SyncResult:
    """Result of a sync operation."""

    platforms_synced: int = 0
    skills_generated: int = 0
    hooks_synced: int = 0
    warnings: list[str] = field(default_factory=list)

    @property
    def has_warnings(self) -> bool:
        """Return True if there were any warnings during sync."""
        return len(self.warnings) > 0


def _migrate_remove_synced_standard_jobs(deepwork_dir: Path) -> None:
    """Remove standard jobs that were previously synced into .deepwork/jobs/.

    Standard jobs are now loaded directly from the package source, so the
    copied ``deepwork_jobs`` folder inside ``.deepwork/jobs/`` is no longer
    needed.  This helper silently removes it when present to keep existing
    installs tidy.
    """
    synced_standard = deepwork_dir / "jobs" / "deepwork_jobs"
    if synced_standard.exists():
        try:
            shutil.rmtree(synced_standard)
            console.print(
                "  [dim]•[/dim] Removed legacy .deepwork/jobs/deepwork_jobs (now loaded from package)"
            )
        except OSError:
            pass  # best-effort cleanup


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


def sync_skills(project_path: Path) -> SyncResult:
    """
    Sync skills to all configured platforms.

    Args:
        project_path: Path to project directory

    Returns:
        SyncResult with statistics and any warnings

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

    # Generate /deepwork skill FIRST for all platforms (before parsing jobs)
    # This ensures the skill is available even if some jobs fail to parse
    generator = SkillGenerator()
    result = SyncResult()
    platform_adapters: list[AgentAdapter] = []
    all_skill_paths_by_platform: dict[str, list[Path]] = {}

    console.print("[yellow]→[/yellow] Generating /deepwork skill...")
    for platform_name in platforms:
        try:
            adapter_cls = AgentAdapter.get(platform_name)
        except Exception:
            warning = f"Unknown platform '{platform_name}', skipping"
            console.print(f"  [yellow]⚠[/yellow] {warning}")
            result.warnings.append(warning)
            continue

        adapter = adapter_cls(project_path)
        platform_adapters.append(adapter)

        platform_dir = project_path / adapter.config_dir
        skills_dir = platform_dir / adapter.skills_dir
        ensure_dir(skills_dir)

        all_skill_paths: list[Path] = []
        try:
            deepwork_skill_path = generator.generate_deepwork_skill(adapter, platform_dir)
            all_skill_paths.append(deepwork_skill_path)
            result.skills_generated += 1
            console.print(f"  [green]✓[/green] {adapter.display_name}: deepwork (MCP entry point)")
        except Exception as e:
            warning = f"{adapter.display_name}: Failed to generate /deepwork skill: {e}"
            console.print(f"  [red]✗[/red] {warning}")
            result.warnings.append(warning)

        all_skill_paths_by_platform[platform_name] = all_skill_paths

    # Migration: remove synced standard jobs from .deepwork/jobs/ since they
    # are now loaded directly from the package's standard_jobs directory.
    _migrate_remove_synced_standard_jobs(deepwork_dir)

    # Discover jobs from all configured job folders
    job_folders = get_job_folders(project_path)
    job_dirs: list[Path] = []
    seen_names: set[str] = set()
    for folder in job_folders:
        if not folder.exists() or not folder.is_dir():
            continue
        for d in sorted(folder.iterdir()):
            if d.is_dir() and (d / "job.yml").exists() and d.name not in seen_names:
                job_dirs.append(d)
                seen_names.add(d.name)

    console.print(f"\n[yellow]→[/yellow] Found {len(job_dirs)} job(s) to sync")

    # Parse all jobs
    jobs = []
    failed_jobs: list[tuple[str, str]] = []
    for job_dir in job_dirs:
        try:
            job_def = parse_job_definition(job_dir)
            jobs.append(job_def)
            console.print(f"  [green]✓[/green] Loaded {job_def.name} v{job_def.version}")
        except Exception as e:
            warning = f"Failed to load {job_dir.name}: {e}"
            console.print(f"  [red]✗[/red] {warning}")
            failed_jobs.append((job_dir.name, str(e)))
            result.warnings.append(warning)

    # Warn about failed jobs but continue (skill already installed)
    if failed_jobs:
        console.print()
        console.print("[bold yellow]Warning: Some jobs failed to parse:[/bold yellow]")
        for job_name, error in failed_jobs:
            console.print(f"  • {job_name}: {error}")
        console.print(
            "[dim]The /deepwork skill is installed. Fix the job errors and run 'deepwork sync' again.[/dim]"
        )

    # Collect hooks from jobs across all job folders
    job_hooks_list: list = []
    seen_hook_jobs: set[str] = set()
    for folder in job_folders:
        if not folder.exists() or not folder.is_dir():
            continue
        for jh in collect_job_hooks(folder):
            if jh.job_name not in seen_hook_jobs:
                job_hooks_list.append(jh)
                seen_hook_jobs.add(jh.job_name)
    if job_hooks_list:
        console.print(f"\n[yellow]→[/yellow] Found {len(job_hooks_list)} job(s) with hooks")

    # Sync hooks and permissions for each platform
    for adapter in platform_adapters:
        console.print(
            f"\n[yellow]→[/yellow] Syncing hooks and permissions to {adapter.display_name}..."
        )

        # NOTE: Job skills (meta-skills and step skills) are no longer generated.
        # The MCP server now handles workflow orchestration directly.
        # Only the /deepwork skill is installed as the entry point.

        # Sync hooks to platform settings
        if job_hooks_list:
            console.print("  [dim]•[/dim] Syncing hooks...")
            try:
                hooks_count = sync_hooks_to_platform(project_path, adapter, job_hooks_list)
                result.hooks_synced += hooks_count
                if hooks_count > 0:
                    console.print(f"    [green]✓[/green] Synced {hooks_count} hook(s)")
            except Exception as e:
                warning = f"Failed to sync hooks: {e}"
                console.print(f"    [red]✗[/red] {warning}")
                result.warnings.append(warning)

        # Sync required permissions to platform settings
        console.print("  [dim]•[/dim] Syncing permissions...")
        try:
            perms_count = adapter.sync_permissions(project_path)
            if perms_count > 0:
                console.print(f"    [green]✓[/green] Added {perms_count} base permission(s)")
            else:
                console.print("    [dim]•[/dim] Base permissions already configured")
        except Exception as e:
            warning = f"Failed to sync permissions: {e}"
            console.print(f"    [red]✗[/red] {warning}")
            result.warnings.append(warning)

        # Add skill permissions for generated skills (if adapter supports it)
        all_skill_paths = all_skill_paths_by_platform.get(adapter.name, [])
        if all_skill_paths and hasattr(adapter, "add_skill_permissions"):
            try:
                skill_perms_count = adapter.add_skill_permissions(project_path, all_skill_paths)
                if skill_perms_count > 0:
                    console.print(
                        f"    [green]✓[/green] Added {skill_perms_count} skill permission(s)"
                    )
            except Exception as e:
                warning = f"Failed to sync skill permissions: {e}"
                console.print(f"    [red]✗[/red] {warning}")
                result.warnings.append(warning)

        result.platforms_synced += 1

    # Summary
    console.print()
    console.print("[bold green]✓ Sync complete![/bold green]")
    console.print()

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Metric", style="cyan")
    table.add_column("Count", style="green")

    table.add_row("Platforms synced", str(result.platforms_synced))
    table.add_row("Total skills", str(result.skills_generated))
    if result.hooks_synced > 0:
        table.add_row("Hooks synced", str(result.hooks_synced))

    console.print(table)
    console.print()

    return result
