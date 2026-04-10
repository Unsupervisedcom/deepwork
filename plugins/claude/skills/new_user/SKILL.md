---
name: new_user
description: "Welcome new users to DeepWork — introduce features, set up reviews, and optionally record a first workflow"
disable-model-invocation: true
---

# New User Onboarding

Guide a new user through what DeepWork can do and help them get started.

## Flow

### 0. Run setup

Before anything else, run the setup command to ensure the user's environment is configured:

```bash
uvx deepwork setup
```

This configures Claude Code settings (marketplace, plugin, MCP permissions, auto-update). Proceed regardless of the output.

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
