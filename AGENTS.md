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

### 2. Library Jobs (`library/jobs/`)

**What they are**: Example or reusable jobs that any repository is welcome to use, but are NOT auto-installed. Users must explicitly copy or import these into their projects. Some library jobs may be symlinks to bespoke jobs that serve as good examples.

**Location**: `library/jobs/[job_name]/`

**Examples**:
- `commit` - Lint, test, and commit workflow (symlink to `.deepwork/jobs/commit`)

**Editing rules**:
- If the job is a symlink, edit the source in `.deepwork/jobs/[job_name]/`
- If the job is a standalone directory, edit directly in `library/jobs/[job_name]/`
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
├── library/                        # Library of examples
│   ├── jobs/                       # Library jobs (may be symlinks)
│   │   ├── commit -> ../../.deepwork/jobs/commit
│   │   └── README.md
│   └── rules/                      # Library rules (may be symlinks)
│       └── json_validation -> ../../.deepwork/rules/json_validation
└── .deepwork/                      # Repo-specific configuration
    ├── jobs/                       # Installed standard jobs + bespoke jobs
    │   ├── deepwork_jobs/          # ← Installed copy, NOT source of truth
    │   ├── deepwork_rules/         # ← Installed copy, NOT source of truth
    │   └── commit/                 # ← Bespoke job (also exposed in library/)
    └── rules/                      # Repo-specific rules
        └── json_validation/        # ← Bespoke rule (also exposed in library/)
```
