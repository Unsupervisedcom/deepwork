"""Sync command for DeepWork CLI."""

import shutil
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from deepwork.core.adapters import AgentAdapter
from deepwork.core.generator import SkillGenerator
from deepwork.core.hooks_syncer import collect_job_hooks, sync_hooks_to_platform
from deepwork.core.parser import parse_job_definition
from deepwork.utils.fs import ensure_dir, fix_permissions
from deepwork.utils.yaml_utils import load_yaml

# Prefix for DeepWork-managed technique folders in platform skill directories
TECHNIQUE_PREFIX = "dwt_"

console = Console()


class SyncError(Exception):
    """Exception raised for sync errors."""

    pass


def sync_techniques_to_platform(
    techniques_dir: Path, skills_dir: Path, adapter: AgentAdapter
) -> tuple[int, int]:
    """
    Sync techniques from .deepwork/techniques/ to platform skill directory.

    Copies technique folders with a 'dwt_' prefix and removes stale dwt_ folders
    that no longer have corresponding techniques.

    Args:
        techniques_dir: Path to .deepwork/techniques/ directory
        skills_dir: Path to platform skills directory (e.g., .claude/skills/)
        adapter: The agent adapter for platform-specific handling

    Returns:
        Tuple of (synced_count, removed_count)
    """
    synced_count = 0
    removed_count = 0

    # Get current technique names (directories with SKILL.md or index.toml)
    current_techniques: set[str] = set()
    if techniques_dir.exists():
        for technique_dir in techniques_dir.iterdir():
            if technique_dir.is_dir() and not technique_dir.name.startswith("."):
                # Check for SKILL.md (Claude) or any .toml file (Gemini)
                has_skill = (technique_dir / "SKILL.md").exists() or any(
                    technique_dir.glob("*.toml")
                )
                if has_skill:
                    current_techniques.add(technique_dir.name)

    # Find existing dwt_ prefixed folders in skills directory
    existing_dwt_folders: set[str] = set()
    if skills_dir.exists():
        for item in skills_dir.iterdir():
            if item.is_dir() and item.name.startswith(TECHNIQUE_PREFIX):
                # Extract the technique name without prefix
                technique_name = item.name[len(TECHNIQUE_PREFIX) :]
                existing_dwt_folders.add(technique_name)

    # Remove stale dwt_ folders (no longer in techniques)
    stale_techniques = existing_dwt_folders - current_techniques
    for stale_name in stale_techniques:
        stale_dir = skills_dir / f"{TECHNIQUE_PREFIX}{stale_name}"
        if stale_dir.exists():
            shutil.rmtree(stale_dir)
            removed_count += 1

    # Copy/update current techniques
    for technique_name in current_techniques:
        source_dir = techniques_dir / technique_name
        dest_dir = skills_dir / f"{TECHNIQUE_PREFIX}{technique_name}"

        # Convert SKILL.md to platform-specific format if needed
        _copy_technique(source_dir, dest_dir, adapter)
        synced_count += 1

    return synced_count, removed_count


def _copy_technique(source_dir: Path, dest_dir: Path, adapter: AgentAdapter) -> None:
    """
    Copy a technique folder to the destination with platform-specific handling.

    Args:
        source_dir: Source technique directory
        dest_dir: Destination directory in platform skills folder
        adapter: Agent adapter for platform-specific handling
    """
    # Remove existing destination if present
    if dest_dir.exists():
        shutil.rmtree(dest_dir)

    # Copy the entire directory
    shutil.copytree(source_dir, dest_dir)
    fix_permissions(dest_dir)

    # Handle Gemini-specific conversion (SKILL.md -> index.toml)
    if adapter.name == "gemini":
        skill_md = dest_dir / "SKILL.md"
        if skill_md.exists():
            _convert_skill_md_to_toml(skill_md, dest_dir / "index.toml")
            skill_md.unlink()


def _convert_skill_md_to_toml(skill_md: Path, toml_path: Path) -> None:
    """
    Convert a SKILL.md file to Gemini's TOML format.

    This is a simple conversion that extracts the frontmatter and content.

    Args:
        skill_md: Path to the SKILL.md file
        toml_path: Path to write the TOML file
    """
    content = skill_md.read_text()

    # Parse frontmatter
    name = ""
    description = ""
    body = content

    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            frontmatter = parts[1].strip()
            body = parts[2].strip()

            # Simple YAML parsing for name and description
            for line in frontmatter.split("\n"):
                if line.startswith("name:"):
                    name = line.split(":", 1)[1].strip().strip('"\'')
                elif line.startswith("description:"):
                    description = line.split(":", 1)[1].strip().strip('"\'')

    # Write TOML format
    toml_content = f'''name = "{name}"
description = "{description}"

[prompt]
content = """
{body}
"""
'''
    toml_path.write_text(toml_content)


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

    # Discover jobs
    jobs_dir = deepwork_dir / "jobs"
    if not jobs_dir.exists():
        job_dirs = []
    else:
        job_dirs = [d for d in jobs_dir.iterdir() if d.is_dir() and (d / "job.yml").exists()]

    console.print(f"[yellow]→[/yellow] Found {len(job_dirs)} job(s) to sync")

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

    # Collect hooks from all jobs
    job_hooks_list = collect_job_hooks(jobs_dir)
    if job_hooks_list:
        console.print(f"[yellow]→[/yellow] Found {len(job_hooks_list)} job(s) with hooks")

    # Sync each platform
    generator = SkillGenerator()
    stats = {"platforms": 0, "skills": 0, "hooks": 0}
    synced_adapters: list[AgentAdapter] = []

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

        # Sync techniques to platform
        techniques_dir = deepwork_dir / "techniques"
        if techniques_dir.exists():
            console.print("  [dim]•[/dim] Syncing techniques...")
            try:
                synced, removed = sync_techniques_to_platform(
                    techniques_dir, skills_dir, adapter
                )
                stats["techniques_synced"] = stats.get("techniques_synced", 0) + synced
                stats["techniques_removed"] = stats.get("techniques_removed", 0) + removed
                if synced > 0 or removed > 0:
                    msg_parts = []
                    if synced > 0:
                        msg_parts.append(f"{synced} synced")
                    if removed > 0:
                        msg_parts.append(f"{removed} removed")
                    console.print(f"    [green]✓[/green] Techniques: {', '.join(msg_parts)}")
                else:
                    console.print("    [dim]•[/dim] No techniques to sync")
            except Exception as e:
                console.print(f"    [red]✗[/red] Failed to sync techniques: {e}")

        stats["platforms"] += 1
        synced_adapters.append(adapter)

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
    if stats.get("techniques_synced", 0) > 0:
        table.add_row("Techniques synced", str(stats["techniques_synced"]))
    if stats.get("techniques_removed", 0) > 0:
        table.add_row("Techniques removed", str(stats["techniques_removed"]))

    console.print(table)
    console.print()

    # Show reload instructions for each synced platform
    if synced_adapters and stats["skills"] > 0:
        console.print("[bold]To use the new skills:[/bold]")
        for adapter in synced_adapters:
            console.print(f"  [cyan]{adapter.display_name}:[/cyan] {adapter.reload_instructions}")
        console.print()
