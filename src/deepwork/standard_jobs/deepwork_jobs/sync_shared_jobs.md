# Sync Shared Jobs

## Objective

Make DeepWork library jobs available in the project by configuring `DEEPWORK_ADDITIONAL_JOBS_FOLDERS` to reference them in-place. Jobs are **never copied** into `.deepwork/jobs/` — they are referenced from a local checkout or a sparse-checkout clone.

## Important

- **Do NOT copy job directories into `.deepwork/jobs/`.** Library jobs must be referenced via `DEEPWORK_ADDITIONAL_JOBS_FOLDERS` so they stay up-to-date with upstream.
- **Do NOT run `deepwork sync`.** DeepWork is now a Claude Code plugin that auto-discovers jobs at runtime.

## Task

### Step 1: Detect Existing Configuration

Before asking the user anything, check for existing setup:

1. **Check environment variable**:
   ```bash
   echo "${DEEPWORK_ADDITIONAL_JOBS_FOLDERS:-not set}"
   ```

2. **Check flake.nix** (if it exists):
   ```bash
   grep -q 'DEEPWORK_ADDITIONAL_JOBS_FOLDERS' flake.nix && echo "configured" || echo "not configured"
   ```

3. **Check for local deepwork checkout** — look for a sibling directory:
   ```bash
   ls ../deepwork/library/jobs/ 2>/dev/null && echo "local checkout found" || echo "no local checkout"
   ```

4. **Check for existing sparse checkout**:
   ```bash
   ls .deepwork/upstream/library/jobs/ 2>/dev/null && echo "sparse checkout found" || echo "no sparse checkout"
   ```

If the env var is set, validate that each colon-separated path exists and contains at least one `job.yml`:
```bash
IFS=: read -ra FOLDERS <<< "$DEEPWORK_ADDITIONAL_JOBS_FOLDERS"
for folder in "${FOLDERS[@]}"; do
  [ -d "$folder" ] && ls "$folder"/*/job.yml 2>/dev/null | head -1 || echo "INVALID: $folder"
done
```

If a working configuration is already detected (env var set and all paths valid):
1. Report what's configured and list available jobs.
2. Ask if the user wants to reconfigure the source.

### Step 2: Determine Source

Based on detection results, use AskUserQuestion to offer appropriate options.

Valid `source` values are `local`, `remote`, or a custom filesystem path. Map the user-facing choice as follows:

**Question**: "How should library jobs be sourced?"

- `source: local` — **Local checkout** (if `../deepwork/library/jobs/` exists). Point to the existing local DeepWork checkout. Best for maintainers or when a local clone already exists. *(Recommended when detected)*
- `source: remote` — **Sparse checkout**. Clone the DeepWork repo into `.deepwork/upstream/` with sparse checkout for just `library/jobs/`. Best for most users who want live upstream updates.
- `source: <custom-path>` — **Custom local path**. Specify a custom path to a DeepWork repository checkout (the filesystem path is used directly as `source`).

If the user selects "Custom local path", ask for the filesystem path to the DeepWork repository root.

### Step 3: Set Up the Source

#### Local Checkout (e.g., `../deepwork`)

1. Set the local checkout path (for the default `../deepwork` layout, or the custom path provided):
   ```bash
   LOCAL_PATH="../deepwork"
   ```
2. Validate the path contains `library/jobs/`:
   ```bash
   ls "$LOCAL_PATH/library/jobs/"
   ```
3. Resolve the absolute path:
   ```bash
   LIBRARY_PATH=$(cd "$LOCAL_PATH/library/jobs" && pwd)
   ```

#### Sparse Checkout (into `.deepwork/upstream/`)

1. If `.deepwork/upstream/` doesn't exist, create it:
   ```bash
   git clone --no-checkout --filter=blob:none \
     https://github.com/Unsupervisedcom/deepwork.git \
     .deepwork/upstream
   git -C .deepwork/upstream sparse-checkout set --no-cone 'library/jobs/**'
   git -C .deepwork/upstream checkout
   ```
2. If it already exists, update it:
   ```bash
   git -C .deepwork/upstream pull
   ```
3. Ensure `.deepwork/upstream/` is in `.gitignore`.
4. Set `LIBRARY_PATH` from the repository root:
   ```bash
   REPO_ROOT=$(git rev-parse --show-toplevel)
   LIBRARY_PATH="$REPO_ROOT/.deepwork/upstream/library/jobs"
   ```

### Step 4: Configure `DEEPWORK_ADDITIONAL_JOBS_FOLDERS`

The env var must be set so the DeepWork plugin discovers library jobs at runtime.

