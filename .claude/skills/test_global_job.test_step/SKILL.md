---
name: test_global_job.test_step
description: "A simple test step"
user-invocable: false

---

# test_global_job.test_step

**Standalone skill** - can be run anytime

> A test global job for demonstration


## Instructions

**Goal**: A simple test step

# Test Step

This is a simple test step for the global job.

## Task

Just create a file called output.txt with some text in it.


### Job Context

This is a test job to demonstrate global job functionality


## Work Branch

Use branch format: `deepwork/test_global_job-[instance]-YYYYMMDD`

- If on a matching work branch: continue using it
- If on main/master: create new branch with `git checkout -b deepwork/test_global_job-[instance]-$(date +%Y%m%d)`

## Outputs

**Required outputs**:
- `output.txt`

## Guardrails

- Do NOT skip prerequisite verification if this step has dependencies
- Do NOT produce partial outputs; complete all required outputs before finishing
- Do NOT proceed without required inputs; ask the user if any are missing
- Do NOT modify files outside the scope of this step's defined outputs

## On Completion

1. Verify outputs are created
2. Inform user: "test_step complete, outputs: output.txt"

This standalone skill can be re-run anytime.

---

**Reference files**: `.deepwork/jobs/test_global_job/job.yml`, `.deepwork/jobs/test_global_job/steps/test_step.md`