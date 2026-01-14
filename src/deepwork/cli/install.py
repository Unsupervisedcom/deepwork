"""Install command for DeepWork CLI."""

import shutil
from pathlib import Path

import click
from rich.console import Console

from deepwork.core.adapters import AgentAdapter
from deepwork.core.detector import PlatformDetector
from deepwork.utils.fs import ensure_dir
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
        console.print(
            f"  [green]✓[/green] Installed {job_name} ({target_dir.relative_to(project_path)})"
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


def _inject_deepwork_policy(jobs_dir: Path, project_path: Path) -> None:
    """
    Inject the deepwork_policy job definition into the project.

    Args:
        jobs_dir: Path to .deepwork/jobs directory
        project_path: Path to project root (for relative path display)

    Raises:
        InstallError: If injection fails
    """
    _inject_standard_job("deepwork_policy", jobs_dir, project_path)


def _create_deepwork_gitignore(deepwork_dir: Path) -> None:
    """
    Create .gitignore file in .deepwork/ directory.

    This ensures that temporary files like .last_work_tree are not committed.

    Args:
        deepwork_dir: Path to .deepwork directory
    """
    gitignore_path = deepwork_dir / ".gitignore"
    gitignore_content = """# DeepWork temporary files
# These files are used for policy evaluation during sessions
.last_work_tree
"""

    # Only write if it doesn't exist or doesn't contain the entry
    if gitignore_path.exists():
        existing_content = gitignore_path.read_text()
        if ".last_work_tree" not in existing_content:
            # Append to existing
            with open(gitignore_path, "a") as f:
                f.write("\n" + gitignore_content)
    else:
        gitignore_path.write_text(gitignore_content)


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

    # Step 2: Detect or validate platform
    detector = PlatformDetector(project_path)

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
        platform_to_add = adapter.name
    else:
        # Auto-detect platform
        console.print("[yellow]→[/yellow] Auto-detecting AI platform...")
        available_adapters = detector.detect_all_platforms()

        if not available_adapters:
            supported = ", ".join(
                f"{AgentAdapter.get(name).display_name} ({AgentAdapter.get(name).config_dir}/)"
                for name in AgentAdapter.list_names()
            )
            raise InstallError(
                f"No AI platform detected.\n"
                f"DeepWork supports: {supported}.\n"
                "Please set up one of these platforms first, or use --platform to specify."
            )

        if len(available_adapters) > 1:
            # Multiple platforms - ask user to specify
            platform_names = ", ".join(a.display_name for a in available_adapters)
            raise InstallError(
                f"Multiple AI platforms detected: {platform_names}\n"
                "Please specify which platform to use with --platform option."
            )

        adapter = available_adapters[0]
        console.print(f"  [green]✓[/green] {adapter.display_name} detected")
        platform_to_add = adapter.name

    # Step 3: Create .deepwork/ directory structure
    console.print("[yellow]→[/yellow] Creating DeepWork directory structure...")
    deepwork_dir = project_path / ".deepwork"
    jobs_dir = deepwork_dir / "jobs"
    ensure_dir(deepwork_dir)
    ensure_dir(jobs_dir)
    console.print(f"  [green]✓[/green] Created {deepwork_dir.relative_to(project_path)}/")

    # Step 3b: Inject standard jobs (core job definitions)
    console.print("[yellow]→[/yellow] Installing core job definitions...")
    _inject_deepwork_jobs(jobs_dir, project_path)
    _inject_deepwork_policy(jobs_dir, project_path)

    # Step 3c: Create .gitignore for temporary files
    _create_deepwork_gitignore(deepwork_dir)
    console.print("  [green]✓[/green] Created .deepwork/.gitignore")

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

    # Add platform if not already present
    if platform_to_add not in config_data["platforms"]:
        config_data["platforms"].append(platform_to_add)
        console.print(f"  [green]✓[/green] Added {adapter.display_name} to platforms")
    else:
        console.print(f"  [dim]•[/dim] {adapter.display_name} already configured")

    save_yaml(config_file, config_data)
    console.print(f"  [green]✓[/green] Updated {config_file.relative_to(project_path)}")

    # Step 5: Run sync to generate commands
    console.print()
    console.print("[yellow]→[/yellow] Running sync to generate commands...")
    console.print()

    from deepwork.cli.sync import sync_commands

    try:
        sync_commands(project_path)
    except Exception as e:
        raise InstallError(f"Failed to sync commands: {e}") from e

    # Success message
    console.print()
    console.print(
        f"[bold green]✓ DeepWork installed successfully for {adapter.display_name}![/bold green]"
    )
    console.print()
    console.print("[bold]Next steps:[/bold]")
    console.print("  1. Start your agent CLI (ex. [cyan]claude[/cyan] or [cyan]gemini[/cyan])")
    console.print("  2. Define your first job using the command [cyan]/deepwork_jobs.define[/cyan]")
    console.print()