1. **If `flake.nix` exists**, check whether it already sets `DEEPWORK_ADDITIONAL_JOBS_FOLDERS`:
   - If yes, verify it points to the correct path. Update if needed.
   - If no, add the shellHook export. The recommended pattern prefers a local checkout (e.g. `../deepwork`) when available and falls back to an existing sparse checkout in `.deepwork/upstream/` (without performing network operations in `shellHook`):
     ```nix
     shellHook = ''
       export REPO_ROOT=$(git rev-parse --show-toplevel)

       # Prefer local deepwork checkout, fall back to an existing sparse checkout
       if [ -d "$REPO_ROOT/../deepwork/library/jobs" ]; then
         export DEEPWORK_ADDITIONAL_JOBS_FOLDERS="${DEEPWORK_ADDITIONAL_JOBS_FOLDERS:+$DEEPWORK_ADDITIONAL_JOBS_FOLDERS:}$REPO_ROOT/../deepwork/library/jobs"
       elif [ -d "$REPO_ROOT/.deepwork/upstream/library/jobs" ]; then
         export DEEPWORK_ADDITIONAL_JOBS_FOLDERS="${DEEPWORK_ADDITIONAL_JOBS_FOLDERS:+$DEEPWORK_ADDITIONAL_JOBS_FOLDERS:}$REPO_ROOT/.deepwork/upstream/library/jobs"
       else
         echo "DeepWork library jobs not found. Run '/deepwork shared_jobs' to set them up." >&2
       fi
     '';
     ```

     To initially set up or manually update the sparse checkout, run this **outside of `shellHook`**:
     ```bash
     REPO_ROOT="$(git rev-parse --show-toplevel)"
     if [ ! -d "$REPO_ROOT/.deepwork/upstream" ]; then
       git clone --no-checkout --filter=blob:none \
         https://github.com/Unsupervisedcom/deepwork.git \
         "$REPO_ROOT/.deepwork/upstream"
       git -C "$REPO_ROOT/.deepwork/upstream" sparse-checkout set --no-cone 'library/jobs/**'
       git -C "$REPO_ROOT/.deepwork/upstream" checkout
     else
       git -C "$REPO_ROOT/.deepwork/upstream" pull --ff-only
     fi
     ```

2. **If no `flake.nix`**, inform the user they need to set the env var in their shell:
   ```bash
   export DEEPWORK_ADDITIONAL_JOBS_FOLDERS="/path/to/deepwork/library/jobs"
   ```

3. **For the current session**, append to the variable so jobs are immediately available (preserving any existing paths):
   ```bash
   export DEEPWORK_ADDITIONAL_JOBS_FOLDERS="${DEEPWORK_ADDITIONAL_JOBS_FOLDERS:+$DEEPWORK_ADDITIONAL_JOBS_FOLDERS:}$LIBRARY_PATH"
   ```

### Step 5: Discover and Report Available Jobs

1. List all subdirectories of `$LIBRARY_PATH` that contain a `job.yml` file.
2. For each discovered job, read the `job.yml` and extract `name`, `version`, `summary`.
3. Present a table:

   | Job Name | Version | Summary |
   |----------|---------|---------|
   | platform_engineer | 1.0.0 | Platform engineering workflows... |
   | research | 1.0.0 | Research workflows... |

4. Verify the jobs are discoverable by checking if they appear alongside local jobs.

### Step 6: Clean Up Stale Copies

Check `.deepwork/jobs/` for any previously-copied library jobs that now exist in the referenced library path. If found, inform the user and offer to remove them (they are now redundant since the library reference handles discovery).

### Step 7: Report Results

Summarize:
- **Source configured**: The path and method (local checkout / sparse checkout)
- **Available jobs**: List of jobs now available from the library
- **Configuration location**: Where the env var is set (flake.nix / shell / etc.)
- **Cleaned up**: Any stale copies that were removed

## Output

### available_jobs

A list of `job.yml` file paths for each job available via the configured library path.

**Location**: `$LIBRARY_PATH/[job_name]/job.yml` for each available job.

## Quality Criteria

- Library jobs are referenced via `DEEPWORK_ADDITIONAL_JOBS_FOLDERS`, NOT copied into `.deepwork/jobs/`
- All referenced `job.yml` files are valid YAML with required fields (`name`, `version`, `summary`, `steps`)
- All `instructions_file` paths referenced in each `job.yml` exist
- The env var is configured for persistence (in flake.nix, shellHook, or equivalent)
- No stale copied library jobs remain in `.deepwork/jobs/`
