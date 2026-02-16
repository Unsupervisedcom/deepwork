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

### Step 1.5: Process Jobs in Parallel

**For each job** (except `deepwork_jobs` which should be updated via `deepwork install`), kick off a sub-agent to audit and repair that job's `job.yml` file. The sub-agent should:

1. Read the job's `job.yml` file
2. Check for and fix all issues described in Steps 2-6 below
3. Validate the YAML is still valid after changes
4. Report what was changed

**Run sub-agents in parallel** - one for each job to speed up the process.

**Example prompt for sub-agent:**
```
Be concise. Output minimal text — only report changes made or confirm no changes needed. Do not echo back file contents, do not explain what each migration rule means, and do not narrate your process.

First, read the job.yml JSON Schema at `.deepwork/schemas/job.schema.json` to understand the current valid structure. Use it as the source of truth.

Then audit and repair the job at `.deepwork/jobs/[job_name]/job.yml`:
1. Remove any `exposed: true` fields from steps
2. Migrate `stop_hooks` to `hooks.after_agent` format
3. Remove references to deleted steps (like `review_job_spec`)
4. Fix orphaned steps by adding them to workflows
5. Migrate `outputs` from array format to map format with `type` and `description`
6. Update any `file` inputs that reference renamed output keys
7. Migrate `quality_criteria` arrays to `reviews` format (run_each + map criteria)
8. Remove any `changelog` section (no longer in schema)
9. Replace `description:` with `common_job_info_provided_to_all_steps_at_runtime:` if present
10. Remove any info in `common_job_info_provided_to_all_steps_at_runtime` that is not relevant to most steps.
11. Read the step instructions and remove anything that is repeated in many steps and put it into `common_job_info_provided_to_all_steps_at_runtime`
12. Remove `<promise>Quality Criteria Met</promise>` lines from step instruction .md files
13. Bump version if changes were made
14. Validate YAML syntax

Report only: which checks passed with no changes, and which changes were made (one line each).
```

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

### Step 6: Migrate `outputs` from Array Format to Map Format

The `outputs` field on steps changed from an array of strings/objects to a map with typed entries. Every output must now have a key (identifier), a `type` (`file` or `files`), and a `description`.

**Before (legacy array format):**
```yaml
steps:
  - id: define
    outputs:
      - job.yml
      - steps/
      - file: report.md
        doc_spec: .deepwork/doc_specs/report.md
```

**After (current map format):**
```yaml
steps:
  - id: define
    outputs:
      job.yml:
        type: file
        description: "The job definition file"
      step_instruction_files:
        type: files
        description: "Instruction Markdown files for each step"
      report.md:
        type: file
        description: "The generated report"
```

**Migration rules:**

1. **Plain filename strings** (e.g., `- job.yml`, `- output.md`): Use the filename as the key, set `type: file`, add a `description`.
2. **Directory strings ending in `/`** (e.g., `- steps/`, `- competitor_profiles/`): Choose a descriptive key name (e.g., `step_instruction_files`, `competitor_profiles`), set `type: files`, add a `description`.
3. **Objects with `doc_spec`** (e.g., `- file: report.md` with `doc_spec: ...`): Drop the `doc_spec` field entirely, use the filename as the key, set `type: file`, add a `description`.
4. **`description` is required** on every output entry. Write a short sentence describing what the output contains.

**Update `file` inputs that reference renamed outputs:**

When a directory output key changes (e.g., `steps/` becomes `step_instruction_files`), any downstream step with a `file` input referencing the old name must be updated to use the new key.

```yaml
# Before: input references old directory name
steps:
  - id: implement
    inputs:
      - file: steps/
        from_step: define

# After: input uses the new output key
steps:
  - id: implement
    inputs:
      - file: step_instruction_files
        from_step: define
```

### Step 7: Migrate `quality_criteria` to `reviews`

The flat `quality_criteria` field on steps has been replaced by the `reviews` array. Each review specifies `run_each` (what to review) and `quality_criteria` as a map of criterion name to a statement describing the expected state (not a question).

**Before (deprecated):**
```yaml
steps:
  - id: my_step
    quality_criteria:
      - "**Complete**: The output is complete."
      - "**Accurate**: The data is accurate."
```

**After (current format):**
```yaml
steps:
  - id: my_step
    reviews:
      - run_each: step
        quality_criteria:
          "Complete": "The output is complete."
          "Accurate": "The data is accurate."
```

**Migration rules:**

1. **Parse the old format**: Each string typically follows `**Name**: Question/Statement` format. Extract the name (bold text) as the map key and convert the value to a statement of expected state (not a question).
2. **Choose `run_each`**: Default to `step` (reviews all outputs together). If the step has a single primary output, consider using that output name instead.
3. **For steps with no quality_criteria**: Use `reviews: []`
4. **Remove the old field**: Delete the `quality_criteria` array entirely after migration.

### Step 8: Remove Deprecated `<promise>Quality Criteria Met</promise>` from Step Instructions

Old step instruction templates included a line telling the agent to self-attest quality by emitting a `<promise>` tag. This has been fully replaced by the structured `reviews` system with `QualityGate` evaluation. The old line serves no purpose and should be removed.

**Find and remove lines like these from step instruction `.md` files:**

```markdown
- When all criteria are met, include `<promise>✓ Quality Criteria Met</promise>` in your response
- When all criteria are met, include `<promise>Quality Criteria Met</promise>` in your response
```

**Where to look:** Check every `.md` file in each job's `steps/` directory. The line typically appears as the last bullet in a `## Quality Criteria` section.

**What to do:** Delete the line entirely. Do not replace it with anything — the `reviews` system in `job.yml` now handles quality evaluation.

### Step 9: Update Version Numbers

If you made significant changes to a job, bump its version number:

```yaml
# Bump patch version for minor fixes
version: "1.0.0"  ->  version: "1.0.1"
```

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

### Issue: `outputs` is an array instead of an object
```
Error: Step 'define' outputs should be an object but got array
```
**Fix:** Convert from the legacy array format to the map format. Each array entry becomes a key in the map with `type` (`file` or `files`) and `description`. See Step 6 for detailed migration rules. Also update any `file` inputs in downstream steps if an output key was renamed.

## Jobs to Check

For each job in `.deepwork/jobs/`, check:

| Check | What to Look For |
|-------|------------------|
| `exposed` field | Remove from all steps |
| `stop_hooks` | Migrate to `hooks.after_agent` |
| `outputs` format | Migrate from array to map with `type` and `description` |
| `quality_criteria` | Migrate to `reviews` with `run_each` and map-format criteria |
| `<promise>` in step `.md` files | Remove deprecated `Quality Criteria Met` self-attestation lines |
| Workflow steps | Remove references to deleted steps |
| Dependencies | Update to valid step IDs |
| File inputs | Update `from_step` references; update keys for renamed outputs |
| Version | Bump if changes were made |

## Important Notes

1. **Preserve custom logic** - When migrating hooks, preserve the prompt content
2. **Test after changes** - Validate YAML syntax after each job fix to catch errors early
