---
name: Standard Jobs Source of Truth
trigger:
  - .deepwork/jobs/deepwork_jobs/**/*
safety:
  - src/deepwork/standard_jobs/deepwork_jobs/**/*
compare_to: base
---
You modified files in `.deepwork/jobs/deepwork_jobs/`.

**These are installed copies, NOT the source of truth!**

Standard jobs (deepwork_jobs) must be edited in their source location:
- Source: `src/deepwork/standard_jobs/[job_name]/`
- Installed copy: `.deepwork/jobs/[job_name]/` (DO NOT edit directly)

**Required action:**
1. Revert your changes to `.deepwork/jobs/deepwork_*/`
2. Make the same changes in `src/deepwork/standard_jobs/[job_name]/`
3. Run `deepwork install --platform claude` to sync changes
4. Verify the changes propagated correctly

See CLAUDE.md section "CRITICAL: Editing Standard Jobs" for details.
