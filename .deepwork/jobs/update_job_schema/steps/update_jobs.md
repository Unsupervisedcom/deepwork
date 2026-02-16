# Update Standard, Library, and Instance Jobs

## Objective

Update all real job.yml files — standard jobs (source of truth in `src/deepwork/standard_jobs/`), library jobs (`library/jobs/`), and installed instances (`.deepwork/jobs/`) — to conform to the updated schema.

## Task

Real job.yml files are used at runtime by the DeepWork MCP server and CLI. They must conform to the updated schema or the system will fail to parse them.

### Process

1. **Read the change summary** and identify what fields changed

2. **Find all real job.yml files**
   - Standard jobs: `src/deepwork/standard_jobs/*/job.yml`
   - Library jobs: `library/jobs/*/job.yml`
   - Instance jobs: `.deepwork/jobs/*/job.yml`

3. **Update standard jobs first** (source of truth)
   - Read and update `src/deepwork/standard_jobs/deepwork_jobs/job.yml`
   - This is the most important file — it defines the core DeepWork workflows
   - Be careful to preserve all existing workflow and step definitions
   - Add new fields thoughtfully — these serve as examples for users

4. **Update library jobs**
   - Read and update `library/jobs/spec_driven_development/job.yml`
   - Preserve the job's intended workflow while adding new schema fields

5. **Update instance jobs**
   - Update `.deepwork/jobs/deepwork_jobs/job.yml` (installed copy of standard job)
   - Update `.deepwork/jobs/test_job_flow/job.yml`
   - Update any other instance jobs found
   - **Note**: For the standard job copy, it should match the source of truth after changes

6. **Sync the install**
   - After updating standard jobs source, run `deepwork install` to sync to `.deepwork/jobs/`
   - Or manually copy changed files if install isn't available

## Output Format

### job_files

All updated job.yml files across all three locations. Each should conform to the updated schema.

**Example — adding a new optional `timeout` field to a step in a real job:**

Before:
```yaml
  - id: define
    name: "Define Job Specification"
    description: "Create a job.yml specification..."
    instructions_file: steps/define.md
    outputs:
      job.yml:
        type: file
        description: "Definition of the job"
        required: true
    reviews:
      - run_each: job.yml
        quality_criteria:
          "Complete": "Is the job.yml complete?"
```

After (with new optional field used where it makes sense):
```yaml
  - id: define
    name: "Define Job Specification"
    description: "Create a job.yml specification..."
    instructions_file: steps/define.md
    timeout: 600  # Optional — added where meaningful
    outputs:
      job.yml:
        type: file
        description: "Definition of the job"
        required: true
    reviews:
      - run_each: job.yml
        quality_criteria:
          "Complete": "Is the job.yml complete?"
```

**Common mistake to avoid**: Don't add new required fields without defaults — this breaks backwards compatibility for users who haven't updated their job files yet. If the schema change adds a required field, the repair workflow (final step) must handle migration.

## Quality Criteria

- All standard job files conform to the updated schema
- All library job files conform to the updated schema
- All instance job files conform to the updated schema
- Standard job source of truth and installed copies are in sync
- Existing workflows and step definitions are preserved
- New fields are used appropriately in each job's context
## Context

Standard jobs are auto-installed to every user's project. Library jobs serve as examples users can adopt. Instance jobs are the working copies read by the MCP server at runtime. All three must conform to the schema or the system breaks. Standard jobs are the source of truth — update them first, then propagate.
