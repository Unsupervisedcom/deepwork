---
name: new_user
description: "Welcome new users to DeepWork — introduce features, set up reviews, and optionally record a first workflow"
disable-model-invocation: true
---

# New User Onboarding

Guide a new user through what DeepWork can do and help them get started.

## Flow

### 0. Check dependencies and run setup

#### 0a. Check for `uv`

The DeepWork MCP server requires `uv` (specifically `uvx`). Check if it is installed:

```bash
command -v uv
```

**If `uv` is NOT found**, install it:

- On macOS/Linux:
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
- On Windows (PowerShell):
  ```powershell
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```

After installing, verify it works:
```bash
uv --version
```

If `uv` was just installed, set `UV_WAS_INSTALLED=true` (you will need this later).

#### 0b. Reload if `uv` was just installed

If `UV_WAS_INSTALLED=true` (from step 0a), the MCP server could not have started when this session began because `uvx` was missing. Use `AskUserQuestion` to tell the user:

> I just installed `uv`, which DeepWork's MCP server needs to run. For everything to work, please type `/reload-plugins` now, then come back and tell me it's done.

Wait for the user to confirm they have reloaded. Do not proceed until they confirm.

#### 0c. Run setup

Run the setup command to configure Claude Code settings (marketplace, plugin, MCP permissions, auto-update):

```bash
uvx deepwork setup
```

Proceed regardless of the output.

#### 0d. Verify the MCP server is running

Call `get_workflows` (using the `mcp__plugin_deepwork_deepwork__get_workflows` tool). If it succeeds, the server is healthy — continue. If it errors, tell the user:

> The DeepWork MCP server isn't responding. This usually means `uv` isn't on your PATH or the plugin needs a restart. Try quitting Claude Code completely and reopening it, then run `/deepwork:new_user` again.

Stop the onboarding if the server is not reachable — continuing without it will just produce more confusing errors.

#### 0e. macOS note (macOS only)

If the platform is macOS, briefly mention:

> **Heads up**: during reviews or workflows that scan files, macOS may pop up permission dialogs for Photos, Dropbox, or other locations outside this project. These are safe to **deny** — DeepWork only needs access to your project directory and the review will still complete fine.

### 1. GitHub star (optional)

Check if the `gh` CLI is installed by running `which gh`.

If `gh` is available, use `AskUserQuestion` to say something like:

> Thanks for installing DeepWork! Would you mind starring the repo on GitHub so you get notified about updates?

If they agree, run:

```bash
gh api -X PUT /user/starred/Unsupervisedcom/deepwork
```

If `gh` is not installed, skip this entirely — do not mention it.

### 2. Introduce DeepWork

Print a brief welcome message explaining what DeepWork does. Lead with the core value proposition: DeepWork makes AI agents **reliable**. It gives you mechanisms to be assured that Claude will do the right things in the process of achieving your requests. Keep it concise — a few sentences, not a wall of text. Then cover the three main capabilities:

- **Workflows** — structured, multi-step processes with quality gates. Do a task once with Claude, then turn it into a repeatable workflow. Examples: competitive research, tutorial writing, API audits, monthly reporting.
- **Reviews** — automated code review rules that run against every change. Define what to check for in `.deepreview` configs, then run `/review`. Catches regressions, style issues, doc drift, security problems.
- **DeepSchemas** — file-level contracts that validate structure and requirements at write time. Define once, enforce everywhere.

Mention that these three layers work together: workflows enforce process, schemas enforce file contracts, reviews verify output.

### 3. Review rules (for code projects)

Check if this looks like a code project (e.g., has source files, a `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, a `src/` directory, etc.).

- **If it is a code project**: use `AskUserQuestion` to explain that DeepWork can set up automated review rules for the project — these run every time `/review` is called and catch issues automatically. Ask if they'd like to set up review rules now.
  - If yes: invoke the `/deepwork:configure_reviews` skill.
  - If no: continue to the next step.
- **If it is NOT a code project** (or you can't tell): skip this step.

### 4. Offer to record a workflow

Use `AskUserQuestion` to explain what workflows are in a bit more detail:

> Workflows let you capture a multi-step process and replay it reliably. You do the task once — research, analysis, report writing, whatever it is — and DeepWork turns it into a structured workflow with quality gates. Next time, the agent follows the exact same process.
>
> Would you like to record a workflow now? You'll just do the task like normal, and when you're done we'll turn it into a reusable workflow.

If they say yes, invoke the `/deepwork:record` skill.
If they say no, let them know they can run `/deepwork:record` anytime to get started, and that `/deepwork` is the main entry point for all DeepWork features.
