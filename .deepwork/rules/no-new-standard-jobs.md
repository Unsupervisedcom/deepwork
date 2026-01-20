---
name: No New Standard Jobs
trigger: src/deepwork/standard_jobs/*/job.yml
safety:
  - src/deepwork/standard_jobs/deepwork_jobs/**/*
  - src/deepwork/standard_jobs/deepwork_rules/**/*
compare_to: prompt
---
A new folder is being created in `src/deepwork/standard_jobs/`.

**STOP: Standard jobs should rarely be created.**

Standard jobs are installed globally via `deepwork install` and ship with the tool itself. Most jobs should be:

1. **Repository jobs** (`/.deepwork/jobs/`) - Specific to this repository, committed with the codebase
2. **Library jobs** - Reusable jobs shared across projects via a library mechanism

Only create a standard job if the user has **explicitly and clearly stated** that:
- This should be a standard job that ships with deepwork itself
- This is intended for global installation across all projects
- They understand the difference between standard, repository, and library jobs

If the user did not explicitly request a standard job, ask them to clarify whether they want:
- A **repository job** (most common) - stored in `.deepwork/jobs/` for this repo only
- A **library job** - reusable across projects
- A **standard job** - only for core deepwork functionality

Please confirm the user's intent before proceeding.
