"""Expert commands for DeepWork CLI."""

from pathlib import Path

import click
from rich.console import Console

from deepwork.core.experts_parser import (
    ExpertParseError,
    format_learnings_markdown,
    format_topics_markdown,
    parse_expert_definition,
)

console = Console()


class ExpertNotFoundError(Exception):
    """Exception raised when an expert is not found."""

    pass


def _find_expert_dir(expert_name: str, project_path: Path) -> Path:
    """
    Find the expert directory for a given expert name.

    The expert name uses dashes (e.g., "rails-activejob") but the folder
    name may use underscores (e.g., "rails_activejob").

    Args:
        expert_name: Expert name (with dashes)
        project_path: Project root directory

    Returns:
        Path to expert directory

    Raises:
        ExpertNotFoundError: If expert is not found
    """
    experts_dir = project_path / ".deepwork" / "experts"

    if not experts_dir.exists():
        raise ExpertNotFoundError(
            f"No experts directory found at {experts_dir}.\n"
            "Run 'deepwork install' to set up the experts system."
        )

    # Convert expert name back to possible folder names
    # rails-activejob -> rails_activejob, rails-activejob
    possible_names = [
        expert_name.replace("-", "_"),  # rails_activejob
        expert_name,  # rails-activejob (direct match)
    ]

    for folder_name in possible_names:
        expert_dir = experts_dir / folder_name
        if expert_dir.exists() and (expert_dir / "expert.yml").exists():
            return expert_dir

    # List available experts for helpful error message
    available_experts = []
    if experts_dir.exists():
        for subdir in experts_dir.iterdir():
            if subdir.is_dir() and (subdir / "expert.yml").exists():
                # Convert folder name to expert name (underscores to dashes)
                name = subdir.name.replace("_", "-")
                available_experts.append(name)

    if available_experts:
        available_str = ", ".join(sorted(available_experts))
        raise ExpertNotFoundError(
            f"Expert '{expert_name}' not found.\nAvailable experts: {available_str}"
        )
    else:
        raise ExpertNotFoundError(
            f"Expert '{expert_name}' not found.\nNo experts have been defined yet."
        )


@click.command()
@click.option(
    "--expert",
    "-e",
    required=True,
    help="Expert name (e.g., 'rails-activejob')",
)
@click.option(
    "--path",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=".",
    help="Path to project directory (default: current directory)",
)
def topics(expert: str, path: Path) -> None:
    """
    List topics for an expert.

    Returns a Markdown list of topics with names, file paths as links,
    and keywords, sorted by most-recently-updated.

    Example:
        deepwork topics --expert "rails-activejob"
    """
    try:
        expert_dir = _find_expert_dir(expert, path)
        expert_def = parse_expert_definition(expert_dir)
        output = format_topics_markdown(expert_def)
        # Print raw output (no Rich formatting) for use in $(command) embedding
        print(output)
    except ExpertNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort() from e
    except ExpertParseError as e:
        console.print(f"[red]Error parsing expert:[/red] {e}")
        raise click.Abort() from e


@click.command()
@click.option(
    "--expert",
    "-e",
    required=True,
    help="Expert name (e.g., 'rails-activejob')",
)
@click.option(
    "--path",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=".",
    help="Path to project directory (default: current directory)",
)
def learnings(expert: str, path: Path) -> None:
    """
    List learnings for an expert.

    Returns a Markdown list of learnings with names, file paths as links,
    and summarized results, sorted by most-recently-updated.

    Example:
        deepwork learnings --expert "rails-activejob"
    """
    try:
        expert_dir = _find_expert_dir(expert, path)
        expert_def = parse_expert_definition(expert_dir)
        output = format_learnings_markdown(expert_def)
        # Print raw output (no Rich formatting) for use in $(command) embedding
        print(output)
    except ExpertNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort() from e
    except ExpertParseError as e:
        console.print(f"[red]Error parsing expert:[/red] {e}")
        raise click.Abort() from e
