# DeepWork for OpenClaw

This bundle lets OpenClaw use DeepWork's workflow and review MCP tools without relying on Claude-specific hooks.

It packages three things together:

- OpenClaw skills for DeepWork workflows and reviews
- an OpenClaw bootstrap hook that injects DeepWork session guidance
- an MCP config that starts `uvx deepwork serve --platform openclaw`

## What This Bundle Adds

When OpenClaw installs this directory as a bundle, it loads:

- [`.codex-plugin/plugin.json`](./.codex-plugin/plugin.json) so the directory is detected as a Codex bundle
- [`skills/deepwork/SKILL.md`](./skills/deepwork/SKILL.md) for workflow execution guidance
- [`skills/review/SKILL.md`](./skills/review/SKILL.md) for review execution guidance
- [`hooks/deepwork-openclaw-bootstrap/HOOK.md`](./hooks/deepwork-openclaw-bootstrap/HOOK.md) and [`handler.ts`](./hooks/deepwork-openclaw-bootstrap/handler.ts) to inject session and resume context into OpenClaw bootstrap
- [`.mcp.json`](./.mcp.json) so OpenClaw exposes DeepWork MCP tools as `deepwork__<tool_name>`

This is an OpenClaw-native bundle shape. It does not depend on Claude's `hooks.json` automation.

## Prerequisites

- OpenClaw with bundle support
- a DeepWork runtime that supports `deepwork serve --platform openclaw`
- `uv` installed, because the bundle launches DeepWork with `uvx`
- a Git repository for the target project

DeepWork stores job definitions under `.deepwork/` and may create work branches while executing workflows. If the target project is not already a Git repository, initialize it first.

## Install

### 1. Clone DeepWork

OpenClaw installs the bundle from this directory, so start by cloning the DeepWork repo:

```bash
git clone https://github.com/Unsupervisedcom/deepwork.git
cd deepwork
```

If you are testing an unreleased branch, check out that branch before continuing. Otherwise stay on the default branch or a released tag.

### 2. Install DeepWork

```bash
uv tool install deepwork
```

This installs the `deepwork` CLI that the OpenClaw bundle launches over MCP.

Verify that the installed runtime supports OpenClaw:

```bash
deepwork serve --platform openclaw
```

If that command fails, upgrade to a newer DeepWork release before installing the bundle.

### 3. Install the OpenClaw bundle

Install the bundle from this checkout:

```bash
openclaw plugins install /path/to/deepwork/plugins/openclaw
openclaw plugins inspect deepwork
openclaw gateway restart
```

Expected output from `openclaw plugins inspect deepwork`:

- `Format: bundle`
- bundle subtype `codex`
- skill roots from `skills/`
- a hook pack from `hooks/`
- an MCP server named `deepwork`

## First Run

Start a new OpenClaw session after installing the bundle.

Typical user prompts:

- `Use DeepWork to create a workflow for shipping release notes.`
- `Use DeepWork to run the tutorial_writer workflow.`
- `Use DeepWork review on this change set.`

The agent should then:

1. Read the injected DeepWork bootstrap note.
2. Use the current OpenClaw `sessionId` as DeepWork `session_id`.
3. Call `deepwork__get_active_workflow` before starting something new if prior DeepWork state exists.
4. Use `deepwork__get_workflows` and `deepwork__start_workflow` to execute workflows.
5. Before `deepwork__finished_step`, compare your payload to `step_expected_outputs` or call `deepwork__validate_step_outputs`.
6. Use `deepwork__get_review_instructions` and launch review tasks with `sessions_spawn`.

## Runtime Contract

This bundle deliberately keeps the DeepWork runtime mostly unchanged and adapts OpenClaw to it.

- DeepWork `session_id` maps to the current OpenClaw `sessionId`
- DeepWork `agent_id` is usually left unset in OpenClaw
- the bootstrap hook writes a synthetic note into bootstrap context so the agent sees the correct `session_id`
- if DeepWork state already exists for the current session, the hook tells the agent to call `deepwork__get_active_workflow`

DeepWork session state for this bundle lives under:

```text
.deepwork/tmp/sessions/openclaw/session-<sessionId>/state.json
```

## Reviews in OpenClaw

DeepWork quality gates can return review tasks. In OpenClaw, those should be run as parallel sub-agents with `sessions_spawn`.

That is why this bundle includes a separate OpenClaw review skill and platform-specific quality-gate formatting. The Claude formatter path is still separate and unchanged.

## Current Limitation

This first OpenClaw adapter scopes DeepWork state to the current OpenClaw session.

That means:

- resume works reliably inside the same OpenClaw session
- `deepwork__get_active_workflow` works after compaction or reset for that same session
- spawned OpenClaw child sessions do not yet share one root DeepWork workflow stack the way Claude Code can

This is a host-context limitation, not a workflow-engine limitation. The current OpenClaw bootstrap hook surface does not expose enough parent/root session metadata to recreate DeepWork's Claude-style shared root session model.

## Troubleshooting

### The DeepWork tools do not appear in OpenClaw

Check:

- the bundle was installed from this directory, not the repo root
- `openclaw plugins inspect deepwork` shows a bundle with an MCP server
- you restarted the OpenClaw gateway after installation
- you started a fresh OpenClaw session after the restart
- the runtime itself starts cleanly:

```bash
uvx deepwork --version
uvx deepwork serve --platform openclaw
```

If `uvx` works in your shell but OpenClaw still does not expose the tools, use the pinned top-level `mcp.servers.deepwork` override shown in the troubleshooting steps below so the gateway launches an exact binary instead of relying on `PATH` or `uvx` resolution.

### I am testing unreleased DeepWork changes from a local checkout

Register the checkout as an editable `uv` tool:

```bash
uv tool install -e /path/to/deepwork
```

This makes `uvx deepwork` resolve to your checkout instead of whatever version is published.

If OpenClaw is still launching the wrong binary, add a top-level `mcp.servers.deepwork` override that points to the exact `deepwork` executable you want:

```json
{
  "mcp": {
    "servers": {
      "deepwork": {
        "command": "/absolute/path/to/deepwork",
        "args": ["serve", "--platform", "openclaw"]
      }
    }
  }
}
```

Restart the OpenClaw gateway after changing the override.

### OpenClaw is launching the wrong DeepWork binary

Check both launch paths explicitly:

```bash
uvx deepwork --version
deepwork --version
```

Then point OpenClaw at the exact binary you want with a top-level `mcp.servers.deepwork` override:

```json
{
  "mcp": {
    "servers": {
      "deepwork": {
        "command": "/absolute/path/to/deepwork",
        "args": ["serve", "--platform", "openclaw"]
      }
    }
  }
}
```

Restart the OpenClaw gateway after changing the override.

### The agent starts a second workflow instead of resuming

Tell the agent to call `deepwork__get_active_workflow` first. That is the intended resume path for OpenClaw after session restore, compaction, or ambiguity about current state.

## Note for Existing Claude Users

If you already use the Claude Code DeepWork plugin on this machine, you may already have a working DeepWork runtime via `uvx`. Before installing DeepWork separately, check:

```bash
uvx deepwork --version
uvx deepwork serve --platform openclaw
```

If that works, you can use the existing runtime. If it fails, install DeepWork explicitly with `uv tool install deepwork` and then continue with the steps above.
