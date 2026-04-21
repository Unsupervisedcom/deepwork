# JOBS-REQ-008: Job Discovery and Standard Jobs

## Overview

DeepWork discovers job definitions from multiple folder sources with a defined priority order. Standard jobs are bundled with the DeepWork package and automatically available at runtime. Project-local jobs take precedence over standard jobs, and additional job folders can be configured via environment variable. This discovery system enables a layered job configuration model.

## Requirements

### JOBS-REQ-008.1: Job Folder Discovery

1. The system MUST provide a `get_job_folders()` function that returns an ordered list of directories to scan for job definitions.
2. The first folder in the list MUST be `{project_root}/.deepwork/jobs/` (project-local jobs).
3. The second folder in the list MUST be the standard jobs directory bundled with the DeepWork package (`src/deepwork/standard_jobs/`).
4. The standard jobs directory MUST be resolved relative to the package installation path, not hardcoded to a development path.
5. Additional folders MAY be appended via the `DEEPWORK_ADDITIONAL_JOBS_FOLDERS` environment variable.
6. The environment variable value MUST be parsed as a colon-delimited list of absolute paths.
7. Empty entries in the colon-delimited list MUST be ignored.
8. Whitespace around entries MUST be stripped.
9. The returned list MAY include non-existent paths; callers MUST handle non-existent paths gracefully.

### JOBS-REQ-008.2: Job Loading

1. `load_all_jobs()` MUST scan each folder from `get_job_folders()` in order.
2. Non-existent or non-directory folders MUST be silently skipped.
3. Within each folder, subdirectories MUST be scanned in sorted order.
4. A subdirectory MUST be considered a job candidate only if it is a directory AND contains a `job.yml` file.
5. When the same job directory name appears in multiple folders, the first folder's version MUST win (project-local overrides standard).
6. Duplicate detection MUST be based on the directory name, not the `name` field inside `job.yml`.
7. Each job candidate MUST be parsed via `parse_job_definition()`.
8. Successfully parsed jobs MUST be added to the results list.
9. Jobs that fail to parse MUST be recorded as `JobLoadError` with `job_name`, `job_dir`, and `error` fields.
10. Failed jobs MUST be logged as warnings.
11. `load_all_jobs()` MUST return a tuple of `(list[JobDefinition], list[JobLoadError])`.

### JOBS-REQ-008.3: Job Directory Lookup

1. `find_job_dir()` MUST search all folders from `get_job_folders()` in priority order.
2. `find_job_dir()` MUST return the first directory matching the job name that is a directory and contains a `job.yml` file.
3. `find_job_dir()` MUST return `None` if no matching job directory is found in any folder.
4. Non-existent or non-directory folders in the search path MUST be silently skipped.

### JOBS-REQ-008.4: Standard Jobs

1. Standard jobs MUST be located in `src/deepwork/standard_jobs/` within the package.
2. Standard jobs MUST be automatically discoverable without any user configuration.
3. The `deepwork_jobs` standard job MUST be bundled with the package.
4. Standard jobs MUST follow the same `job.yml` format and validation rules as any other job (see JOBS-REQ-002).
5. Project-local jobs (in `.deepwork/jobs/`) MUST take precedence over standard jobs with the same directory name.

### JOBS-REQ-008.5: Job Load Error Reporting

1. The `JobLoadError` dataclass MUST contain: `job_name` (str), `job_dir` (str), `error` (str).
2. Load errors MUST be surfaced to callers (e.g., `get_workflows` tool) so agents can see which jobs failed and why.
3. A load error for one job MUST NOT prevent other jobs from loading successfully.
