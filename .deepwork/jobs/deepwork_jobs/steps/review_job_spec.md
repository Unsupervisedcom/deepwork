# Review Job Specification

## Objective

Review the `job.yml` created in the define step against the doc spec quality criteria using a sub-agent for unbiased evaluation, then iterate on fixes until all criteria pass.

## Why This Step Exists

The define step focuses on understanding user requirements. This review step ensures the specification meets quality standards before implementation. A sub-agent provides "fresh eyes" that catch issues the main agent might miss.

## Task

Use a sub-agent to review the job.yml against all 9 doc spec quality criteria, then fix any failed criteria.

### Process

1. **Read the files**
   - Read `.deepwork/jobs/[job_name]/job.yml`
   - Read `.deepwork/doc_specs/job_spec.md` for reference

2. **Spawn review sub-agent**
   - Use Task tool with `subagent_type: general-purpose` and `model: haiku`
   - Include the full job.yml content and all 9 quality criteria in the prompt
   - Request PASS/FAIL for each criterion with specific issues if failed

3. **Fix failed criteria**
   - Edit job.yml to address each failed criterion
   - Common fixes: shorten summary, add changelog, fix dependencies

4. **Re-run review if needed**
   - Spawn a new sub-agent with updated content
   - Repeat until all 9 criteria pass

5. **Confirm completion**
   - Announce "All 9 doc spec quality criteria pass"
   - Include `<promise>Quality Criteria Met</promise>`
   - Guide to next step: `/deepwork_jobs.implement`

### The 9 Quality Criteria

1. **Valid Identifier**: lowercase with underscores, no spaces
2. **Semantic Version**: X.Y.Z format
3. **Concise Summary**: under 200 characters
4. **Rich Description**: multi-line with problem/process/outcome/users
5. **Changelog Present**: array with at least initial version
6. **Complete Steps**: each has id, name, description, instructions_file, outputs, dependencies
7. **Valid Dependencies**: reference existing steps, no circular refs
8. **Input Consistency**: from_step must be in dependencies
9. **Output Paths**: valid filenames or paths

## Output

The validated `job.yml` file that passes all quality criteria.
