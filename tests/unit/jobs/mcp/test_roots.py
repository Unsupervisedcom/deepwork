"""Tests for JOBS-REQ-011: MCP root resolution via listRoots."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from deepwork.jobs.mcp.roots import RootResolver, resolve_project_root


def _make_root(uri: str) -> MagicMock:
    """Create a mock Root object with the given URI."""
    root = MagicMock()
    root.uri = uri
    return root


def _make_ctx(roots: list[MagicMock] | Exception | None = None) -> MagicMock:
    """Create a mock Context whose list_roots returns *roots*."""
    ctx = MagicMock()
    if isinstance(roots, Exception):
        ctx.list_roots = AsyncMock(side_effect=roots)
    elif roots is None:
        ctx.list_roots = AsyncMock(return_value=[])
    else:
        ctx.list_roots = AsyncMock(return_value=roots)
    return ctx


# ---------------------------------------------------------------------------
# resolve_project_root (JOBS-REQ-011.2)
# ---------------------------------------------------------------------------

FALLBACK = Path("/fallback/dir")


@pytest.mark.asyncio
async def test_resolve_single_file_root(tmp_path: Path) -> None:
    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-011.2.2).
    ctx = _make_ctx([_make_root(tmp_path.as_uri())])
    result = await resolve_project_root(ctx, FALLBACK)
    assert result == tmp_path.resolve()


@pytest.mark.asyncio
async def test_resolve_uri_with_spaces(tmp_path: Path) -> None:
    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-011.2.3).
    spaced = tmp_path / "my project"
    spaced.mkdir()
    ctx = _make_ctx([_make_root(spaced.as_uri())])
    result = await resolve_project_root(ctx, FALLBACK)
    assert result == spaced.resolve()


@pytest.mark.asyncio
async def test_fallback_on_empty_roots() -> None:
    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-011.2.6).
    ctx = _make_ctx(None)  # empty list
    result = await resolve_project_root(ctx, FALLBACK)
    assert result == FALLBACK


@pytest.mark.asyncio
async def test_fallback_on_exception() -> None:
    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-011.2.5).
    ctx = _make_ctx(RuntimeError("no client"))
    result = await resolve_project_root(ctx, FALLBACK)
    assert result == FALLBACK


@pytest.mark.asyncio
async def test_skips_non_file_roots(tmp_path: Path) -> None:
    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-011.2.2, JOBS-REQ-011.2.7).
    ctx = _make_ctx(
        [
            _make_root("https://example.com"),
            _make_root(tmp_path.as_uri()),
        ]
    )
    result = await resolve_project_root(ctx, FALLBACK)
    assert result == tmp_path.resolve()


@pytest.mark.asyncio
async def test_fallback_when_no_file_roots() -> None:
    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-011.2.7).
    ctx = _make_ctx([_make_root("https://example.com")])
    result = await resolve_project_root(ctx, FALLBACK)
    assert result == FALLBACK


# ---------------------------------------------------------------------------
# RootResolver — explicit mode (JOBS-REQ-011.1)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_explicit_always_returns_fallback() -> None:
    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-011.1.3).
    resolver = RootResolver(fallback_root=FALLBACK, explicit=True)
    ctx = _make_ctx([_make_root("file:///other/path")])
    result = await resolver.get_root(ctx)
    assert result == FALLBACK
    ctx.list_roots.assert_not_awaited()


def test_startup_root_returns_fallback() -> None:
    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-011.1.6).
    resolver = RootResolver(fallback_root=FALLBACK, explicit=False)
    assert resolver.startup_root == FALLBACK


# ---------------------------------------------------------------------------
# RootResolver — dynamic mode, no caching (JOBS-REQ-011.1)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dynamic_calls_list_roots_every_time() -> None:
    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-011.1.4, JOBS-REQ-011.1.5).
    resolver = RootResolver(fallback_root=FALLBACK, explicit=False)

    root1 = _make_root("file:///first")
    root2 = _make_root("file:///second")

    ctx = MagicMock()
    ctx.list_roots = AsyncMock(side_effect=[[root1], [root2]])

    first = await resolver.get_root(ctx)
    second = await resolver.get_root(ctx)

    assert first == Path("/first")
    assert second == Path("/second")
    assert ctx.list_roots.await_count == 2


@pytest.mark.asyncio
async def test_dynamic_falls_back_on_error() -> None:
    # THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-011.1.4).
    resolver = RootResolver(fallback_root=FALLBACK, explicit=False)
    ctx = _make_ctx(RuntimeError("disconnected"))
    result = await resolver.get_root(ctx)
    assert result == FALLBACK
