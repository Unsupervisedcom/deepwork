# DW-REQ-005: CLI Commands

## Overview

The DeepWork CLI provides four active commands: `serve` (starts the MCP server), `hook` (runs hook scripts), `jobs` (job inspection), and `review` (review instructions), plus two deprecated back-compat commands: `install` and `sync`. The CLI is built with Click and serves as the entry point for `deepwork` executable. The `serve` command is the primary runtime entry point, `hook` provides a generic mechanism for running Python hook modules, and `jobs` provides subcommands for inspecting active workflow sessions.

## Requirements

### DW-REQ-005.1: CLI Entry Point

1. The CLI MUST be a Click group command named `cli`.
2. The CLI MUST provide a `--version` option sourced from the `deepwork` package version.
3. The CLI MUST register `serve`, `hook`, `jobs`, `review`, `install`, and `sync` as subcommands.
4. The CLI MUST be callable as `deepwork` from the command line (via package entry point).

### DW-REQ-005.2: serve Command

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

### DW-REQ-005.3: hook Command

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

### DW-REQ-005.4: jobs Command

1. The `jobs` command MUST be a Click group command.
2. The `jobs` group MUST provide a `get-stack` subcommand.
3. The `get-stack` subcommand MUST accept a `--path` option (default: `"."`, must exist) specifying the project root directory.
4. The `get-stack` subcommand MUST read session files from `.deepwork/tmp/` under the specified path.
5. The `get-stack` subcommand MUST filter for sessions with `status == "active"` only.
6. For each active session, the subcommand MUST include `session_id`, `job_name`, `workflow_name`, `goal`, `current_step_id`, `instance_id`, and `completed_steps` in the output.
7. For each active session, the subcommand SHOULD enrich the output with `common_job_info` and `current_step_instructions` from the job definition when the job directory is found.
8. For each active session, the subcommand SHOULD include `step_number` and `total_steps` when the step's position can be determined from the workflow.
9. If the job directory is not found or the job definition cannot be parsed, the subcommand MUST still include the session with `null` for enrichment fields (graceful degradation).
10. The subcommand MUST output valid JSON to stdout with an `active_sessions` array.
11. If no `.deepwork/tmp/` directory exists or no active sessions are found, the subcommand MUST output `{"active_sessions": []}`.

### DW-REQ-005.5: Deprecated install and sync Commands

> **SCHEDULED REMOVAL: June 1st, 2026; details in PR https://github.com/Unsupervisedcom/deepwork/pull/227.** These commands exist only for
> backwards compatibility with users who installed DeepWork globally via
> `brew` or `uv`. Once all users have migrated to the Claude Code plugin
> distribution model, this entire section and all associated code and tests
> SHOULD be deleted.

1. Both `install` and `sync` MUST be registered as Click commands with `hidden=True` so they do not appear in `--help` output.
2. Both commands MUST execute the same shared implementation (`_run_install_deprecation`).
3. The shared implementation MUST write plugin configuration to `.claude/settings.json`, creating the `.claude/` directory if it does not exist.
4. The configuration MUST merge into existing settings without overwriting unrelated keys (e.g., `permissions`).
5. The written `extraKnownMarketplaces` MUST contain a `deepwork-plugins` entry with source `{"source": "github", "repo": "Unsupervisedcom/deepwork"}`.
6. The written `enabledPlugins` MUST set `deepwork@deepwork-plugins` and `learning-agents@deepwork-plugins` to `true`.
7. If `.claude/settings.json` exists but contains invalid JSON, the command MUST treat it as an empty settings object (not crash).
8. Both commands MUST print a deprecation message that includes `brew uninstall deepwork` and `uv tool uninstall deepwork` instructions.
