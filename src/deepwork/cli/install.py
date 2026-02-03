"""Install command for DeepWork CLI."""

import shutil
from pathlib import Path

import click
from rich.console import Console

from deepwork.core.adapters import AgentAdapter
from deepwork.core.detector import PlatformDetector
from deepwork.utils.fs import ensure_dir, fix_permissions
from deepwork.utils.git import is_git_repo
from deepwork.utils.yaml_utils import load_yaml, save_yaml

console = Console()


class InstallError(Exception):
    """Exception raised for installation errors."""

    pass


def _inject_standard_job(job_name: str, jobs_dir: Path, project_path: Path) -> None:
    """
    Inject a standard job definition into the project.

    Args:
        job_name: Name of the standard job to inject
        jobs_dir: Path to .deepwork/jobs directory
        project_path: Path to project root (for relative path display)

    Raises:
        InstallError: If injection fails
    """
    # Find the standard jobs directory
    standard_jobs_dir = Path(__file__).parent.parent / "standard_jobs" / job_name

    if not standard_jobs_dir.exists():
        raise InstallError(
            f"Standard job '{job_name}' not found at {standard_jobs_dir}. "
            "DeepWork installation may be corrupted."
        )

    # Target directory
    target_dir = jobs_dir / job_name

    # Copy the entire directory
    try:
        if target_dir.exists():
            # Remove existing if present (for reinstall/upgrade)
            shutil.rmtree(target_dir)

        shutil.copytree(standard_jobs_dir, target_dir)
        # Fix permissions - source may have restrictive permissions (e.g., read-only)
        fix_permissions(target_dir)
        console.print(
            f"  [green]✓[/green] Installed {job_name} ({target_dir.relative_to(project_path)})"
        )

        # Copy any doc specs from the standard job to .deepwork/doc_specs/
        doc_specs_source = standard_jobs_dir / "doc_specs"
        doc_specs_target = project_path / ".deepwork" / "doc_specs"
        if doc_specs_source.exists():
            for doc_spec_file in doc_specs_source.glob("*.md"):
                target_doc_spec = doc_specs_target / doc_spec_file.name
                shutil.copy(doc_spec_file, target_doc_spec)
                # Fix permissions for copied doc spec
                fix_permissions(target_doc_spec)
                console.print(
                    f"  [green]✓[/green] Installed doc spec {doc_spec_file.name} ({target_doc_spec.relative_to(project_path)})"
                )
    except Exception as e:
        raise InstallError(f"Failed to install {job_name}: {e}") from e


def _inject_deepwork_jobs(jobs_dir: Path, project_path: Path) -> None:
    """
    Inject the deepwork_jobs job definition into the project.

    Args:
        jobs_dir: Path to .deepwork/jobs directory
        project_path: Path to project root (for relative path display)

    Raises:
        InstallError: If injection fails
    """
    _inject_standard_job("deepwork_jobs", jobs_dir, project_path)


def _create_deepwork_gitignore(deepwork_dir: Path) -> None:
    """
    Create .gitignore file in .deepwork/ directory.

    This ensures that runtime artifacts are not committed while keeping
    the tmp directory structure in version control.

    Args:
        deepwork_dir: Path to .deepwork directory
    """
    gitignore_path = deepwork_dir / ".gitignore"
    gitignore_content = """# DeepWork runtime artifacts
# These files are generated during sessions and should not be committed
.last_work_tree
.last_head_ref

# Temporary files (but keep the directory via .gitkeep)
tmp/*
!tmp/.gitkeep
"""

    # Always overwrite to ensure correct content
    gitignore_path.write_text(gitignore_content)


def _create_tmp_directory(deepwork_dir: Path) -> None:
    """
    Create the .deepwork/tmp directory with a .gitkeep file.

    This ensures the tmp directory exists in version control, which is required
    for file permissions to work correctly when Claude Code starts fresh.

    Args:
        deepwork_dir: Path to .deepwork directory
    """
    tmp_dir = deepwork_dir / "tmp"
    ensure_dir(tmp_dir)

    gitkeep_file = tmp_dir / ".gitkeep"
    if not gitkeep_file.exists():
        gitkeep_file.write_text(
            "# This file ensures the .deepwork/tmp directory exists in version control.\n"
            "# The tmp directory is used for temporary files during DeepWork operations.\n"
            "# Do not delete this file.\n"
        )


class DynamicChoice(click.Choice):
    """A Click Choice that gets its values dynamically from AgentAdapter."""

    def __init__(self) -> None:
        # Get choices at runtime from registered adapters
        super().__init__(AgentAdapter.list_names(), case_sensitive=False)


@click.command()
@click.option(
    "--platform",
    "-p",
    type=DynamicChoice(),
    required=False,
    help="AI platform to install for. If not specified, will auto-detect.",
)
@click.option(
    "--path",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=".",
    help="Path to project directory (default: current directory)",
)
def install(platform: str | None, path: Path) -> None:
    """
    Install DeepWork in a project.

    Adds the specified AI platform to the project configuration and syncs
    commands for all configured platforms.
    """
    try:
        _install_deepwork(platform, path)
    except InstallError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort() from e
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        raise


