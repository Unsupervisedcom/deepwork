# Review Job Specification

## Objective

Review the `job.yml` created in the define step against quality criteria using a sub-agent for unbiased evaluation, then iterate on fixes until all criteria pass.

## Why This Step Exists

The define step focuses on understanding user requirements. This review step ensures the specification meets quality standards before implementation. A sub-agent provides "fresh eyes" that catch issues the main agent might miss.

## Task

Use a sub-agent to review the job.yml against doc spec quality criteria, fix any failures, and repeat until all pass.

### Step 1: Read the Job Specification

Read both files:
- `.deepwork/jobs/[job_name]/job.yml` - The specification to review
- `.deepwork/doc_specs/job_spec.md` - The quality criteria

### Step 2: Spawn Review Sub-Agent

Use the Task tool with:
- `subagent_type`: "general-purpose"
- `model`: "haiku"
- `description`: "Review job.yml against doc spec"

**Sub-agent prompt**:

```
Review this job.yml against the following 9 quality criteria.

For each criterion, respond with PASS or FAIL.
If FAIL: provide the specific issue and suggested fix.

## job.yml Content

[paste full job.yml content]

## Quality Criteria

1. **Valid Identifier**: Job name lowercase with underscores (e.g., `competitive_research`)
2. **Semantic Version**: Format X.Y.Z (e.g., `1.0.0`)
3. **Concise Summary**: Under 200 characters, describes what job accomplishes
4. **Rich Description**: Multi-line explaining problem, process, outcomes, users
5. **Changelog Present**: Array with at least initial version entry
6. **Complete Steps**: Each has id, name, description, instructions_file, outputs, dependencies
7. **Valid Dependencies**: Reference existing step IDs, no circular references
8. **Input Consistency**: File inputs with `from_step` reference a step in dependencies
9. **Output Paths**: Valid filenames or paths

## Response Format

### Overall: [X/9 PASS]

### Criterion Results
1. Valid Identifier: [PASS/FAIL]
   [If FAIL: Issue and fix]
...

### Summary of Required Fixes
[List fixes needed, or "No fixes required"]
```

### Step 3: Review Findings

Parse the sub-agent's response:
1. Count passing criteria
2. Identify failures
3. Note suggested fixes

### Step 4: Fix Failed Criteria

Edit job.yml to address each failure:

| Criterion | Common Fix |
|-----------|-----------|
| Valid Identifier | Convert to lowercase_underscores |
| Semantic Version | Set to `"1.0.0"` or fix format |
| Concise Summary | Shorten to <200 chars |
| Rich Description | Add multi-line explanation |
| Changelog Present | Add `changelog:` array |
| Complete Steps | Add missing required fields |
| Valid Dependencies | Fix step ID reference |
| Input Consistency | Add referenced step to dependencies |
| Output Paths | Use valid filename/path format |

### Step 5: Re-Run Review (If Needed)

If any criteria failed:
1. Spawn a new sub-agent with updated job.yml
2. Review new findings
3. Fix remaining issues
4. Repeat until all 9 criteria pass

### Step 6: Confirm Completion

When all 9 criteria pass:

1. Announce: "All 9 doc spec quality criteria pass."
2. Include: `<promise>Quality Criteria Met</promise>`
3. Guide: "Run `/deepwork_jobs.implement` to generate step instruction files."

## Output

The validated `job.yml` file at `.deepwork/jobs/[job_name]/job.yml` passing all 9 quality criteria.
