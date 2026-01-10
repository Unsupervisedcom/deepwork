# Example 1: Simple Job with User Inputs

**Context**: First (and only) step of simple_job - has user inputs, no dependencies

**Rendered Output**:

---

Name: simple_job.single_step
Description: A single step that performs a task

## Overview

This is step 1 of 1 in the **simple_job** workflow.

**Job**: A simple single-step job for testing

## Instructions

# Single Step Instructions

## Objective
Perform a simple task with the given input parameter.

## Task
Create an output file with the results of processing {{input_param}}.

## Output Format
Create `output.md` with the results.

## Inputs

### User Parameters

Please gather the following information from the user:
- **input_param**: An input parameter

## Work Branch Management

All work for this job should be done on a dedicated work branch:

1. **Check current branch**:
   - If already on a work branch for this job (format: `work/simple_job-[instance]-[date]`), continue using it
   - If on main/master, create a new work branch

2. **Create work branch** (if needed):
   ```bash
   git checkout -b work/simple_job-[instance]-$(date +%Y%m%d)
   ```
   Replace `[instance]` with a descriptive identifier (e.g., `acme`, `q1-launch`, etc.)

3. **All outputs go in the work directory**:
   - Create files in: `work/[branch-name]/`
   - This keeps work products organized and reviewable

## Output Requirements

Create the following output(s) in the work directory:
- `work/[branch-name]/output.md`

Ensure all outputs are:
- Well-formatted and complete
- Committed to the work branch
- Ready for review or use by subsequent steps

## Completion

After completing this step:

1. **Commit your work**:
   ```bash
   git add work/[branch-name]/
   git commit -m "simple_job: Complete single_step step"
   ```

2. **Verify outputs**: Confirm all required files have been created

3. **Inform the user**:
   - Step 1 of 1 is complete
   - Outputs created: output.md
   - This is the final step - the job is complete!

## Workflow Complete

This is the final step in the simple_job workflow. All outputs should now be complete and ready for review.

Consider:
- Reviewing all work products in `work/[branch-name]/`
- Creating a pull request to merge the work branch
- Documenting any insights or learnings

---

## Context Files

- Job definition: `.deepwork/jobs/simple_job/job.yml`
- Step instructions: `.deepwork/jobs/simple_job/steps/single_step.md`
