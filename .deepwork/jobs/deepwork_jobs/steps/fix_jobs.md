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

Steps not included in any workflow cannot be invoked via the MCP interface. The parser will emit warnings for these.

Run the following to see warnings:
```bash
deepwork sync 2>&1 | grep -i "warning"
```

**For each orphaned step, ask the user which action to take:**

1. **Add to a workflow** - Create a new single-step workflow for it:
   ```yaml
   workflows:
     - name: standalone_step_name
       summary: "Runs the step_name step"
       steps:
         - step_name
   ```

2. **Remove the step entirely** - Delete the step from `steps:` array and its instruction file

3. **Keep as-is (deprecated)** - The step will remain inaccessible but preserved in the job definition

**Do not automatically decide** - Always confirm with the user which option they prefer for each orphaned step.

### Step 6: Validate Against Schema

After making changes, validate each job.yml:

```bash
deepwork sync
```

Fix any schema validation errors that appear.

### Step 7: Update Version Numbers

If you made significant changes to a job, bump its version number:

```yaml
# Bump patch version for minor fixes
version: "1.0.0"  ->  version: "1.0.1"

# Add changelog entry
changelog:
  - version: "1.0.1"
    changes: "Migrated to current DeepWork format; removed deprecated fields"
```

### Step 8: Run Sync

After all fixes, regenerate commands:

```bash
deepwork sync
```

Verify no errors or warnings appear.

## Quality Criteria

- All `exposed: true` fields are removed or noted
- All `stop_hooks` are migrated to `hooks.after_agent` format
- References to removed steps (like `review_job_spec`) are updated
- Orphaned steps are either added to workflows or removed
- All job.yml files pass schema validation
- `deepwork sync` runs without errors
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
**Fix:** Either add the step to a workflow or remove it from the job.

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
3. **Test after changes** - Run `deepwork sync` after each job fix to catch errors early
