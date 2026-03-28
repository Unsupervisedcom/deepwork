# DeepWork - Agent Instructions

This file contains critical instructions for AI agents working on this codebase.

## Project Overview

DeepWork is a framework for enabling AI agents to perform complex, multi-step work tasks across any domain. It is inspired by GitHub's spec-kit but generalized for any job type - from competitive research to ad campaign design to monthly reporting.

**Key Insight**: DeepWork is delivered as a **plugin** for AI agent CLIs (Claude Code, Gemini CLI, etc.). The plugin provides a skill, MCP server configuration, and hooks. The MCP server (`deepwork serve`) is the core runtime — the CLI has no install/sync commands.

## Core Concepts

### Jobs
Jobs are complex, multi-step tasks defined once and executed many times by AI agents. Examples: Feature Development, Competitive Research, Ad Campaign Design, Monthly Sales Reporting, Data-Driven Research.

### Steps
Each job consists of reviewable steps with clear inputs and outputs. For example:
- Competitive Research steps: `identify_competitors` -> `primary_research` -> `secondary_research` -> `report` -> `position`

## Architecture Principles

1. **Job-Agnostic**: Supports any multi-step workflow, not just software development
2. **Git-Native**: All work products are versioned for collaboration and context accumulation
3. **Step-Driven**: Jobs decomposed into reviewable steps with clear inputs/outputs
4. **Plugin-Based**: Delivered as platform plugins (Claude Code plugin, Gemini extension)
5. **AI-Neutral**: Supports multiple AI platforms (Claude Code, Gemini, Copilot, etc.)
6. **Stateless Execution**: All state stored in filesystem artifacts for transparency
7. **MCP-Powered**: The MCP server is the core runtime — no install/sync CLI commands needed

## CRITICAL: Job Type Classification

When creating or modifying jobs in this repository, you MUST understand which type of job you are working with. There are exactly **three types of jobs**, each with a specific location and purpose.

### 1. Standard Jobs (`src/deepwork/standard_jobs/`)

**What they are**: Core jobs that are part of the DeepWork framework itself. These are auto-discovered at runtime by the MCP server and copied to `.deepwork/jobs/` automatically.

**Location**: `src/deepwork/standard_jobs/[job_name]/`

**Current standard jobs**:
- `deepwork_jobs` - Core job management (define, implement, learn)
- `deepwork_reviews` - DeepWork job review and quality control workflows

**Editing rules**:
- Source of truth is ALWAYS in `src/deepwork/standard_jobs/`
- NEVER edit the runtime copies in `.deepwork/jobs/` directly — the MCP server overwrites them at startup

### 2. Library Jobs (`library/jobs/`)

**What they are**: Example or reusable jobs that any repository is welcome to use, but are NOT auto-installed. Users must explicitly copy or import these into their projects.

**Location**: `library/jobs/[job_name]/`

**Examples** (potential):
- Competitive research workflows
- Code review processes
- Documentation generation
- Release management

**Editing rules**:
- Edit directly in `library/jobs/[job_name]/`
- These are templates/examples for users to adopt
- Should be well-documented and self-contained

### 3. Bespoke/Repo Jobs (`.deepwork/jobs/`)

**What they are**: Jobs that are ONLY for this specific repository (the DeepWork repo itself). These are not distributed to users and exist only for internal development workflows.

**Location**: `.deepwork/jobs/[job_name]/` (but NOT if the job also exists in `src/deepwork/standard_jobs/`)

**Identifying bespoke jobs**: A job in `.deepwork/jobs/` is bespoke ONLY if it does NOT have a corresponding directory in `src/deepwork/standard_jobs/`.

**Editing rules**:
- Edit directly in `.deepwork/jobs/[job_name]/`
- These are private to this repository

## IMPORTANT: When Creating New Jobs

Before creating any new job, you MUST determine which type it should be. **If there is any ambiguity**, ask the user a structured question to clarify:

```
Which type of job should this be?
1. Standard Job - Part of the DeepWork framework, auto-installed to all users
2. Library Job - Reusable example that users can optionally adopt
3. Bespoke Job - Only for this repository's internal workflows
```

### Decision Guide

| Question | If Yes → |
|----------|----------|
| Should this ship with DeepWork and be auto-discovered for all users? | Standard Job |
| Is this a reusable pattern that other repos might want to copy? | Library Job |
| Is this only useful for developing DeepWork itself? | Bespoke Job |

## Project Structure

```
deepwork/
├── src/deepwork/
│   ├── cli/              # CLI commands (serve, hook, review, jobs)
│   ├── core/             # Core logic (doc_spec_parser)
│   ├── jobs/             # Job discovery, parsing, schema, and MCP server
│   │   └── mcp/          # MCP server module (the core runtime)
│   ├── hooks/            # Hook scripts and wrappers
│   ├── standard_jobs/    # Built-in job definitions (auto-discovered at runtime)
│   │   ├── deepwork_jobs/
│   │   └── deepwork_reviews/
│   ├── review/           # DeepWork Reviews system (.deepreview pipeline)
│   ├── schemas/          # Definition schemas (deepreview, doc_spec)
│   └── utils/            # Utilities (fs, git, yaml, validation)
├── platform/             # Shared platform-agnostic content
│   └── skill-body.md     # Canonical skill body (source of truth)
├── plugins/
│   ├── claude/           # Claude Code plugin
│   │   ├── .claude-plugin/plugin.json
│   │   ├── README_REVIEWS.md
│   │   ├── example_reviews/
│   │   ├── skills/
│   │   │   ├── deepwork/SKILL.md
│   │   │   └── review/SKILL.md
│   │   ├── hooks/        # hooks.json, post_commit_reminder.sh, post_compact.sh, startup_context.sh
│   │   └── .mcp.json     # MCP server config
│   └── gemini/           # Gemini CLI extension
│       └── skills/deepwork/SKILL.md
├── library/jobs/         # Reusable example jobs
├── tests/                # Test suite
├── doc/                  # Documentation
└── doc/architecture.md   # Detailed architecture document
```

