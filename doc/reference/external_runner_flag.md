# The `--external-runner` Flag

The `--external-runner` flag on `deepwork serve` controls **how the quality gate evaluates step outputs** when an agent calls `finished_step`.

## Overview

When a step completes, the quality gate checks the agent's outputs against the step's quality criteria. The `--external-runner` flag determines the execution strategy for that check.

There are three modes:

| Mode | Flag | Behavior |
|------|------|-----------|
| **External runner** | `--external-runner claude` | DeepWork invokes Claude Code as a subprocess to run each review and returns pass/fail results directly to the MCP response. |
| **Self-review** (default) | _(omit flag)_ | DeepWork writes a review instructions file to `.deepwork/tmp/` and asks the calling agent to spawn a subagent to perform the review. |
| **Disabled** | `--no-quality-gate` | Quality gate evaluation is skipped entirely. `finished_step` always proceeds to the next step. |

## Values

The flag currently accepts one value:

- **`claude`** — Invokes Claude Code (`claude`) as a subprocess using `--print` mode with structured JSON output. Requires Claude Code to be installed and on `PATH`.

## External Runner Mode (`--external-runner claude`)

```bash
deepwork serve --external-runner claude
deepwork serve --path /path/to/project --external-runner claude
```

In this mode:

1. The agent calls `finished_step` with its outputs.
2. DeepWork assembles a review payload containing the step's quality criteria and the agent's output files.
3. DeepWork invokes `claude` as a subprocess with the payload.
4. Claude evaluates each quality criterion and returns structured JSON (`passed`, `feedback`, `criteria_results`).
5. If the step passes, `finished_step` returns the next step instructions.
6. If the step fails, `finished_step` returns feedback for the agent to address before retrying.

**File embedding strategy**: Up to 5 output files are embedded inline in the review payload. When a step produces more than 5 files, only the file paths are listed and the reviewer is expected to read them directly.

**When to use**: This mode is suitable when Claude Code is available as a subprocess (e.g., in the Claude Code plugin environment). It provides automated, synchronous quality enforcement without requiring the calling agent to spin up its own subagent.

## Self-Review Mode (default — no flag)

```bash
deepwork serve
deepwork serve --path /path/to/project
```

In this mode:

1. The agent calls `finished_step` with its outputs.
2. DeepWork writes a review instructions file to `.deepwork/tmp/quality_review_<session>_<workflow>_<step>.md`.
3. `finished_step` returns a response instructing the calling agent to spawn a subagent using that instructions file.
4. The calling agent runs the subagent review and calls `finished_step` again with the results.

**File embedding strategy**: Output files are never embedded inline — only paths are listed. The subagent is expected to read them from disk.

**When to use**: This mode is appropriate when no external runner is available or when you prefer the calling agent to own the review step explicitly.

## Disabled Mode (`--no-quality-gate`)

```bash
deepwork serve --no-quality-gate
```

Quality gate evaluation is skipped. `finished_step` always moves to the next step regardless of output quality. Useful for development, testing, or workflows where quality criteria are enforced by other means.

## Plugin Default

The Claude Code plugin's `.mcp.json` uses `--external-runner claude` by default, so that quality gate reviews run automatically via Claude subprocess without extra agent turns:

```json
{
  "mcpServers": {
    "deepwork": {
      "command": "uvx",
      "args": ["deepwork", "serve", "--path", ".", "--external-runner", "claude", "--platform", "claude"]
    }
  }
}
```

## All Serve Options

For reference, the complete set of `deepwork serve` options:

| Option | Default | Description |
|--------|---------|-------------|
| `--path <dir>` | `.` | Project directory |
| `--external-runner claude` | None (self-review) | Quality gate execution strategy |
| `--no-quality-gate` | False | Disable quality gate entirely |
| `--transport stdio\|sse` | `stdio` | MCP transport protocol |
| `--port <n>` | `8000` | Port for SSE transport |
| `--platform <name>` | None | Platform identifier for review output formatting |

## Related

- [`doc/reference/calling_claude_in_print_mode.md`](calling_claude_in_print_mode.md) — How DeepWork invokes Claude Code as a subprocess for quality gate reviews
- [`doc/architecture.md`](../architecture.md) — Quality Gate section for implementation details
