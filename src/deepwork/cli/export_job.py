"""Export job command for DeepWork CLI."""

import shutil
from pathlib import Path

import click
from rich.console import Console

from deepwork.core.adapters import AgentAdapter
from deepwork.core.generator import SkillGenerator
from deepwork.core.hooks_syncer import JobHooks, sync_hooks_to_platform
from deepwork.core.parser import parse_job_definition
from deepwork.utils.fs import ensure_dir, fix_permissions

console = Console()


class ExportError(Exception):
    """Exception raised for export errors."""

    pass


def _get_global_deepwork_dir() -> Path:
    """
    Get the global DeepWork directory in the user's home.

    Returns:
        Path to ~/.deepwork/
    """
    return Path.home() / ".deepwork"


def _get_global_claude_dir() -> Path:
    """
    Get the global Claude settings directory in the user's home.

    Returns:
        Path to ~/.claude/
    """
    return Path.home() / ".claude"


@click.command()
@click.argument("job_name")
@click.option(
    "--path",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=".",
    help="Path to project directory (default: current directory)",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Overwrite existing global job without confirmation",
)
def export_job(job_name: str, path: Path, force: bool) -> None:
    """
    Export a job to global Claude settings.

    Copies the job definition, generates skills in ~/.claude/skills/,
    and updates ~/.claude/settings.json with necessary hooks and permissions.
    This makes the job available across all Claude projects.
    """
    try:
        _export_job(job_name, path, force)
    except ExportError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort() from e
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        raise


