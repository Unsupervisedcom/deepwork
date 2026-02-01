# Define Job Specification

## Objective

Create a `job.yml` specification file that defines the structure of a new DeepWork job by understanding the user's workflow requirements through interactive questions.

## Task

Guide the user through defining a job specification by asking structured questions. The output is **only** the `job.yml` file - step instruction files are created in the `implement` step.

### Process

1. **Understand the job purpose**
   - Ask structured questions about the overall goal, domain, and frequency
   - Understand what success looks like and who the audience is
   - Identify the major phases of the workflow

2. **Detect document-oriented workflows**
   - Look for patterns: "report", "summary", "monthly", "for stakeholders"
   - If detected, offer to create a doc spec for consistent quality
   - Use `.deepwork/doc_specs/job_spec.md` as a reference example

3. **Define each step**
   - For each phase, gather: purpose, inputs, outputs, dependencies
   - Ask about output file paths and organization
   - Consider whether steps need agent delegation

4. **Validate the workflow**
   - Summarize the complete workflow
   - Check for gaps in inputs/outputs between steps
   - Confirm job name, summary, and version

5. **Create the job specification**
   - Run `make_new_job.sh` to create directory structure:
     ```bash
     .deepwork/jobs/deepwork_jobs/make_new_job.sh [job_name]
     ```
   - Create `job.yml` at `.deepwork/jobs/[job_name]/job.yml`

### Key Guidelines

- **Ask structured questions** using the AskUserQuestion tool
- **Work products go in main repo**, not `.deepwork/` (for discoverability)
- **Use dates in paths** for periodic outputs that accumulate
- **Use `_dataroom` folders** for supporting materials
- Reference templates in `.deepwork/jobs/deepwork_jobs/templates/`

## Output

Create `.deepwork/jobs/[job_name]/job.yml` following the doc spec at `.deepwork/doc_specs/job_spec.md`.

After creating the file, tell the user to run `/deepwork_jobs.review_job_spec` next.