## Technology Stack

- **Language**: Python 3.11+
- **Runtime Dependencies**: PyYAML, Click, jsonschema, FastMCP, Pydantic, aiofiles
- **Dev Dependencies**: Jinja2, GitPython, Rich, pytest, ruff, mypy
- **Distribution**: uv/pipx/brew for Python package management
- **Testing**: pytest with pytest-mock
- **Linting**: ruff
- **Type Checking**: mypy

## Debugging Issues

When debugging issues in this codebase, **always consult `doc/debugging_history/`** first. This directory contains documentation of past debugging sessions, including:

- Root causes of tricky bugs
- Key learnings and patterns to avoid
- Related files and test cases

**After resolving an issue**, append your findings to the appropriate file in `doc/debugging_history/` (or create a new file if none exists for that subsystem). This helps future agents avoid the same pitfalls.

Current debugging history files:
- `doc/debugging_history/hooks.md` - Hooks system debugging (rules_check, blocking, queue management)

## Development Environment

This project uses **Nix Flakes** to provide a reproducible development environment.

### Using the Environment

- **With direnv (Recommended)**: Just `cd` into the directory. The `.envrc` will automatically load the flake environment.
- **Without direnv**: Run `nix develop` to enter the shell.
- **Building**: Run `nix build` to build the package.

**Note**: The flake is configured to automatically allow unfree packages (required for the BSL 1.1 license), so you do not need to set `NIXPKGS_ALLOW_UNFREE=1`.

The environment includes:
- Python 3.11
- uv (package manager)
- All dev dependencies (pytest, ruff, mypy, etc.)

### Package Management

This project uses `uv` for package management:

```bash
uv sync                  # Install dependencies
uv run pytest           # Run tests
```

## How DeepWork Works

### 1. Plugin Installation
Users install the DeepWork plugin for their AI agent CLI:
```
/plugin marketplace add https://github.com/Unsupervisedcom/deepwork
/plugin install deepwork@deepwork-plugins
```
The plugin provides:
- `/deepwork` skill for invoking workflows
- `/review` and `/configure_reviews` skills for automated reviews
- MCP server configuration (`uvx deepwork serve`)
- Hooks for workflow enforcement

### 2. Job Definition
Users define jobs via the `/deepwork` skill. The agent uses MCP tools (`get_workflows` -> `start_workflow` -> `finished_step`) to guide you through defining jobs. Job definitions are stored in `.deepwork/jobs/[job-name]/` and tracked in Git.

### 3. Job Execution
Each step:
- Creates/uses a work branch (`deepwork/[job-name]-[instance]-[date]`)
- Reads inputs from previous steps
- Generates outputs for review
- Suggests next step

### 4. Work Completion
- Review outputs on the work branch
- Commit artifacts as you progress
- Create PR for team review
- Merge to preserve work products for future context

## Editing Standard Jobs

**Standard jobs** (like `deepwork_jobs`) are bundled with DeepWork and discovered at runtime from the Python package. They exist in TWO locations:

1. **Source of truth**: `src/deepwork/standard_jobs/[job_name]/` - The canonical source files
2. **Runtime copy**: `.deepwork/jobs/[job_name]/` - Copied at runtime by the MCP server

**Edit the source files** in `src/deepwork/standard_jobs/[job_name]/`:
- `job.yml` - Job definition with inline step instructions, workflows, and step_arguments

### How to Identify Job Types

- **Standard jobs**: Exist in `src/deepwork/standard_jobs/` (currently: `deepwork_jobs`, `deepwork_reviews`)
- **Library jobs**: Exist in `library/jobs/`
- **Bespoke jobs**: Exist ONLY in `.deepwork/jobs/` with no corresponding standard_jobs entry

**When creating a new job, always clarify which type it should be.** If uncertain, ask the user.

## Key Files to Reference

- `doc/architecture.md` - Comprehensive architecture documentation
- `README.md` - High-level project overview
- `doc/reference/calling_claude_in_print_mode.md` - Correct flag ordering, structured output with JSON schemas, and common gotchas when invoking Claude Code as a subprocess

## Development Guidelines

1. **Read Before Modifying**: Always read existing code before suggesting changes
2. **Security**: Avoid XSS, SQL injection, command injection, and OWASP top 10 vulnerabilities
3. **Simplicity**: Do not over-engineer; make only requested changes
4. **Testing**: Write tests for new functionality
5. **Type Safety**: Use type hints for better code quality
6. **No Auto-Commit**: DO NOT automatically commit changes to git. Let the user review and commit changes themselves.
7. **Documentation Sync**: When making implementation changes, always update `doc/architecture.md` and `README.md` to reflect those changes. The architecture document must stay in sync with the actual codebase.
8. **Succinctness**: Jobs, documentation, and code MUST be succinct. Avoid verbose preambles, redundant explanations, and duplicated content. Step instructions should contain only what the agent needs to act — not philosophy, not quality criteria already enforced by the workflow runtime, and not domain tables already in `common_job_info`. If it can be said in one sentence, do not use three.
