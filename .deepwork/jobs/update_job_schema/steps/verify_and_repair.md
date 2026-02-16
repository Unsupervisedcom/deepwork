# Verify and Update Repair Workflow

## Objective

Update the `deepwork_jobs` repair workflow to handle migration for the schema change (if needed), then verify the entire system works by restarting the MCP server and calling `get_workflows` to confirm all jobs parse successfully.

## Task

This is the final verification step. It ensures that: (1) existing user installations can be migrated to the new schema via the repair workflow, and (2) the full system works end-to-end after all changes.

### Process

1. **Read the change summary** and determine if the change is breaking (requires migration) or non-breaking (optional fields only)

2. **Update the repair workflow** (if migration needed)
   - Read the repair workflow step files:
     - `src/deepwork/standard_jobs/deepwork_jobs/steps/fix_jobs.md` — fixes job.yml files
     - `src/deepwork/standard_jobs/deepwork_jobs/steps/fix_settings.md` — fixes settings
     - `src/deepwork/standard_jobs/deepwork_jobs/steps/errata.md` — post-repair verification
   - If the schema change is breaking, add migration instructions to `fix_jobs.md`:
     - Describe what old job.yml files look like (before the change)
     - Describe what they should look like after migration
     - Provide specific transformation rules
   - If the change is non-breaking (new optional fields), migration may not be needed — document this decision

3. **Sync standard jobs**
   - After updating repair workflow files in `src/deepwork/standard_jobs/`, run `deepwork install` to sync to `.deepwork/jobs/`
   - This ensures the MCP server picks up the updated repair workflow

4. **Verify with get_workflows**
   - Call the `get_workflows` MCP tool
   - Confirm ALL jobs are listed and parsed correctly
   - Check that no parsing errors or warnings appear
   - If any jobs fail to parse, diagnose and fix the issue before completing

5. **Run the test suite one final time**
   - Run `uv run pytest tests/` to confirm everything passes
   - This is the final safety check

6. **Write the verification log**
   - Document the get_workflows output
   - Document the test suite results
   - Note any issues encountered and how they were resolved

## Output Format

### repair_step_file

The updated repair workflow step file (typically `fix_jobs.md`), if migration logic was added. This output is optional — if no migration was needed, skip it.

### verification_log

A markdown file at `.deepwork/tmp/verification_log.md`:

```markdown
# Verification Log

## Schema Change
[Brief description of what was changed]

## get_workflows Result
[Full output from the get_workflows MCP tool call, showing all jobs parsed successfully]

## Test Suite Result
[Summary of pytest results — number of tests passed/failed/skipped]

## Issues Encountered
[Any issues found during verification and how they were resolved, or "None"]

## Migration Status
[Whether the repair workflow was updated with migration logic, and why/why not]
```

## Quality Criteria

- The get_workflows MCP call succeeds and returns all jobs without parsing errors
- The full test suite passes (`uv run pytest tests/`)
- If the change is breaking, the repair workflow has migration instructions
- The verification log documents all results clearly
## Context

This step is the final gate. If get_workflows fails, it means something in the chain is broken — a job.yml doesn't conform, the parser can't handle a field, or the MCP layer has a mismatch. The repair workflow is also critical: when users upgrade DeepWork, the repair workflow is how their existing job.yml files get migrated to the new schema version.
