# DeepWork - Agent Instructions

This file contains critical instructions for AI agents working on this codebase.

## CRITICAL: Job Type Classification

When creating or modifying jobs in this repository, you MUST understand which type of job you are working with. There are exactly **three types of jobs**, each with a specific location and purpose.

### 1. Standard Jobs (`src/deepwork/standard_jobs/`)

**What they are**: Core jobs that are part of the DeepWork framework itself. These get automatically installed to every target repository when users run `deepwork install`.

**Location**: `src/deepwork/standard_jobs/[job_name]/`

**Current standard jobs**:
- `deepwork_jobs` - Core job management (define, implement, learn)
- `deepwork_rules` - Rules enforcement system

**Editing rules**:
- Source of truth is ALWAYS in `src/deepwork/standard_jobs/`
- NEVER edit the installed copies in `.deepwork/jobs/` directly
- After editing, run `deepwork install --platform claude` to sync

### 2. Library Jobs (`jobs/library/`)

**What they are**: Example or reusable jobs that any repository is welcome to use, but are NOT auto-installed. Users must explicitly copy or import these into their projects.

**Location**: `jobs/library/[job_name]/`

**Examples** (potential):
- Competitive research workflows
- Code review processes
- Documentation generation
- Release management

**Editing rules**:
- Edit directly in `jobs/library/[job_name]/`
- These are templates/examples for users to adopt
- Should be well-documented and self-contained

### 3. Bespoke/Repo Jobs (`.deepwork/jobs/`)

**What they are**: Jobs that are ONLY for this specific repository (the DeepWork repo itself). These are not distributed to users and exist only for internal development workflows.

**Location**: `.deepwork/jobs/[job_name]/` (but NOT if the job also exists in `src/deepwork/standard_jobs/`)

**Identifying bespoke jobs**: A job in `.deepwork/jobs/` is bespoke ONLY if it does NOT have a corresponding directory in `src/deepwork/standard_jobs/`.

**Editing rules**:
- Edit directly in `.deepwork/jobs/[job_name]/`
- These are private to this repository
- Run `deepwork sync` after changes to regenerate skills

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
| Should this be installed automatically when users run `deepwork install`? | Standard Job |
| Is this a reusable pattern that other repos might want to copy? | Library Job |
| Is this only useful for developing DeepWork itself? | Bespoke Job |

## File Structure Summary

```
deepwork/
├── src/deepwork/standard_jobs/    # Standard jobs (source of truth)
│   ├── deepwork_jobs/
│   └── deepwork_rules/
├── jobs/library/                   # Library/example jobs
│   └── [example_job]/
└── .deepwork/jobs/                 # Installed standard jobs + bespoke jobs
    ├── deepwork_jobs/              # ← Installed copy, NOT source of truth
    ├── deepwork_rules/             # ← Installed copy, NOT source of truth
    └── [bespoke_job]/              # ← Source of truth for bespoke only

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

```
