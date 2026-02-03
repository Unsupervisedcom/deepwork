"""DeepWork MCP Server module.

This module provides an MCP (Model Context Protocol) server that guides AI agents
through DeepWork workflows via checkpoint calls with quality gate enforcement.

The server exposes three main tools:
- get_workflows: List all available workflows
- start_workflow: Initialize a workflow session
- finished_step: Report step completion and get next instructions

Example usage:
    deepwork serve --path /path/to/project
"""


def create_server(*args, **kwargs):  # type: ignore
    """Lazy import to avoid loading fastmcp at module import time."""
    from deepwork.mcp.server import create_server as _create_server

    return _create_server(*args, **kwargs)


__all__ = ["create_server"]
