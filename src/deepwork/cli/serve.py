"""Serve command for DeepWork MCP server."""

from pathlib import Path

import click
from rich.console import Console

from deepwork.utils.yaml_utils import load_yaml

console = Console()


class ServeError(Exception):
    """Exception raised for serve errors."""

    pass


def _load_config(project_path: Path) -> dict:
    """Load DeepWork config from project.

    Args:
        project_path: Path to project root

    Returns:
        Config dictionary

    Raises:
        ServeError: If config not found or invalid
    """
    config_file = project_path / ".deepwork" / "config.yml"
    if not config_file.exists():
        raise ServeError(
            f"DeepWork not installed in {project_path}. "
            "Run 'deepwork install' first."
        )

    config = load_yaml(config_file)
    if config is None:
        config = {}

    return config


@click.command()
@click.option(
    "--path",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=".",
    help="Path to project directory (default: current directory)",
)
@click.option(
    "--quality-gate",
    type=str,
    default=None,
    help="Command for quality gate agent (e.g., 'claude -p --output-format json')",
)
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse"]),
    default="stdio",
    help="MCP transport protocol (default: stdio)",
)
@click.option(
    "--port",
    type=int,
    default=8000,
    help="Port for SSE transport (default: 8000)",
)
def serve(
    path: Path,
    quality_gate: str | None,
    transport: str,
    port: int,
) -> None:
    """Start the DeepWork MCP server.

    Exposes workflow management tools to AI agents via MCP protocol.
    By default uses stdio transport for local integration with Claude Code.

    Examples:

        # Start server for current directory
        deepwork serve

        # Start with quality gate enabled
        deepwork serve --quality-gate "claude -p --output-format json"

        # Start for a specific project
        deepwork serve --path /path/to/project
    """
    try:
        _serve_mcp(path, quality_gate, transport, port)
    except ServeError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort() from e
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        raise


def _serve_mcp(
    project_path: Path,
    quality_gate_command: str | None,
    transport: str,
    port: int,
) -> None:
    """Start the MCP server.

    Args:
        project_path: Path to project directory
        quality_gate_command: Optional quality gate command
        transport: Transport protocol (stdio or sse)
        port: Port for SSE transport

    Raises:
        ServeError: If server fails to start
    """
    # Validate project has DeepWork installed
    _load_config(project_path)

    # Load quality gate settings from config if not specified via CLI
    config = _load_config(project_path)
    qg_config = config.get("quality_gate", {})

    if quality_gate_command is None:
        quality_gate_command = qg_config.get("agent_review_command")

    # Get timeout and max_attempts from config (with defaults)
    quality_gate_timeout = qg_config.get("default_timeout", 120)
    quality_gate_max_attempts = qg_config.get("default_max_attempts", 3)

    # Create and run server
    from deepwork.mcp.server import create_server

    server = create_server(
        project_root=project_path,
        quality_gate_command=quality_gate_command,
        quality_gate_timeout=quality_gate_timeout,
        quality_gate_max_attempts=quality_gate_max_attempts,
    )

    if transport == "stdio":
        server.run(transport="stdio")
    else:
        server.run(transport="sse", port=port)
