# DeepWork on OpenClaw — Design Doc

This document describes how DeepWork integrates with [OpenClaw](https://openclaw.ai), why the integration is shaped the way it is, and how the moving parts fit together.

Primary reference: [OpenClaw — Building Plugins](https://docs.openclaw.ai/plugins/building-plugins). Related pages: [Plugin Bundles](https://docs.openclaw.ai/plugins/bundles), [Hooks](https://docs.openclaw.ai/automation/hooks), [Skills](https://docs.openclaw.ai/tools/skills), [mcp CLI](https://docs.openclaw.ai/cli/mcp), [Agent Bootstrapping](https://docs.openclaw.ai/start/bootstrapping).

## Goal

Let an OpenClaw session use DeepWork's workflow engine and review system through MCP, with no DeepWork-specific pre-install on the host, and no Claude-specific machinery.

## Why a Codex bundle, not a native OpenClaw plugin

OpenClaw supports two plugin formats:

- **Native plugins** — npm package with `package.json`, `openclaw.plugin.json`, and a TypeScript entry point that calls `api.registerTool(...)`, `api.registerHook(...)`, etc. Plugins run in-process in the OpenClaw gateway.
- **Codex bundles** — content packs that OpenClaw maps onto its native features. A bundle is identified by a `.codex-plugin/plugin.json` marker and may ship `skills/`, `hooks/`, `.mcp.json`, and `.app.json`. No entry point, no npm package, no TypeScript. See [Plugin Bundles](https://docs.openclaw.ai/plugins/bundles).

DeepWork is an out-of-process MCP server written in Python. It does not need to run inside the OpenClaw gateway. The Codex bundle format fits exactly: declare the MCP server in `.mcp.json`, ship skill instructions the agent reads when the user invokes `/deepwork` or `/review`, and ship one bootstrap hook so the agent sees the right `session_id` up front. This is strictly less machinery than a native plugin and gives the same runtime behavior.

## File layout

```
plugins/openclaw/
├── .codex-plugin/
│   └── plugin.json                         # Codex bundle marker
├── .mcp.json                               # Registers the DeepWork MCP server
├── skills/
│   ├── deepwork/SKILL.md                   # /deepwork skill — workflow execution
│   └── review/SKILL.md                     # /review skill — DeepWork reviews
└── hooks/
    └── deepwork-openclaw-bootstrap/
        ├── HOOK.md                         # Declares the agent:bootstrap hook
        └── handler.ts                      # Injects session/resume context
```

Nothing else in this bundle is required. No `package.json`. No `index.ts`. No `openclaw.plugin.json`. Those belong to native plugins, not Codex bundles.

## Install flow (what the user actually does)

1. Install `uv` (so `uvx` is on PATH).
2. Clone DeepWork, or otherwise get the bundle on disk.
3. `openclaw plugins install /path/to/deepwork/plugins/openclaw`
4. Restart the OpenClaw gateway and start a new session.

No `uv tool install deepwork`. No `pip install`. The MCP config uses `uvx deepwork serve --platform openclaw`, so `uvx` fetches and caches the published `deepwork` package on first launch and auto-resolves updates on subsequent runs. Users get updates by letting `uvx` refresh the cache (or by running `uv cache clean` if they want to force a refresh); they do not need to re-run an install step.

The "bundle still has to be on disk" part is the one remaining pre-install step, and the right fix is publishing the bundle to ClawHub or npm so `openclaw plugins install clawhub:unsupervisedcom/deepwork` works. Until then, pointing `openclaw plugins install` at the cloned repo path is the intended flow.

## Runtime contract

DeepWork's MCP tools require a `session_id` on every call. In OpenClaw, we map that to the current session's `sessionId`. In Claude Code, we map it to `CLAUDE_CODE_SESSION_ID`. The MCP server itself is unchanged between platforms — `--platform openclaw` only affects the adapter that formats review output, not the tool shapes.

Session state lives under the workspace at:

```
.deepwork/tmp/sessions/openclaw/session-<sessionId>/state.json
```

This scoping means resume works inside a single OpenClaw session. Spawned child sessions get their own session directories; they do not yet share a DeepWork workflow stack with their parent the way Claude Code does. That shared-root model depends on parent/root session metadata that OpenClaw's current bootstrap hook surface does not expose. We'll revisit when it does.

## The bootstrap hook

Skills tell the agent what to do when the user invokes `/deepwork` or `/review`. The bootstrap hook exists because the agent also needs to know *which* `session_id` to use before it makes any MCP call — and the agent cannot read that from the skill file alone.

`HOOK.md` registers a hook on the [`agent:bootstrap`](https://docs.openclaw.ai/automation/hooks) event. `handler.ts` receives the event, reads `context.sessionId`, `context.sessionKey`, `context.agentId`, and `context.workspaceDir`, and appends a synthetic bootstrap file to `context.bootstrapFiles` telling the agent:

- the exact `session_id` to pass to every DeepWork MCP call
- whether DeepWork state already exists for this session (detected by checking for `state.json` on disk) — if so, prompt the agent to call `deepwork__get_active_workflow` before starting a new workflow
- the review-spawn conventions specific to OpenClaw (`sessions_spawn` + `sessions_yield`, no `timeoutSeconds` unless `0`, workspace-relative instruction paths)

The handler also writes the same note to disk as a best-effort fallback, but the in-memory `bootstrapFiles` injection is the load-bearing mechanism.

## Reviews on OpenClaw

DeepWork quality gates can return review tasks that the agent needs to run in parallel. Claude Code runs these as sub-tasks via the Task tool. OpenClaw runs them as parallel sub-agents via [`sessions_spawn`](https://docs.openclaw.ai/) + [`sessions_yield`](https://docs.openclaw.ai/).

The review instructions returned by the MCP server are platform-neutral. The OpenClaw-specific skill file (`skills/review/SKILL.md`) tells the agent how to dispatch them as OpenClaw sub-agents. The Claude formatter path in the DeepWork runtime is separate and unchanged.

## Troubleshooting

### DeepWork tools don't appear

- Confirm `openclaw plugins inspect deepwork` shows a bundle with an MCP server.
- Restart the OpenClaw gateway and start a fresh session.
- Verify `uvx deepwork --version` works in your shell. If `uvx` is not on PATH, install `uv`.

### OpenClaw launches the wrong DeepWork binary

Add a top-level `mcp.servers.deepwork` override in OpenClaw's config that points at an exact executable:

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

Restart the gateway after the change. This is a rare case — `uvx` resolution is normally correct.

### Testing unreleased DeepWork changes from a local checkout

Register the checkout as an editable `uv` tool so `uvx deepwork` resolves to your local source:

```bash
uv tool install -e /path/to/deepwork
```

If you want the gateway to launch a specific binary regardless of `PATH`, use the top-level `mcp.servers.deepwork` override above.

### Agent starts a second workflow instead of resuming

Tell the agent to call `deepwork__get_active_workflow` first. The bootstrap hook already prompts this when it detects prior state on disk; if the hook did not run, the skill file will still produce the correct behavior when the agent reads it.

## Known limitations

- **Session-scoped state.** Parent/child OpenClaw sessions do not yet share one DeepWork workflow stack. Revisit when OpenClaw exposes parent/root session metadata in the bootstrap context.
- **Bundle distribution.** Until the bundle is published to ClawHub or npm, the install step requires a local clone of DeepWork.
- **No auto-update for MCP servers.** OpenClaw does not refresh plugin-declared MCP servers automatically. `uvx`'s own cache handles version updates, but a gateway restart may be needed to pick up a new binary.