def _install_deepwork(platform_name: str | None, project_path: Path) -> None:
    """
    Install DeepWork in a project.

    Args:
        platform_name: Platform to install for (or None to auto-detect)
        project_path: Path to project directory

    Raises:
        InstallError: If installation fails
    """
    console.print("\n[bold cyan]DeepWork Installation[/bold cyan]\n")

    # Step 1: Check Git repository
    console.print("[yellow]→[/yellow] Checking Git repository...")
    if not is_git_repo(project_path):
        raise InstallError(
            "Not a Git repository. DeepWork requires a Git repository.\n"
            "Run 'git init' to initialize a repository."
        )
    console.print("  [green]✓[/green] Git repository found")

    # Step 2: Detect or validate platform(s)
    detector = PlatformDetector(project_path)
    platforms_to_add: list[str] = []
    detected_adapters: list[AgentAdapter] = []

    if platform_name:
        # User specified platform - check if it's available
        console.print(f"[yellow]→[/yellow] Checking for {platform_name.title()}...")
        adapter = detector.detect_platform(platform_name.lower())

        if adapter is None:
            # Platform not detected - provide helpful message
            adapter = detector.get_adapter(platform_name.lower())
            raise InstallError(
                f"{adapter.display_name} not detected in this project.\n"
                f"Expected to find '{adapter.config_dir}/' directory.\n"
                f"Please ensure {adapter.display_name} is set up in this project."
            )

        console.print(f"  [green]✓[/green] {adapter.display_name} detected")
        platforms_to_add = [adapter.name]
        detected_adapters = [adapter]
    else:
        # Auto-detect all available platforms
        console.print("[yellow]→[/yellow] Auto-detecting AI platforms...")
        available_adapters = detector.detect_all_platforms()

        if not available_adapters:
            # No platforms detected - default to Claude Code
            console.print("  [dim]•[/dim] No AI platform detected, defaulting to Claude Code")

            # Create .claude directory
            claude_dir = project_path / ".claude"
            ensure_dir(claude_dir)
            console.print(f"  [green]✓[/green] Created {claude_dir.relative_to(project_path)}/")

            # Get Claude adapter
            claude_adapter_class = AgentAdapter.get("claude")
            claude_adapter = claude_adapter_class(project_root=project_path)
            platforms_to_add = [claude_adapter.name]
            detected_adapters = [claude_adapter]
        else:
            # Add all detected platforms
            for adapter in available_adapters:
                console.print(f"  [green]✓[/green] {adapter.display_name} detected")
                platforms_to_add.append(adapter.name)
            detected_adapters = available_adapters

    # Step 3: Create .deepwork/ directory structure
    console.print("[yellow]→[/yellow] Creating DeepWork directory structure...")
    deepwork_dir = project_path / ".deepwork"
    jobs_dir = deepwork_dir / "jobs"
    doc_specs_dir = deepwork_dir / "doc_specs"
    ensure_dir(deepwork_dir)
    ensure_dir(jobs_dir)
    ensure_dir(doc_specs_dir)
    console.print(f"  [green]✓[/green] Created {deepwork_dir.relative_to(project_path)}/")

    # Step 3b: Inject standard jobs (core job definitions)
    console.print("[yellow]→[/yellow] Installing core job definitions...")
    _inject_deepwork_jobs(jobs_dir, project_path)

    # Step 3c: Create .gitignore for temporary files
    _create_deepwork_gitignore(deepwork_dir)
    console.print("  [green]✓[/green] Created .deepwork/.gitignore")

    # Step 3d: Create tmp directory with .gitkeep file for version control
    _create_tmp_directory(deepwork_dir)
    console.print("  [green]✓[/green] Created .deepwork/tmp/.gitkeep")

    # Step 4: Load or create config.yml
    console.print("[yellow]→[/yellow] Updating configuration...")
    config_file = deepwork_dir / "config.yml"

    if config_file.exists():
        config_data = load_yaml(config_file)
        if config_data is None:
            config_data = {}
    else:
        config_data = {}

    # Initialize config structure
    if "version" not in config_data:
        config_data["version"] = "0.1.0"

    if "platforms" not in config_data:
        config_data["platforms"] = []

    # Initialize quality_gate config with defaults
    if "quality_gate" not in config_data:
        config_data["quality_gate"] = {
            "agent_review_command": "claude -p --output-format json",
            "default_timeout": 120,
            "default_max_attempts": 3,
        }

    # Add each platform if not already present
    added_platforms: list[str] = []
    for i, platform in enumerate(platforms_to_add):
        adapter = detected_adapters[i]
        if platform not in config_data["platforms"]:
            config_data["platforms"].append(platform)
            added_platforms.append(adapter.display_name)
            console.print(f"  [green]✓[/green] Added {adapter.display_name} to platforms")
        else:
            console.print(f"  [dim]•[/dim] {adapter.display_name} already configured")

    save_yaml(config_file, config_data)
    console.print(f"  [green]✓[/green] Updated {config_file.relative_to(project_path)}")

    # Step 5: Register MCP server for each platform
    console.print("[yellow]→[/yellow] Registering MCP server...")
    for adapter in detected_adapters:
        if adapter.register_mcp_server(project_path):
            console.print(f"  [green]✓[/green] Registered MCP server for {adapter.display_name}")
        else:
            console.print(f"  [dim]•[/dim] MCP server already registered for {adapter.display_name}")

    # Step 6: Run sync to generate skills
    console.print()
    console.print("[yellow]→[/yellow] Running sync to generate skills...")
    console.print()

    from deepwork.cli.sync import sync_skills

    try:
        sync_skills(project_path)
    except Exception as e:
        raise InstallError(f"Failed to sync skills: {e}") from e

    # Success message
    console.print()
    platform_names = ", ".join(a.display_name for a in detected_adapters)
    console.print(
        f"[bold green]✓ DeepWork installed successfully for {platform_names}![/bold green]"
    )
    console.print()
    console.print("[bold]Next steps:[/bold]")
    console.print("  1. Start your agent CLI (ex. [cyan]claude[/cyan] or [cyan]gemini[/cyan])")
    console.print("  2. Define your first job using the command [cyan]/deepwork_jobs[/cyan]")
    console.print()
