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
    hidden=True,
    help="Deprecated. Quality gate now uses DeepWork Reviews infrastructure.",
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
    hidden=True,
    help="Deprecated. Quality gate now uses DeepWork Reviews infrastructure.",
)
@click.option(
    "--platform",
    type=str,
    default=None,
    help="Platform identifier (e.g., 'claude'). Used by the review tool to format output.",
)
def serve(
    path: Path,
    no_quality_gate: bool,
    transport: str,
    port: int,
    external_runner: str | None,
    platform: str | None,
) -> None:
    """Start the DeepWork MCP server.

    Exposes workflow management tools to AI agents via MCP protocol.
    By default uses stdio transport for local integration with Claude Code.

    Quality reviews are handled by the DeepWork Reviews infrastructure
    (dynamic review rules from job.yml + .deepreview file rules).

    Examples:

        # Start server for current directory
        deepwork serve

        # Start for a specific project
        deepwork serve --path /path/to/project

        # SSE transport for remote access
        deepwork serve --transport sse --port 8000
    """
    try:
        _serve_mcp(path, transport, port, platform)
    except ServeError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort() from e
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        raise


def _serve_mcp(
    project_path: Path,
    transport: str,
    port: int,
    platform: str | None = None,
) -> None:
    """Start the MCP server.

    Args:
        project_path: Path to project directory
        transport: Transport protocol (stdio or sse)
        port: Port for SSE transport
        platform: Platform identifier for the review tool (e.g., "claude").

    Raises:
        ServeError: If server fails to start
    """
    # Ensure .deepwork/tmp/ exists for session state
    tmp_dir = project_path / ".deepwork" / "tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    # Ensure .deepwork/tmp/.gitignore exists to keep tmp contents out of git
    tmp_gitignore = tmp_dir / ".gitignore"
    if not tmp_gitignore.exists():
        tmp_gitignore.write_text(
            "# Ignore everything in this directory\n*\n# But keep this .gitignore\n!.gitignore\n"
        )

    # Create and run server
    from deepwork.jobs.mcp.server import create_server

    server = create_server(
        project_root=project_path,
        platform=platform,
    )

    if transport == "stdio":
        server.run(transport="stdio")
    else:
        server.run(transport="sse", port=port)
