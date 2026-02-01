"""Sync command for DeepWork CLI."""

from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from deepwork.core.adapters import AgentAdapter
from deepwork.core.experts_generator import ExpertGenerator
from deepwork.core.experts_parser import (
    ExpertParseError,
    discover_experts,
    parse_expert_definition,
)
from deepwork.core.hooks_syncer import collect_expert_hooks, sync_hooks_to_platform
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
    Sync DeepWork skills to all configured platforms.

    Regenerates all skills for workflows and expert agents based on
    the current expert definitions in .deepwork/experts/.
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

    # Discover and parse experts (experts include their workflows)
    experts_dir = deepwork_dir / "experts"
    expert_dirs = discover_experts(experts_dir)
    console.print(f"[yellow]→[/yellow] Found {len(expert_dirs)} expert(s) to sync")

    experts = []
    failed_experts: list[tuple[str, str]] = []
    total_workflows = 0
    for expert_dir in expert_dirs:
        try:
            expert_def = parse_expert_definition(expert_dir)
            experts.append(expert_def)
            workflow_count = len(expert_def.workflows)
            total_workflows += workflow_count
            if workflow_count > 0:
                console.print(
                    f"  [green]✓[/green] Loaded {expert_def.name} ({workflow_count} workflow(s))"
                )
            else:
                console.print(f"  [green]✓[/green] Loaded {expert_def.name}")
        except ExpertParseError as e:
            console.print(f"  [red]✗[/red] Failed to load {expert_dir.name}: {e}")
            failed_experts.append((expert_dir.name, str(e)))

    # Fail early if any experts failed to parse
    if failed_experts:
        console.print()
        console.print("[bold red]Sync aborted due to expert parsing errors:[/bold red]")
        for expert_name, error in failed_experts:
            console.print(f"  • {expert_name}: {error}")
        raise SyncError(f"Failed to parse {len(failed_experts)} expert(s)")

    if total_workflows > 0:
        console.print(f"[yellow]→[/yellow] Found {total_workflows} workflow(s) across all experts")

    # Collect hooks from all experts (via their workflows)
    expert_hooks_list = collect_expert_hooks(experts_dir)
    if expert_hooks_list:
        console.print(f"[yellow]→[/yellow] Found {len(expert_hooks_list)} expert(s) with hooks")

    # Sync each platform
    expert_generator = ExpertGenerator()
    stats = {"platforms": 0, "skills": 0, "hooks": 0, "agents": 0}

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

        # Generate expert agents (only for Claude currently - agents live in .claude/agents/)
        all_skill_paths: list[Path] = []
        if experts and adapter.name == "claude":
            console.print("  [dim]•[/dim] Generating expert agents...")
            for expert in experts:
                try:
                    agent_path = expert_generator.generate_expert_agent(
                        expert, adapter, platform_dir
                    )
                    stats["agents"] += 1
                    console.print(f"    [green]✓[/green] {expert.name} ({agent_path.name})")
                except Exception as e:
                    console.print(f"    [red]✗[/red] Failed for {expert.name}: {e}")

        # Generate workflow skills for all experts
        if experts:
            console.print("  [dim]•[/dim] Generating workflow skills...")
            for expert in experts:
                if not expert.workflows:
                    continue
                try:
                    expert_skill_paths = expert_generator.generate_all_expert_skills(
                        expert, adapter, platform_dir, project_root=project_path
                    )
                    all_skill_paths.extend(expert_skill_paths)
                    stats["skills"] += len(expert_skill_paths)
                    console.print(
                        f"    [green]✓[/green] {expert.name} ({len(expert_skill_paths)} skills)"
                    )
                except Exception as e:
                    console.print(f"    [red]✗[/red] Failed for {expert.name}: {e}")

        # Sync hooks to platform settings
        if expert_hooks_list:
            console.print("  [dim]•[/dim] Syncing hooks...")
            try:
                hooks_count = sync_hooks_to_platform(project_path, adapter, expert_hooks_list)
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
    if stats["agents"] > 0:
        table.add_row("Expert agents", str(stats["agents"]))
    table.add_row("Total skills", str(stats["skills"]))
    if stats["hooks"] > 0:
        table.add_row("Hooks synced", str(stats["hooks"]))

    console.print(table)
    console.print()
