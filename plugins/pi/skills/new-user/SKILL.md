---
name: new-user
description: "Welcome new DeepWork users on Pi and configure MCP access"
disable-model-invocation: true
---

# New User Onboarding

Guide a new user through DeepWork and help them get started on Pi.

## Flow

### 0. Check Dependencies

Check for `uv`:

```bash
command -v uv
```

If `uv` is missing, install it. On macOS, first warn that the installer may trigger harmless permission prompts for folders outside the project and those prompts are safe to deny.

- If `brew` is available: `brew install uv`
- macOS/Linux fallback: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Windows PowerShell: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`

After install, run `command -v uv` and `uv --version`. If `uv` is still unavailable, ask the user to restart their terminal and resume.

### 1. Configure Pi

Run:

```text
/deepwork_setup
```

This writes the DeepWork MCP server to `.mcp.json` and reloads Pi resources.

### 2. Verify MCP

Verify the DeepWork MCP server is reachable. Prefer direct `get_workflows`; otherwise use the `mcp` proxy:

```text
mcp({ search: "get_workflows" })
```

Then call the returned `get_workflows` tool with `{}`. If the server is not reachable, tell the user to run `/deepwork_setup`, then `/reload`, then try `/new-user` again.

### 3. GitHub Star

If `gh` is installed, ask whether the user wants to star the repo. If yes:

```bash
gh api -X PUT /user/starred/Unsupervisedcom/deepwork
```

Skip this entirely if `gh` is unavailable.

### 4. Introduce DeepWork

Print a concise welcome message. Lead with: DeepWork makes AI agents reliable by giving workflows, schemas, and reviews that verify process and output.

Cover:
- **Workflows** - structured, multi-step processes with quality gates
- **Reviews** - `.deepreview` rules run by `/review`
- **DeepSchemas** - file-level contracts enforced at write time and review time

### 5. Review Rules

If this looks like a code project, ask whether the user wants automated review rules. If yes, invoke `configure-reviews`. If no, continue.

### 6. Offer Recording

Ask whether they want to record a workflow now. If yes, invoke `record`. If no, tell them they can run `/record` anytime and `/deepwork` is the main workflow entry point.
