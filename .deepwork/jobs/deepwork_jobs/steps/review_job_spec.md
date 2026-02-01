# Review Job Specification

## Objective

Review the `job.yml` created in the define step against doc spec quality criteria, then iterate on fixes until all criteria pass.

## Why This Step Exists

The define step focuses on understanding user requirements. This review step ensures the specification meets quality standards before implementation. A fresh review catches issues that might be missed after being deeply involved in definition.

## Task

Review the job.yml against all 9 doc spec quality criteria, fix any failures, and repeat until all pass.

### Step 1: Read the Files

Read the job specification:
```
.deepwork/jobs/[job_name]/job.yml
```

Read the doc spec for reference:
```
.deepwork/doc_specs/job_spec.md
```

### Step 2: Evaluate Against Quality Criteria

Review the job.yml against these 9 criteria:

1. **Valid Identifier** - Job name is lowercase with underscores, no spaces or special characters
2. **Semantic Version** - Version follows X.Y.Z format (e.g., `1.0.0`)
3. **Concise Summary** - Summary is under 200 characters and clearly describes the job
4. **Rich Description** - Description is multi-line and explains: problem solved, process, expected outcomes, target users
5. **Changelog Present** - Includes changelog array with at least initial version entry
6. **Complete Steps** - Each step has: id, name, description, instructions_file, outputs, dependencies
7. **Valid Dependencies** - Dependencies reference existing step IDs with no circular references
8. **Input Consistency** - File inputs with `from_step` reference a step in the dependencies array
9. **Output Paths** - Outputs are valid filenames or paths

For each criterion, determine PASS or FAIL. If FAIL, note the specific issue and fix.

### Step 3: Fix Failed Criteria

For each failed criterion, edit the job.yml:

| Criterion | Common Issue | Fix |
|-----------|-------------|-----|
| Valid Identifier | Spaces or uppercase | Convert to lowercase_underscores |
| Semantic Version | Invalid format | Set to `"1.0.0"` |
| Concise Summary | Too long | Shorten to <200 chars |
| Rich Description | Single line | Add multi-line explanation |
| Changelog Present | Missing | Add changelog with initial version |
| Complete Steps | Missing fields | Add required fields |
| Valid Dependencies | Non-existent step | Fix step ID reference |
| Input Consistency | from_step not in deps | Add step to dependencies |
| Output Paths | Invalid format | Use valid filename/path |

### Step 4: Re-Evaluate (If Needed)

If any criteria failed:
1. Review the updated job.yml
2. Re-evaluate all criteria
3. Fix remaining issues
4. Repeat until all 9 pass

### Step 5: Confirm Completion

When all 9 criteria pass:

1. Announce: "All 9 doc spec quality criteria pass."
2. List what was validated
3. Include: `<promise>Quality Criteria Met</promise>`
4. Guide to next step: "Run `/deepwork_jobs.implement` to generate the step instruction files."

## Output

The validated `job.yml` file at `.deepwork/jobs/[job_name]/job.yml` that passes all 9 quality criteria.
