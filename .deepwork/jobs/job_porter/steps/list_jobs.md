# List Available Jobs

## Objective

Display all DeepWork jobs available in both local and global locations, helping users understand what jobs they have and where they're located.

## Task

Discover and list all jobs from both local and global locations, presenting them in a clear, organized format.

### Step 1: Discover Jobs from Both Locations

Run the sync command with output to see job counts:

```bash
deepwork sync 2>&1 | grep -A3 "Found.*job(s)"
```

This will show you the count of local and global jobs.

### Step 2: List Local Jobs

List all jobs in the local `.deepwork/jobs/` directory:

```bash
if [ -d ".deepwork/jobs" ]; then
  echo "=== LOCAL JOBS (.deepwork/jobs/) ==="
  for job_dir in .deepwork/jobs/*/; do
    if [ -f "${job_dir}job.yml" ]; then
      job_name=$(basename "$job_dir")
      # Extract version from job.yml
      version=$(grep "^version:" "${job_dir}job.yml" | head -1 | cut -d'"' -f2 | tr -d "'")
      # Extract summary
      summary=$(grep "^summary:" "${job_dir}job.yml" | head -1 | cut -d'"' -f2 | tr -d "'")
      echo "  📁 $job_name (v$version)"
      echo "     $summary"
      echo ""
    fi
  done
else
  echo "=== LOCAL JOBS ==="
  echo "  (none)"
  echo ""
fi
```

### Step 3: List Global Jobs

List all jobs in the global `~/.deepwork/jobs/` directory:

```bash
if [ -d "$HOME/.deepwork/jobs" ]; then
  echo "=== GLOBAL JOBS (~/.deepwork/jobs/) ==="
  for job_dir in $HOME/.deepwork/jobs/*/; do
    if [ -f "${job_dir}job.yml" ]; then
      job_name=$(basename "$job_dir")
      # Extract version from job.yml
      version=$(grep "^version:" "${job_dir}job.yml" | head -1 | cut -d'"' -f2 | tr -d "'")
      # Extract summary
      summary=$(grep "^summary:" "${job_dir}job.yml" | head -1 | cut -d'"' -f2 | tr -d "'")
      echo "  🌍 $job_name (v$version)"
      echo "     $summary"
      echo ""
    fi
  done
else
  echo "=== GLOBAL JOBS ==="
  echo "  (none)"
  echo ""
fi
```

### Step 4: Create Summary Output

Save the complete list to `jobs_list.txt`:

```bash
{
  echo "# DeepWork Jobs Inventory"
  echo "Generated: $(date)"
  echo ""
  # Run the above discovery commands
} > jobs_list.txt
```

### Step 5: Provide Guidance

Explain what the user can do next:

1. **Port a job**: Use `/job_porter.port_job` to move a job between local and global
2. **Learn about scopes**: Use `/job_porter.explain_scopes` to understand when to use each scope
3. **Create new jobs**: When creating jobs with `/deepwork_jobs`, you'll be asked to choose the scope

## Quality Criteria

- **Both locations checked**: Listed jobs from both `.deepwork/jobs/` and `~/.deepwork/jobs/`
- **Clear organization**: Jobs are clearly separated by scope (local vs global)
- **Useful metadata**: Each job shows name, version, and summary
- **Visual distinction**: Used emojis or markers to distinguish local (📁) from global (🌍) jobs
- **Output file created**: `jobs_list.txt` contains the complete inventory
- **Next steps provided**: User knows how to port jobs or learn more about scopes
