# Review Workflow Specification

## Objective

Review the `workflow.yml` created in the define step against quality criteria, then iterate on fixes until all criteria pass.

## Why This Step Exists

The define step focuses on understanding user requirements. This review step ensures the specification meets quality standards before implementation. A fresh review catches issues that might be missed after being deeply involved in definition.

## Task

Review the workflow.yml against all quality criteria, fix any failures, and repeat until all pass.

### Step 1: Read the Files

Read the workflow specification:
```
.deepwork/experts/[expert_name]/workflows/[workflow_name]/workflow.yml
```

### Step 2: Evaluate Against Quality Criteria

Review the workflow.yml against these criteria:

1. **Valid Identifier** - Workflow name is lowercase with underscores, matches folder name
2. **Semantic Version** - Version follows X.Y.Z format (e.g., `1.0.0`)
3. **Concise Summary** - Summary is under 200 characters and clearly describes the workflow
4. **Rich Description** - Description is multi-line and explains: problem solved, process, expected outcomes, target users
5. **Complete Steps** - Each step has: id, name, description, instructions_file, outputs
6. **Unique Step IDs** - Step IDs are unique within the expert (across all workflows)
7. **Valid Dependencies** - Dependencies reference existing step IDs with no circular references
8. **Input Consistency** - File inputs with `from_step` reference a step in the dependencies array
9. **Output Paths** - Outputs are valid filenames or paths

For each criterion, determine PASS or FAIL. If FAIL, note the specific issue and fix.

### Step 3: Fix Failed Criteria

For each failed criterion, edit the workflow.yml:

| Criterion | Common Issue | Fix |
|-----------|-------------|-----|
| Valid Identifier | Spaces or uppercase | Convert to lowercase_underscores |
| Semantic Version | Invalid format | Set to `"1.0.0"` |
| Concise Summary | Too long | Shorten to <200 chars |
| Rich Description | Single line | Add multi-line explanation |
| Complete Steps | Missing fields | Add required fields |
| Unique Step IDs | Duplicate ID | Rename to unique identifier |
| Valid Dependencies | Non-existent step | Fix step ID reference |
| Input Consistency | from_step not in deps | Add step to dependencies |
| Output Paths | Invalid format | Use valid filename/path |

### Step 4: Re-Evaluate (If Needed)

If any criteria failed:
1. Review the updated workflow.yml
2. Re-evaluate all criteria
3. Fix remaining issues
4. Repeat until all pass

### Step 5: Confirm Completion

When all criteria pass:

1. Announce: "All workflow spec quality criteria pass."
2. List what was validated
3. Guide to next step: "Run `/experts.implement` to generate the step instruction files."

## Output

The validated `workflow.yml` file at `.deepwork/experts/[expert_name]/workflows/[workflow_name]/workflow.yml` that passes all quality criteria.
