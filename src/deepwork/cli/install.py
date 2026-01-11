"""Install command for DeepWork CLI."""

from datetime import datetime
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from deepwork.core.detector import PlatformDetector
from deepwork.core.generator import CommandGenerator
from deepwork.utils.fs import ensure_dir
from deepwork.utils.git import is_git_repo
from deepwork.utils.yaml_utils import save_yaml

console = Console()


class InstallError(Exception):
    """Exception raised for installation errors."""

    pass


@click.command()
@click.option(
    "--platform",
    "-p",
    type=click.Choice(["claude", "gemini", "copilot"], case_sensitive=False),
    required=False,
    help="AI platform to install for (claude, gemini, or copilot). If not specified, will auto-detect.",
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

    Sets up DeepWork configuration and installs core skills for the specified
    AI platform (Claude Code, Google Gemini, or GitHub Copilot).
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
        platform_config = detector.detect_platform(platform_name.lower())

        if platform_config is None:
            # Platform not detected - provide helpful message
            platform_cfg = detector.get_platform_config(platform_name.lower())
            raise InstallError(
                f"{platform_cfg.display_name} not detected in this project.\n"
                f"Expected to find '{platform_cfg.config_dir}/' directory.\n"
                f"Please ensure {platform_cfg.display_name} is set up in this project."
            )

        console.print(f"  [green]✓[/green] {platform_config.display_name} detected")
    else:
        # Auto-detect platform
        console.print("[yellow]→[/yellow] Auto-detecting AI platform...")
        available_platforms = detector.detect_all_platforms()

        if not available_platforms:
            raise InstallError(
                "No AI platform detected.\n"
                "DeepWork supports: Claude Code (.claude/), Google Gemini (.gemini/), "
                "GitHub Copilot (.github/).\n"
                "Please set up one of these platforms first, or use --platform to specify."
            )

        if len(available_platforms) > 1:
            # Multiple platforms - ask user to specify
            platform_names = ", ".join(p.display_name for p in available_platforms)
            raise InstallError(
                f"Multiple AI platforms detected: {platform_names}\n"
                "Please specify which platform to use with --platform option."
            )

        platform_config = available_platforms[0]
        console.print(f"  [green]✓[/green] {platform_config.display_name} detected")

    # Step 3: Create .deepwork/ directory structure
    console.print("[yellow]→[/yellow] Creating DeepWork directory structure...")
    deepwork_dir = project_path / ".deepwork"
    jobs_dir = deepwork_dir / "jobs"
    ensure_dir(deepwork_dir)
    ensure_dir(jobs_dir)
    console.print(f"  [green]✓[/green] Created {deepwork_dir.relative_to(project_path)}/")

    # Step 4: Create config.yml
    console.print("[yellow]→[/yellow] Creating configuration...")
    config_data = {
        "platform": platform_config.name,
        "version": "1.0.0",
        "installed": datetime.utcnow().isoformat() + "Z",
    }
    config_file = deepwork_dir / "config.yml"
    save_yaml(config_file, config_data)
    console.print(f"  [green]✓[/green] Created {config_file.relative_to(project_path)}")

    # Step 5: Create registry.yml
    console.print("[yellow]→[/yellow] Initializing job registry...")
    registry_file = deepwork_dir / "registry.yml"
    if not registry_file.exists():
        save_yaml(registry_file, {"jobs": {}})
    console.print(f"  [green]✓[/green] Created {registry_file.relative_to(project_path)}")

    # Step 6: Create commands directory
    console.print("[yellow]→[/yellow] Creating commands directory...")
    platform_dir = project_path / platform_config.config_dir
    commands_dir = platform_dir / platform_config.commands_dir
    ensure_dir(commands_dir)
    console.print(f"  [green]✓[/green] Created {commands_dir.relative_to(project_path)}/")
    console.print("  [dim]Job step commands will be generated here when you install jobs[/dim]")

    # Step 7: Success message
    console.print()
    _print_success_panel(platform_config.name, platform_config.display_name, project_path)


def _print_success_panel(
    platform_name: str, platform_display: str, project_path: Path
) -> None:
    """
    Print success panel with next steps.

    Args:
        platform_name: Platform name (e.g., "claude")
        platform_display: Platform display name (e.g., "Claude Code")
        project_path: Path to project directory
    """
    # Create table with installed files
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("File", style="cyan")

    table.add_row("✓ .deepwork/config.yml")
    table.add_row("✓ .deepwork/registry.yml")
    table.add_row(f"✓ {get_platform_config_dir(platform_name)}/commands/")

    # Create success message
    success_msg = (
        f"[bold green]DeepWork installed successfully for {platform_display}![/bold green]\n\n"
        "[bold]Files created:[/bold]\n"
    )

    # Create next steps message
    next_steps = (
        "\n[bold]Next steps:[/bold]\n"
        "  1. Create a job definition in [cyan].deepwork/jobs/[job_name]/[/cyan]\n"
        "  2. Install the job to generate slash-commands\n"
        "  3. Use slash-commands like [cyan]/[job_name].[step_name][/cyan] to execute steps!\n\n"
        "[dim]See CLAUDE.md or readme.md for more information[/dim]"
    )

    # Combine all parts
    panel_content = success_msg

    # Render table to string
    from io import StringIO

    table_str = StringIO()
    temp_console = Console(file=table_str, force_terminal=True)
    temp_console.print(table)
    panel_content += table_str.getvalue()

    panel_content += next_steps

    # Print panel
    panel = Panel(
        panel_content,
        title="🎉 Installation Complete",
        border_style="green",
        padding=(1, 2),
    )
    console.print(panel)


def get_platform_config_dir(platform_name: str) -> str:
    """
    Get platform config directory name.

    Args:
        platform_name: Platform name

    Returns:
        Config directory name
    """
    if platform_name == "claude":
        return ".claude"
    elif platform_name == "gemini":
        return ".gemini"
    elif platform_name == "copilot":
        return ".github"
    else:
        return f".{platform_name}"
