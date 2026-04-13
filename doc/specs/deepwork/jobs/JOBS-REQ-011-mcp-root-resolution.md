# JOBS-REQ-011: MCP Root Resolution via listRoots

## Overview

The MCP server resolves the project root dynamically using the MCP `listRoots` client capability. This allows the server to track workspace changes mid-session (e.g. when the client switches to a git worktree). When `--path` is explicitly provided on the CLI, the server uses that path unconditionally and does not consult `listRoots`.

## Requirements

### JOBS-REQ-011.1: Root Resolver

1. The system MUST provide a `RootResolver` class in `deepwork.jobs.mcp.roots`.
2. `RootResolver` MUST accept a `fallback_root` (Path) and an `explicit` (bool) keyword argument at construction.
3. When `explicit` is `True`, `get_root()` MUST always return `fallback_root` without calling `list_roots()`.
4. When `explicit` is `False`, `get_root()` MUST call `ctx.list_roots()` on every invocation.
5. `RootResolver` MUST NOT cache roots across tool calls — the client may change roots mid-session (e.g. via worktree switches).
6. `RootResolver` MUST provide a `startup_root` property that returns `fallback_root` for code that runs before a client connects.

### JOBS-REQ-011.2: Root Resolution Logic

1. The system MUST provide an async `resolve_project_root(ctx, fallback)` function.
2. The function MUST call `ctx.list_roots()` and return the first root whose URI scheme is `file`.
3. The function MUST convert `file://` URIs to `Path` objects using `urllib.parse.urlparse` and `urllib.parse.unquote` for correct handling of percent-encoded characters (e.g. spaces).
4. The returned `Path` MUST be resolved to an absolute path.
5. If `list_roots()` raises an exception, the function MUST return `fallback`.
6. If `list_roots()` returns an empty list, the function MUST return `fallback`.
7. If no root with a `file` URI scheme is found, the function MUST return `fallback`.

### JOBS-REQ-011.3: Tool Handler Integration

1. All MCP tool handlers (`get_workflows`, `start_workflow`, `finished_step`, `abort_workflow`, `go_to_step`, `get_named_schemas`, `get_review_instructions`, `get_configured_reviews`, `mark_review_as_passed`) MUST accept a `Context` parameter (auto-injected by FastMCP).
2. All MCP tool handlers MUST call `root_resolver.get_root(ctx)` to obtain the project root before executing their logic.
3. The resolved root MUST be used for job discovery, schema discovery, review rule discovery, file path validation, and all other operations that depend on the project root.
4. Startup-time operations (schema copy, manifest writing, issue detection, StateManager/StatusWriter construction) MUST continue using the startup root, not `listRoots`.

### JOBS-REQ-011.4: CLI Integration

1. When `--path` is not provided to `deepwork serve`, the CLI MUST pass `explicit_path=False` to `create_server()`.
2. When `--path` is explicitly provided, the CLI MUST pass `explicit_path=True` to `create_server()`.
3. When `--path` is not provided, the CLI MUST use `Path.cwd()` as the fallback root.
