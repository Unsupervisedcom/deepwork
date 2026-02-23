# REQ-005: CLI Commands

## Overview

The DeepWork CLI provides two primary commands: `serve` (starts the MCP server) and `hook` (runs hook scripts), plus two deprecated back-compat commands: `install` and `sync`. The CLI is built with Click and serves as the entry point for `deepwork` executable. The `serve` command is the primary runtime entry point, while `hook` provides a generic mechanism for running Python hook modules.

## Requirements

### REQ-005.1: CLI Entry Point

1. The CLI MUST be a Click group command named `cli`.
2. The CLI MUST provide a `--version` option sourced from the `deepwork` package version.
3. The CLI MUST register `serve`, `hook`, `install`, and `sync` as subcommands.
4. The CLI MUST be callable as `deepwork` from the command line (via package entry point).

### REQ-005.2: serve Command

1. The `serve` command MUST be a Click command.
2. The `serve` command MUST accept a `--path` option (default: `"."`, must exist, must be a directory).
3. The `serve` command MUST accept a `--no-quality-gate` flag (default: False). When set, quality gate evaluation MUST be disabled.
4. The `serve` command MUST accept a `--transport` option with choices `"stdio"` or `"sse"` (default: `"stdio"`).
5. The `serve` command MUST accept a `--port` option (integer, default: 8000) for SSE transport.
6. The `serve` command MUST accept an `--external-runner` option with choice `"claude"` (default: None).
7. Before starting the server, the `serve` command MUST create the `.deepwork/tmp/` directory under the specified path (with `parents=True, exist_ok=True`).
8. The `serve` command MUST create the MCP server via `create_server()` with the resolved path and configuration options.
9. When transport is `"stdio"`, the server MUST be run with `transport="stdio"`.
10. When transport is `"sse"`, the server MUST be run with `transport="sse"` and the specified port.
11. The `serve` command MUST catch `ServeError` and print a user-friendly error message to stderr, then abort.
12. The `serve` command MUST propagate other unexpected exceptions.

### REQ-005.3: hook Command

1. The `hook` command MUST be a Click command.
2. The `hook` command MUST accept a single positional argument `HOOK_NAME`.
3. If `HOOK_NAME` contains a dot (`.`), the system MUST treat it as a fully-qualified Python module path (e.g., `deepwork.hooks.my_hook`).
4. If `HOOK_NAME` does not contain a dot, the system MUST construct the module path as `deepwork.hooks.{hook_name}`.
5. The system MUST dynamically import the resolved module using `importlib.import_module()`.
6. If the module is not found, the system MUST raise `HookError` with a message indicating the hook was not found.
7. If the module is found, the system MUST check for a `main()` function.
8. If the module has a `main()` function, the system MUST call `sys.exit(module.main())`.
9. If the module does not have a `main()` function, the system MUST raise `HookError`.
10. `HookError` exceptions MUST be caught and printed to stderr with exit code 1.
11. Other unexpected exceptions MUST be caught and printed to stderr with exit code 1.

### REQ-005.4: Deprecated install and sync Commands

> **SCHEDULED REMOVAL: June 1st, 2026; details in PR https://github.com/Unsupervisedcom/deepwork/pull/227.** These commands exist only for
> backwards compatibility with users who installed DeepWork globally via
> `uv`. Once all users have migrated to the Claude Code plugin
> distribution model, this entire section and all associated code and tests
> SHOULD be deleted.

1. Both `install` and `sync` MUST be registered as Click commands with `hidden=True` so they do not appear in `--help` output.
2. Both commands MUST execute the same shared implementation (`_run_install_deprecation`).
3. The shared implementation MUST write plugin configuration to `.claude/settings.json`, creating the `.claude/` directory if it does not exist.
4. The configuration MUST merge into existing settings without overwriting unrelated keys (e.g., `permissions`).
5. The written `extraKnownMarketplaces` MUST contain a `deepwork-plugins` entry with source `{"source": "github", "repo": "Unsupervisedcom/deepwork"}`.
6. The written `enabledPlugins` MUST set `deepwork@deepwork-plugins` and `learning-agents@deepwork-plugins` to `true`.
7. If `.claude/settings.json` exists but contains invalid JSON, the command MUST treat it as an empty settings object (not crash).
8. Both commands MUST print a deprecation message that includes `uv tool uninstall deepwork` instructions.
