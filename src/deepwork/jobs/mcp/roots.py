"""MCP root resolution via listRoots client capability.

Resolves the project root dynamically by asking the MCP client for its
filesystem roots. When ``--path`` is explicitly passed on the CLI the
resolver always returns that path. Otherwise it calls ``ctx.list_roots()``
on every tool invocation so it tracks workspace changes (e.g. git worktree
switches) without caching stale values.

For OpenClaw bundle installs, the MCP server can be launched from the plugin
bundle directory itself (for example ``plugins/openclaw``) when the host does
not expose a usable ``listRoots`` capability. In that case we normalize the
bundle directory back to the enclosing workspace root when we can detect
OpenClaw workspace markers.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import unquote, urlparse

if TYPE_CHECKING:
    from fastmcp import Context

logger = logging.getLogger("deepwork.jobs.mcp")

_OPENCLAW_PLUGIN_MARKER = Path(".codex-plugin") / "plugin.json"
_OPENCLAW_WORKSPACE_MARKER = Path(".openclaw") / "workspace-state.json"


async def resolve_project_root(ctx: Context, fallback: Path) -> Path:
    """Ask the MCP client for its filesystem root.

    Calls ``ctx.list_roots()`` and returns the first root whose URI uses the
    ``file`` scheme.  Falls back to *fallback* when the call fails, returns
    no roots, or none of the roots use the ``file`` scheme.
    """
    try:
        roots = await ctx.list_roots()
    except Exception:
        logger.debug("list_roots unavailable, using fallback %s", fallback)
        return fallback

    for root in roots:
        uri = str(root.uri)
        parsed = urlparse(uri)
        if parsed.scheme == "file":
            path = Path(unquote(parsed.path)).resolve()
            logger.debug("Resolved project root from listRoots: %s", path)
            return path

    logger.debug("No file:// root found, using fallback %s", fallback)
    return fallback


class RootResolver:
    """Resolve the project root for each MCP tool call.

    Parameters
    ----------
    fallback_root:
        The directory to use when ``list_roots`` is unavailable (typically
        the process working directory or an explicit ``--path`` value).
    explicit:
        When ``True`` the *fallback_root* was explicitly provided via
        ``--path`` and MUST be used unconditionally.  ``list_roots`` is
        never consulted.
    """

    def __init__(self, fallback_root: Path, *, explicit: bool) -> None:
        self._fallback = fallback_root
        self._explicit = explicit

    @property
    def startup_root(self) -> Path:
        """Return the root for startup code that runs before a client connects."""
        return self._fallback

    async def get_root(self, ctx: Context) -> Path:
        """Return the project root for the current tool invocation.

        When ``--path`` was explicitly set, returns *fallback_root* without
        consulting the client.  Otherwise calls ``list_roots()`` every time
        so workspace changes (e.g. worktree switches) are picked up
        immediately.
        """
        if self._explicit:
            return self._fallback
        candidate = await resolve_project_root(ctx, self._fallback)
        return _normalize_openclaw_bundle_root(candidate)


def _normalize_openclaw_bundle_root(candidate: Path) -> Path:
    """Map an OpenClaw plugin bundle path back to the workspace root."""

    resolved = candidate.resolve()
    if not (resolved / _OPENCLAW_PLUGIN_MARKER).exists():
        return resolved

    for ancestor in (resolved, *resolved.parents):
        if (ancestor / _OPENCLAW_WORKSPACE_MARKER).exists():
            logger.debug(
                "Normalized OpenClaw plugin bundle root %s to workspace root %s",
                resolved,
                ancestor,
            )
            return ancestor

    return resolved
