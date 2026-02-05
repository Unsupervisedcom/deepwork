# Fix Job Definitions

## Objective

Update all job.yml files and step instructions in `.deepwork/jobs/` to the current DeepWork format. This step migrates deprecated fields, removes references to deleted steps, and ensures all jobs are compatible with the MCP-based workflow system.

## Task

Audit and repair all job definitions, migrating from legacy formats to current specifications.

### Step 1: Inventory All Jobs

List all jobs in the project:

```bash
ls -la .deepwork/jobs/
```

For each job directory, you'll need to check and potentially fix the `job.yml` file.

### Step 2: Remove `exposed` Field

The `exposed` field on steps no longer has any effect in MCP-based DeepWork. Steps are now only accessible through workflows.

**Find and remove:**
```yaml
steps:
  - id: some_step
    exposed: true  # REMOVE THIS LINE
```

If a step was `exposed: true` and is not in any workflow, it should either:
1. Be added to a workflow, OR
2. Be removed from the job entirely

### Step 3: Migrate `stop_hooks` to `hooks.after_agent`

The `stop_hooks` field is deprecated. Migrate to the new `hooks` structure:

**Before (deprecated):**
```yaml
steps:
  - id: my_step
    stop_hooks:
      - prompt: "Verify the output meets quality standards"
```

**After (current format):**
```yaml
steps:
  - id: my_step
    hooks:
      after_agent:
        - prompt: "Verify the output meets quality standards"
```

### Step 4: Remove References to Deleted Steps

Check for references to steps that no longer exist in the standard jobs:

**Steps that have been removed:**
- `review_job_spec` - Was removed from `deepwork_jobs` in v1.0.1

**What to fix:**
- Remove from workflow `steps` arrays
- Update `from_step` references in inputs
- Update `dependencies` arrays

**Example fix:**
```yaml
# Before
workflows:
  - name: new_job
    steps:
      - define
      - review_job_spec  # REMOVE
      - implement

steps:
  - id: implement
    inputs:
      - file: job.yml
        from_step: review_job_spec  # CHANGE TO: define
    dependencies:
      - review_job_spec  # CHANGE TO: define
```

### Step 5: Fix Orphaned Steps

Steps not included in any workflow cannot be invoked via the MCP interface.

**How to handle orphaned steps depends on whether the job has ANY workflows defined:**

#### Case A: Job has NO workflows defined

If the job has no `workflows:` section at all (or it's empty), create a **single workflow with the same name as the job** containing all steps in their defined order:

```yaml
# For a job named "my_job" with steps: step_a, step_b, step_c
workflows:
  - name: my_job  # Same name as the job
    summary: "Runs the complete my_job workflow"
    steps:
      - step_a
      - step_b
      - step_c
```

This preserves the original intent of the job as a sequential workflow.

#### Case B: Job has SOME workflows defined

If the job already has one or more workflows defined, but some steps are not included in any of them, create a **separate single-step workflow for each orphaned step** with the same name as the step:

```yaml
# Existing workflows stay as-is, add new ones for orphans
workflows:
  - name: existing_workflow
    summary: "..."
    steps: [...]

  # Add for each orphaned step:
  - name: orphaned_step_name  # Same name as the step
    summary: "Runs the orphaned_step_name step"
    steps:
      - orphaned_step_name
```

This ensures all steps remain accessible via the MCP interface while preserving the existing workflow structure.

### Step 6: Update Version Numbers

If you made significant changes to a job, bump its version number:

```yaml
# Bump patch version for minor fixes
version: "1.0.0"  ->  version: "1.0.1"

# Add changelog entry
changelog:
  - version: "1.0.1"
    changes: "Migrated to current DeepWork format; removed deprecated fields"
```

## Quality Criteria

- All `exposed: true` fields are removed or noted
- All `stop_hooks` are migrated to `hooks.after_agent` format
- References to removed steps (like `review_job_spec`) are updated
- Jobs with no workflows get a single workflow (same name as job) containing all steps
- Jobs with existing workflows get individual workflows for each orphaned step (same name as step)
- All job.yml files are valid YAML
- When all criteria are met, include `<promise>Quality Criteria Met</promise>` in your response

## Common Issues and Fixes

### Issue: Step references non-existent step in `from_step`
```
Error: Step 'implement' has file input from 'review_job_spec' but 'review_job_spec' is not in dependencies
```
**Fix:** Update `from_step` to reference a step that still exists.

### Issue: Workflow references non-existent step
```
Error: Workflow 'new_job' references non-existent step 'review_job_spec'
```
**Fix:** Remove the step from the workflow's `steps` array.

### Issue: Orphaned step warning
```
Warning: Job 'my_job' has steps not included in any workflow: standalone_step
```
**Fix:**
- If the job has NO workflows: Create one workflow named `my_job` with all steps in order
- If the job has SOME workflows: Add a `standalone_step` workflow containing just that step

## Jobs to Check

For each job in `.deepwork/jobs/`, check:

| Check | What to Look For |
|-------|------------------|
| `exposed` field | Remove from all steps |
| `stop_hooks` | Migrate to `hooks.after_agent` |
| Workflow steps | Remove references to deleted steps |
| Dependencies | Update to valid step IDs |
| File inputs | Update `from_step` references |
| Version | Bump if changes were made |

## Important Notes

1. **Don't modify standard jobs directly** - If `deepwork_jobs` is out of date, run `deepwork install --platform claude` to get the latest version
2. **Preserve custom logic** - When migrating hooks, preserve the prompt content
3. **Test after changes** - Validate YAML syntax after each job fix to catch errors early
