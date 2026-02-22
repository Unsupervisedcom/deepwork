# DeepWork - Project Context for Claude Code

## Project Overview

DeepWork is a framework for enabling AI agents to perform complex, multi-step work tasks across any domain. It is inspired by GitHub's spec-kit but generalized for any job type - from competitive research to ad campaign design to monthly reporting.

**Key Insight**: DeepWork is delivered as a **plugin** for AI agent CLIs (Claude Code, Gemini CLI, etc.). The plugin provides a skill, MCP server configuration, and hooks. The MCP server (`deepwork serve`) is the core runtime — the CLI has no install/sync commands.

## Core Concepts

### Jobs
Jobs are complex, multi-step tasks defined once and executed many times by AI agents. Examples:
- Feature Development
- Competitive Research
- Ad Campaign Design
- Monthly Sales Reporting
- Data-Driven Research

### Steps
Each job consists of reviewable steps with clear inputs and outputs. For example:
- Competitive Research steps: `identify_competitors` → `primary_research` → `secondary_research` → `report` → `position`

## Architecture Principles

1. **Job-Agnostic**: Supports any multi-step workflow, not just software development
2. **Git-Native**: All work products are versioned for collaboration and context accumulation
3. **Step-Driven**: Jobs decomposed into reviewable steps with clear inputs/outputs
4. **Plugin-Based**: Delivered as platform plugins (Claude Code plugin, Gemini extension)
5. **AI-Neutral**: Supports multiple AI platforms (Claude Code, Gemini, Copilot, etc.)
6. **Stateless Execution**: All state stored in filesystem artifacts for transparency
7. **MCP-Powered**: The MCP server is the core runtime — no install/sync CLI commands needed

## Project Structure

```
deepwork/
├── src/deepwork/
│   ├── cli/              # CLI commands (serve, hook)
│   ├── core/             # Core logic (parsing, jobs, doc_spec_parser)
│   ├── mcp/              # MCP server (the core runtime)
│   ├── hooks/            # Hook scripts and wrappers
│   ├── standard_jobs/    # Built-in job definitions (auto-discovered at runtime)
│   │   └── deepwork_jobs/
│   ├── schemas/          # Job definition schemas
│   └── utils/            # Utilities (fs, git, yaml, validation)
├── platform/             # Shared platform-agnostic content
│   └── skill-body.md     # Canonical skill body (source of truth)
├── plugins/
│   ├── claude/           # Claude Code plugin
│   │   ├── .claude-plugin/plugin.json
│   │   ├── skills/deepwork/SKILL.md
│   │   ├── hooks/        # hooks.json
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

## Development Environment

This project uses Nix for reproducible development environments:

```bash
# Enter development environment
nix-shell

# Inside nix-shell, use uv for package management
uv sync                  # Install dependencies
uv run pytest           # Run tests
```

## How DeepWork Works

### 1. Plugin Installation
Users install the DeepWork plugin for their AI agent CLI:

**Claude Code:**
```
/plugin marketplace add https://github.com/Unsupervisedcom/deepwork
/plugin install deepwork@deepwork-plugins
```

The plugin provides:
- `/deepwork` skill for invoking workflows
- MCP server configuration (`uvx deepwork serve`)
- SessionStart hook for version checking

### 2. Job Definition
Users define jobs via the `/deepwork` skill:
```
/deepwork Make a job for doing competitive research
```

The agent uses MCP tools (`get_workflows` → `start_workflow` → `finished_step`) to guide you through defining jobs. Job definitions are stored in `.deepwork/jobs/[job-name]/` and tracked in Git.

### 3. Job Execution
Execute jobs via the `/deepwork` skill:
```
/deepwork competitive_research
```

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

## Target Project Structure (After Plugin Install)

```
my-project/
├── .git/
└── .deepwork/                  # DeepWork runtime data
    ├── tmp/                    # Session state (created lazily)
    └── jobs/
        ├── deepwork_jobs/      # Built-in job (auto-discovered from package)
        │   ├── job.yml
        │   └── steps/
        └── [job-name]/
            ├── job.yml
            └── steps/
                └── [step].md
```

**Note**: The plugin provides the skill and MCP config. Work outputs are created on dedicated Git branches (e.g., `deepwork/job_name-instance-date`), not in a separate directory.


## Key Files to Reference

- `doc/architecture.md` - Comprehensive architecture documentation
- `README.md` - High-level project overview
- `shell.nix` - Development environment setup
- `doc/reference/calling_claude_in_print_mode.md` - When invoking Claude Code as a subprocess (e.g., with `--print` or `-p`), read this for correct flag ordering, structured output with JSON schemas, and common gotchas

## Development Guidelines

1. **Read Before Modifying**: Always read existing code before suggesting changes
2. **Security**: Avoid XSS, SQL injection, command injection, and OWASP top 10 vulnerabilities
3. **Simplicity**: Don't over-engineer; make only requested changes
4. **Testing**: Write tests for new functionality
5. **Type Safety**: Use type hints for better code quality
6. **No Auto-Commit**: DO NOT automatically commit changes to git. Let the user review and commit changes themselves.
7. **Documentation Sync**: CRITICAL - When making implementation changes, always update `doc/architecture.md` and `README.md` to reflect those changes. The architecture document must stay in sync with the actual codebase (terminology, file paths, structure, behavior, etc.).

## CRITICAL: Job Types and Where to Edit

**See `AGENTS.md` for the complete job classification guide.** This repository has THREE types of jobs:

| Type | Location | Purpose |
|------|----------|---------|
| **Standard Jobs** | `src/deepwork/standard_jobs/` | Framework core, auto-discovered at runtime |
| **Library Jobs** | `library/jobs/` | Reusable examples users can adopt |
| **Bespoke Jobs** | `.deepwork/jobs/` (if not in standard_jobs) | This repo's internal workflows only |

### Editing Standard Jobs

**Standard jobs** (like `deepwork_jobs`) are bundled with DeepWork and discovered at runtime from the Python package. They exist in TWO locations:

1. **Source of truth**: `src/deepwork/standard_jobs/[job_name]/` - The canonical source files
2. **Runtime copy**: `.deepwork/jobs/[job_name]/` - Copied at runtime by the MCP server

**Edit the source files** in `src/deepwork/standard_jobs/[job_name]/`:
- `job.yml` - Job definition with steps, hooks, etc.
- `steps/*.md` - Step instruction files
- `hooks/*` - Any hook scripts

### How to Identify Job Types

- **Standard jobs**: Exist in `src/deepwork/standard_jobs/` (currently: `deepwork_jobs`)
- **Library jobs**: Exist in `library/jobs/`
- **Bespoke jobs**: Exist ONLY in `.deepwork/jobs/` with no corresponding standard_jobs entry

**When creating a new job, always clarify which type it should be.** If uncertain, ask the user.

## Success Metrics

1. **Usability**: Users can define and execute new jobs in <30 minutes
2. **Reliability**: 99%+ of steps execute successfully on first try
3. **Performance**: Job import completes in <10 seconds
4. **Extensibility**: New AI platforms can be added in <2 days
5. **Quality**: 90%+ test coverage, zero critical bugs
