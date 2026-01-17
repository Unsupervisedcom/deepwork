# DeepWork - Project Context for Claude Code

## Project Overview

DeepWork is a framework for enabling AI agents to perform complex, multi-step work tasks across any domain. It is inspired by GitHub's spec-kit but generalized for any job type - from competitive research to ad campaign design to monthly reporting.

**Key Insight**: DeepWork is an *installation tool* that sets up job-based workflows in your project. After installation, all work is done through your chosen AI agent CLI (like Claude Code) using slash commands. The DeepWork CLI itself is only used for initial setup.

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
- Each step becomes a slash command: `/competitive_research.identify_competitors`

## Architecture Principles

1. **Job-Agnostic**: Supports any multi-step workflow, not just software development
2. **Git-Native**: All work products are versioned for collaboration and context accumulation
3. **Step-Driven**: Jobs decomposed into reviewable steps with clear inputs/outputs
4. **Template-Based**: Job definitions are reusable and shareable via Git
5. **AI-Neutral**: Supports multiple AI platforms (Claude Code, Gemini, Copilot, etc.)
6. **Stateless Execution**: All state stored in filesystem artifacts for transparency
7. **Installation-Only CLI**: DeepWork installs skills/commands then gets out of the way

## Project Structure

```
deepwork/
├── src/deepwork/
│   ├── cli/              # CLI commands (install, sync)
│   ├── core/             # Core logic (detection, generation, parsing)
│   ├── templates/        # Command templates per AI platform
│   │   ├── claude/
│   │   ├── gemini/
│   │   └── copilot/
│   ├── standard_jobs/    # Built-in job definitions
│   │   └── deepwork_jobs/
│   ├── schemas/          # Job definition schemas
│   └── utils/            # Utilities (fs, git, yaml, validation)
├── tests/                # Test suite
├── doc/                  # Documentation
└── doc/architecture.md   # Detailed architecture document
```

## Technology Stack

- **Language**: Python 3.11+
- **Dependencies**: Jinja2 (templates), PyYAML (config), GitPython (git ops)
- **Distribution**: uv/pipx for modern Python package management
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

## Running DeepWork CLI (Claude Code Web Environment)

When running in Claude Code on the web (not local installations), the `deepwork` CLI may not be available. To run DeepWork commands:

```bash
# Install the package in editable mode (one-time setup)
pip install -e .

# Then run commands normally
deepwork install --platform claude
deepwork sync
```

**Note**: In web environments, you may also need to install dependencies like `jsonschema`, `pyyaml`, `gitpython`, `jinja2`, and `click` if they're not already available.

## How DeepWork Works

### 1. Installation
Users install DeepWork globally, then run it in a Git project:
```bash
cd my-project/
deepwork install --claude
```

This installs core commands into `.claude/commands/`:
- `deepwork_jobs.define` - Interactive job definition wizard
- `deepwork_jobs.implement` - Generates step files and syncs commands
- `deepwork_jobs.refine` - Refine existing job definitions

### 2. Job Definition
Users define jobs via Claude Code:
```
/deepwork_jobs.define
```

The agent guides you through defining:
- Job name and description
- Steps with inputs/outputs
- Dependencies between steps

This creates the `job.yml` file. Then run:
```
/deepwork_jobs.implement
```

This generates step instruction files and syncs commands to `.claude/commands/`.

Job definitions are stored in `.deepwork/jobs/[job-name]/` and tracked in Git.

### 3. Job Execution
Execute jobs via slash commands in Claude Code:
```
/competitive_research.identify_competitors
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

## Target Project Structure (After Installation)

```
my-project/
├── .git/
├── .claude/                    # Claude Code directory
│   └── commands/               # Command files
│       ├── deepwork_jobs.define.md
│       ├── deepwork_jobs.implement.md
│       ├── deepwork_jobs.refine.md
│       └── [job].[step].md
└── .deepwork/                  # DeepWork configuration
    ├── config.yml              # version, platforms[]
    └── jobs/
        ├── deepwork_jobs/      # Built-in job
        │   ├── job.yml
        │   └── steps/
        └── [job-name]/
            ├── job.yml
            └── steps/
                └── [step].md
```

**Note**: Work outputs are created on dedicated Git branches (e.g., `deepwork/job_name-instance-date`), not in a separate directory.


## Key Files to Reference

- `doc/architecture.md` - Comprehensive architecture documentation
- `README.md` - High-level project overview
- `shell.nix` - Development environment setup

## Development Guidelines

1. **Read Before Modifying**: Always read existing code before suggesting changes
2. **Security**: Avoid XSS, SQL injection, command injection, and OWASP top 10 vulnerabilities
3. **Simplicity**: Don't over-engineer; make only requested changes
4. **Testing**: Write tests for new functionality
5. **Type Safety**: Use type hints for better code quality
6. **No Auto-Commit**: DO NOT automatically commit changes to git. Let the user review and commit changes themselves.
7. **Documentation Sync**: CRITICAL - When making implementation changes, always update `doc/architecture.md` and `README.md` to reflect those changes. The architecture document must stay in sync with the actual codebase (terminology, file paths, structure, behavior, etc.).

## CRITICAL: Editing Standard Jobs

**Standard jobs** (like `deepwork_jobs` and `deepwork_rules`) are bundled with DeepWork and installed to user projects. They exist in THREE locations:

1. **Source of truth**: `src/deepwork/standard_jobs/[job_name]/` - The canonical source files
2. **Installed copy**: `.deepwork/jobs/[job_name]/` - Installed by `deepwork install`
3. **Generated commands**: `.claude/commands/[job_name].[step].md` - Generated from installed jobs

### Editing Workflow for Standard Jobs

**NEVER edit files in `.deepwork/jobs/` or `.claude/commands/` for standard jobs directly!**

Instead, follow this workflow:

1. **Edit the source files** in `src/deepwork/standard_jobs/[job_name]/`
   - `job.yml` - Job definition with steps, stop_hooks, etc.
   - `steps/*.md` - Step instruction files
   - `hooks/*` - Any hook scripts

2. **Run `deepwork install --platform claude`** to sync changes to `.deepwork/jobs/` and `.claude/commands/`

3. **Verify** the changes propagated correctly to all locations

### How to Identify Standard Jobs

Standard jobs are defined in `src/deepwork/standard_jobs/`. Currently:
- `deepwork_jobs` - Core job management commands (define, implement, refine)
- `deepwork_rules` - Rules enforcement system

If a job exists in `src/deepwork/standard_jobs/`, it is a standard job and MUST be edited there.

## Success Metrics

1. **Usability**: Users can define and execute new jobs in <30 minutes
2. **Reliability**: 99%+ of steps execute successfully on first try
3. **Performance**: Job import completes in <10 seconds
4. **Extensibility**: New AI platforms can be added in <2 days
5. **Quality**: 90%+ test coverage, zero critical bugs
