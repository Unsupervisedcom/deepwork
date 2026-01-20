---
name: New Standard Job Warning
created: src/deepwork/standard_jobs/*/job.yml
compare_to: prompt
---
A new standard job is being created. Standard jobs are bundled with DeepWork and available to all users.

**Before proceeding, verify this is intentional:**

- **Standard jobs** (`src/deepwork/standard_jobs/`) - Ship with DeepWork, available globally
- **Repository jobs** (`.deepwork/jobs/`) - Specific to a single repository
- **Library jobs** - Installed from external packages

Unless the user **explicitly requested** creating a new standard job (not just "a job" or "a new job"), this should likely be a **repository job** in `.deepwork/jobs/` instead.

If uncertain, ask the user: "Should this be a standard job (shipped with DeepWork) or a repository-specific job?"