def _export_job(job_name: str, project_path: Path, force: bool) -> None:
    """
    Export a job to global Claude settings.

    Args:
        job_name: Name of the job to export
        project_path: Path to project directory
        force: If True, overwrite without confirmation

    Raises:
        ExportError: If export fails
    """
    console.print("\n[bold cyan]Exporting Job to Global Claude Settings[/bold cyan]\n")

    # Step 1: Validate job exists in project
    console.print(f"[yellow]→[/yellow] Validating job '{job_name}'...")
    project_job_dir = project_path / ".deepwork" / "jobs" / job_name
    if not project_job_dir.exists():
        raise ExportError(
            f"Job '{job_name}' not found in project.\n"
            f"Expected location: {project_job_dir}\n"
            f"Use '/deepwork_jobs.define' to create a new job."
        )

    job_yml_path = project_job_dir / "job.yml"
    if not job_yml_path.exists():
        raise ExportError(
            f"Job definition not found: {job_yml_path}\n" "Job directory exists but job.yml is missing."
        )

    # Parse the job definition
    try:
        job_def = parse_job_definition(project_job_dir)
        console.print(f"  [green]✓[/green] Job '{job_name}' validated (v{job_def.version})")
    except Exception as e:
        raise ExportError(f"Failed to parse job definition: {e}") from e

    # Step 2: Check if job already exists in global settings
    global_deepwork_dir = _get_global_deepwork_dir()
    global_job_dir = global_deepwork_dir / "jobs" / job_name

    if global_job_dir.exists() and not force:
        console.print(
            f"[yellow]⚠[/yellow] Job '{job_name}' already exists in global settings: {global_job_dir}"
        )
        if not click.confirm("Do you want to overwrite it?", default=False):
            console.print("[yellow]Export cancelled.[/yellow]")
            raise ExportError("Export cancelled by user")

    # Step 3: Copy job to global deepwork directory
    console.print("[yellow]→[/yellow] Copying job to global DeepWork directory...")
    ensure_dir(global_deepwork_dir / "jobs")

    # Remove existing if present
    if global_job_dir.exists():
        shutil.rmtree(global_job_dir)

    # Copy the entire job directory
    try:
        shutil.copytree(project_job_dir, global_job_dir)
        fix_permissions(global_job_dir)
        console.print(f"  [green]✓[/green] Job copied to {global_job_dir}")
    except Exception as e:
        raise ExportError(f"Failed to copy job: {e}") from e

    # Step 4: Copy doc specs if present
    project_doc_specs_dir = project_path / ".deepwork" / "doc_specs"
    if project_doc_specs_dir.exists():
        global_doc_specs_dir = global_deepwork_dir / "doc_specs"
        ensure_dir(global_doc_specs_dir)

        # Find doc specs referenced by this job
        doc_specs_to_copy = []
        for step in job_def.steps:
            for output in step.outputs:
                if output.doc_spec:
                    doc_spec_file = project_doc_specs_dir / Path(output.doc_spec).name
                    if doc_spec_file.exists() and doc_spec_file not in doc_specs_to_copy:
                        doc_specs_to_copy.append(doc_spec_file)

        if doc_specs_to_copy:
            console.print("[yellow]→[/yellow] Copying doc specs...")
            for doc_spec_file in doc_specs_to_copy:
                dest_file = global_doc_specs_dir / doc_spec_file.name
                shutil.copy(doc_spec_file, dest_file)
                fix_permissions(dest_file)
                console.print(f"  [green]✓[/green] Copied {doc_spec_file.name}")

    # Step 5: Generate skills in global Claude directory
    console.print("[yellow]→[/yellow] Generating skills for Claude Code...")
    global_claude_dir = _get_global_claude_dir()

    # Create global Claude directory if it doesn't exist
    if not global_claude_dir.exists():
        ensure_dir(global_claude_dir)
        console.print(f"  [green]✓[/green] Created {global_claude_dir}")

    global_claude_skills_dir = global_claude_dir / "skills"
    ensure_dir(global_claude_skills_dir)

    # Generate skills using Claude adapter
    claude_adapter = AgentAdapter.get("claude")(project_root=Path.home())
    generator = SkillGenerator()

    try:
        skill_paths = generator.generate_all_skills(
            job_def, claude_adapter, global_claude_dir, project_root=Path.home()
        )
        console.print(f"  [green]✓[/green] Generated {len(skill_paths)} skills in {global_claude_skills_dir}")
    except Exception as e:
        raise ExportError(f"Failed to generate skills: {e}") from e

    # Step 6: Sync hooks to global Claude settings
    job_hooks = JobHooks.from_job_dir(global_job_dir)
    if job_hooks:
        console.print("[yellow]→[/yellow] Syncing hooks to global Claude settings...")
        try:
            hooks_count = sync_hooks_to_platform(Path.home(), claude_adapter, [job_hooks])
            if hooks_count > 0:
                console.print(f"  [green]✓[/green] Synced {hooks_count} hook(s)")
        except Exception as e:
            raise ExportError(f"Failed to sync hooks: {e}") from e

    # Step 7: Sync permissions to global Claude settings
    console.print("[yellow]→[/yellow] Syncing permissions to global Claude settings...")
    try:
        # Add global deepwork directory permissions
        perms_count = claude_adapter.sync_permissions(Path.home())
        if perms_count > 0:
            console.print(f"  [green]✓[/green] Added {perms_count} base permission(s)")

        # Add skill permissions
        if skill_paths and hasattr(claude_adapter, "add_skill_permissions"):
            skill_perms_count = claude_adapter.add_skill_permissions(Path.home(), skill_paths)
            if skill_perms_count > 0:
                console.print(f"  [green]✓[/green] Added {skill_perms_count} skill permission(s)")
    except Exception as e:
        raise ExportError(f"Failed to sync permissions: {e}") from e

    # Success message
    console.print()
    console.print(f"[bold green]✓ Job '{job_name}' exported successfully to global Claude settings![/bold green]")
    console.print()
    console.print("[bold]The job is now available across all your Claude projects.[/bold]")
    console.print()
    console.print("[bold]To use the job:[/bold]")
    console.print(f"  Start Claude and use: [cyan]/{job_name}[/cyan] or [cyan]/{job_name}.<step_name>[/cyan]")
    console.print()
