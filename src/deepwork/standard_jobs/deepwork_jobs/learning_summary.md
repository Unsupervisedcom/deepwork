# Learning Summary

## Job Analyzed
- Job: deepwork_jobs
- Work performed: Added make_new_job.sh script and templates directory

## Generalizable Improvements Made
- **implement.md**: Added Step 1 using `make_new_job.sh` script to create directory structure
- **implement.md**: Added list of available templates for reference
- **implement.md**: Replaced inline step instruction example with template reference
- **implement.md**: Replaced inline implementation summary with template reference
- **define.md**: Replaced inline job.yml example with template references
- **learn.md**: Replaced inline AGENTS.md structure with template reference
- **learn.md**: Replaced inline learning_summary format with template reference

## Templates Created
- `job.yml.template` - Job specification structure
- `step_instruction.md.template` - Step instruction file structure
- `implementation_summary.md.template` - Implementation summary format
- `learning_summary.md.template` - Learning summary format
- `agents.md.template` - AGENTS.md file structure
- `example_job.yml` - Complete job specification example
- `example_step_instruction.md` - Complete step instruction example

## Bespoke Learnings Captured
- Location: `src/deepwork/standard_jobs/deepwork_jobs/AGENTS.md`
- Entries added:
  - Dual location maintenance (source of truth vs working copy)
  - File organization structure
  - Version management guidelines
  - Copy commands for syncing locations

## Files Modified
- `src/deepwork/standard_jobs/deepwork_jobs/make_new_job.sh` (created)
- `src/deepwork/standard_jobs/deepwork_jobs/job.yml` (version bump to 0.3.0)
- `src/deepwork/standard_jobs/deepwork_jobs/steps/implement.md` (updated)
- `src/deepwork/standard_jobs/deepwork_jobs/steps/define.md` (updated)
- `src/deepwork/standard_jobs/deepwork_jobs/steps/learn.md` (updated)
- `src/deepwork/standard_jobs/deepwork_jobs/templates/*` (created, 7 files)
- `src/deepwork/standard_jobs/deepwork_jobs/AGENTS.md` (created)
- `.deepwork/jobs/deepwork_jobs/*` (synced copies)

## Recommendations
- Consider adding a `sync_standard_jobs.sh` script to automate copying from source to working directory
- The templates directory could be referenced by the make_new_job.sh script to optionally copy templates to new jobs
