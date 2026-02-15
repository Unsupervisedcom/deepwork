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
        raise ServeError(f"DeepWork not installed in {project_path}. Run 'deepwork install' first.")

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
    "--no-quality-gate",
    is_flag=True,
    default=False,
    help="Disable quality gate evaluation",
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
@click.option(
    "--external-runner",
    type=click.Choice(["claude"]),
    default=None,
    help="External runner for quality gate reviews. 'claude' uses Claude CLI subprocess. Default: None (agent self-review).",
)
def serve(
    path: Path,
    no_quality_gate: bool,
    transport: str,
    port: int,
    external_runner: str | None,
) -> None:
    """Start the DeepWork MCP server.

    Exposes workflow management tools to AI agents via MCP protocol.
    By default uses stdio transport for local integration with Claude Code.

    Quality gate is enabled by default. Use --external-runner to specify
    how quality reviews are executed:

    \b
    - No flag (default): Agent self-review via instructions file
    - --external-runner claude: Claude CLI subprocess review

    Examples:

        # Start server for current directory (agent self-review)
        deepwork serve

        # Start with Claude CLI as quality gate reviewer
        deepwork serve --external-runner claude

        # Start with quality gate disabled
        deepwork serve --no-quality-gate

        # Start for a specific project
        deepwork serve --path /path/to/project
    """
    try:
        _serve_mcp(path, not no_quality_gate, transport, port, external_runner)
    except ServeError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort() from e
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        raise


def _serve_mcp(
    project_path: Path,
    enable_quality_gate: bool,
    transport: str,
    port: int,
    external_runner: str | None = None,
) -> None:
    """Start the MCP server.

    Args:
        project_path: Path to project directory
        enable_quality_gate: Whether to enable quality gate evaluation
        transport: Transport protocol (stdio or sse)
        port: Port for SSE transport
        external_runner: External runner for quality gate reviews.
            "claude" uses Claude CLI subprocess. None means agent self-review.

    Raises:
        ServeError: If server fails to start
    """
    # Validate project has DeepWork installed
    _load_config(project_path)

    # Create and run server
    from deepwork.mcp.server import create_server

    server = create_server(
        project_root=project_path,
        enable_quality_gate=enable_quality_gate,
        external_runner=external_runner,
    )

    if transport == "stdio":
        server.run(transport="stdio")
    else:
        server.run(transport="sse", port=port)
