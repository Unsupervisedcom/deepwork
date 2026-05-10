# DeepWork for OpenClaw

This directory is an OpenClaw [Codex bundle](https://docs.openclaw.ai/plugins/bundles) that lets OpenClaw sessions use DeepWork's workflow and review MCP tools.

For how the integration works, why it is shaped this way, and troubleshooting beyond the basics, see [`doc/openclaw_design.md`](../../doc/openclaw_design.md).

## Prerequisites

- OpenClaw with bundle support
- [`uv`](https://docs.astral.sh/uv/) installed (so `uvx` is on PATH)
- a Git repository for the target project (DeepWork stores job definitions under `.deepwork/` and may create work branches)

You do **not** need to install the `deepwork` CLI separately. The bundle launches it via `uvx deepwork serve --platform openclaw`, which auto-fetches the published package on first use.

## Install

```bash
git clone https://github.com/Unsupervisedcom/deepwork.git
openclaw plugins install ./deepwork/plugins/openclaw
openclaw gateway restart
```

Then start a new OpenClaw session. Verify with:

```bash
openclaw plugins inspect deepwork
```

You should see bundle subtype `codex`, skill roots from `skills/`, a hook pack from `hooks/`, and an MCP server named `deepwork`.

## First run

Typical prompts:

- `Use DeepWork to create a workflow for shipping release notes.`
- `Use DeepWork to run the tutorial_writer workflow.`
- `Use DeepWork review on this change set.`

The bundled bootstrap hook will have already told the agent the correct `session_id` to use for DeepWork MCP calls and whether prior DeepWork state exists for the session.

## Runtime layout

- `.codex-plugin/plugin.json` — Codex bundle marker
- `.mcp.json` — declares the `deepwork` MCP server (`uvx deepwork serve --platform openclaw`)
- `skills/deepwork/SKILL.md`, `skills/review/SKILL.md` — agent-facing instructions for `/deepwork` and `/review`
- `hooks/deepwork-openclaw-bootstrap/` — `agent:bootstrap` hook that injects session and resume guidance

See the [design doc](../../doc/openclaw_design.md) for how these pieces fit together, known limitations (notably: session-scoped state across spawned sub-sessions), and troubleshooting for pinning a specific `deepwork` binary.
