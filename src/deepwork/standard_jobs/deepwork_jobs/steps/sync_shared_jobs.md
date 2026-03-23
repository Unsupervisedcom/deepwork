# Sync Shared Jobs

## Objective

Install library jobs from the DeepWork shared job library into the project's `.deepwork/jobs/` directory. Supports fetching from the remote GitHub repository or from a local DeepWork repo checkout (useful for maintainers developing new jobs).

## Task

### Step 1: Determine Source

Use the AskUserQuestion tool to ask structured questions about the source:

**Question**: "Where should library jobs be fetched from?"

- **Remote (GitHub)** — Clone from the official DeepWork repository on GitHub. Best for most users.
- **Local path** — Use a local checkout of the DeepWork repository. Best for maintainers testing new jobs before merging.

If the user selects "Local path", ask for the filesystem path to the DeepWork repository root (e.g., `../deepwork` or `/home/user/code/deepwork`).

### Step 2: Obtain Library Jobs

#### Remote Source (GitHub)

1. Create a temporary directory for the sparse checkout:
   ```bash
   TMPDIR=$(mktemp -d)
   ```
2. Perform a sparse checkout of only the `library/jobs/` directory:
   ```bash
   git clone --filter=blob:none --sparse https://github.com/Unsupervisedcom/deepwork.git "$TMPDIR/deepwork"
   cd "$TMPDIR/deepwork"
   git sparse-checkout set library/jobs
   ```
3. Set `LIBRARY_PATH="$TMPDIR/deepwork/library/jobs"`

#### Local Source

1. Validate that the provided path exists and contains `library/jobs/`:
   ```bash
   ls "$LOCAL_PATH/library/jobs/"
   ```
2. If the directory doesn't exist, inform the user and ask for the correct path.
3. Set `LIBRARY_PATH="$LOCAL_PATH/library/jobs"`

### Step 3: Discover Available Jobs

1. List all subdirectories of `$LIBRARY_PATH` that contain a `job.yml` file.
2. For each discovered job, read the `job.yml` and extract:
   - `name`
   - `version`
   - `summary`
3. Check which jobs already exist in the project's `.deepwork/jobs/` directory.
4. Present a table to the user:

   | Job Name | Version | Summary | Status |
   |----------|---------|---------|--------|
   | spec_driven_development | 1.0.0 | Spec-driven development workflow... | New |
   | another_job | 2.1.0 | Description... | Exists (v1.0.0) |

### Step 4: Select Jobs to Install

Use the AskUserQuestion tool to ask structured questions:

**Question**: "Which jobs would you like to install?"

- **All jobs** — Install every job from the library
- **Select specific jobs** — Choose individual jobs to install

If the user selects specific jobs, present the list and let them choose.

For jobs that already exist in the project, ask:

**Question**: "Job `[name]` already exists (v[existing_version]). How should this be handled?"

- **Overwrite** — Replace with the library version (v[new_version])
- **Skip** — Keep the existing version
- **Backup and overwrite** — Back up existing to `.deepwork/jobs/[name].backup/` then install new version

### Step 5: Copy Selected Jobs

For each selected job:

1. Copy the entire job directory (including `job.yml`, `steps/`, and any other files) from `$LIBRARY_PATH/[job_name]/` to `.deepwork/jobs/[job_name]/`.
2. If "Backup and overwrite" was selected, first copy the existing directory to `.deepwork/jobs/[job_name].backup/`.
3. Verify the copy was successful by checking that `job.yml` exists in the destination.

### Step 6: Run DeepWork Sync

Run `deepwork sync` to regenerate skill files for the newly installed jobs:

```bash
deepwork sync
```

Verify the sync completes without errors.

### Step 7: Clean Up

If the remote source was used, remove the temporary directory:

```bash
rm -rf "$TMPDIR"
```

### Step 8: Report Results

Summarize what was done:

- **Installed**: List each newly installed job with name and version
- **Overwritten**: List jobs that were overwritten (with old and new versions)
- **Skipped**: List jobs that were skipped
- **Errors**: Report any issues encountered

## Output

### installed_jobs

A list of `job.yml` file paths for each job that was installed or updated.

**Location**: `.deepwork/jobs/[job_name]/job.yml` for each installed job.

## Quality Criteria

- All installed `job.yml` files are valid YAML with required fields (`name`, `version`, `summary`, `steps`)
- All `instructions_file` paths referenced in each `job.yml` exist in the installed job directory
- Existing job conflicts were handled according to user preference (new install, overwrite with approval, or skip)
- `deepwork sync` was run after installation and completed successfully
