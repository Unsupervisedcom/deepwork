"""Serve command for DeepWork MCP server."""

from pathlib import Path

import click


class ServeError(Exception):
    """Exception raised for serve errors."""

    pass


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
        click.echo(f"Error: {e}", err=True)
        raise click.Abort() from e
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
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
    # Ensure .deepwork/tmp/ exists for session state
    tmp_dir = project_path / ".deepwork" / "tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)

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
