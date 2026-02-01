---
name: experts.review_workflow_spec
description: "Review workflow.yml against quality criteria using a sub-agent for unbiased validation"
user-invocable: false
context: fork
agent: general-purpose

---

# experts.review_workflow_spec

**Step 2/3** in **new_workflow** workflow

> Create a new multi-step DeepWork workflow with spec definition, review, and implementation

## Prerequisites (Verify First)

Before proceeding, confirm these steps are complete:
- `/experts.define`

## Instructions

**Goal**: Review workflow.yml against quality criteria using a sub-agent for unbiased validation

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


### Workflow Context

Guide the user through creating a new DeepWork workflow by:
1. Understanding their workflow requirements through interactive questioning
2. Creating a validated workflow.yml specification
3. Reviewing the spec against quality criteria
4. Generating step instruction files and syncing skills


## Required Inputs


**Files from Previous Steps** - Read these first:
- `.deepwork/experts/{expert_name}/workflows/{workflow_name}/workflow.yml` (from `define`)

## Work Branch

Use branch format: `deepwork/experts-new_workflow-[instance]-YYYYMMDD`

- If on a matching work branch: continue using it
- If on main/master: create new branch with `git checkout -b deepwork/experts-new_workflow-[instance]-$(date +%Y%m%d)`

## Outputs

**Required outputs**:
- `.deepwork/experts/{expert_name}/workflows/{workflow_name}/workflow.yml`

## Guardrails

- Do NOT skip prerequisite verification if this step has dependencies
- Do NOT produce partial outputs; complete all required outputs before finishing
- Do NOT proceed without required inputs; ask the user if any are missing
- Do NOT modify files outside the scope of this step's defined outputs

## Quality Validation

**Before completing this step, you MUST have your work reviewed against the quality criteria below.**

Use a sub-agent (Haiku model) to review your work against these criteria:

**Criteria (all must be satisfied)**:
1. Workflow name is lowercase with underscores, no spaces or special characters
2. Version follows X.Y.Z format (e.g., 1.0.0)
3. Summary is under 200 characters and clearly describes the workflow
4. Description is multi-line and explains problem, process, outcomes, and users
5. Each step has id, name, description, instructions_file, outputs
6. Step IDs are unique within the expert (across all workflows)
7. Dependencies reference existing step IDs with no circular references
8. File inputs with from_step reference a step in the dependencies array
9. Outputs are valid filenames or paths
**Review Process**:
1. Once you believe your work is complete, spawn a sub-agent using Haiku to review your work against the quality criteria above
2. The sub-agent should examine your outputs and verify each criterion is met
3. If the sub-agent identifies valid issues, fix them
4. Have the sub-agent review again until all valid feedback has been addressed
5. Only mark the step complete when the sub-agent confirms all criteria are satisfied

## On Completion

1. Verify outputs are created
2. Inform user: "new_workflow step 2/3 complete, outputs: .deepwork/experts/{expert_name}/workflows/{workflow_name}/workflow.yml"
3. **Continue workflow**: Use Skill tool to invoke `/experts.implement`

---

**Reference files**: `.deepwork/experts/experts/workflows/new_workflow/workflow.yml`, `.deepwork/experts/experts/workflows/new_workflow/steps/review_workflow_spec.md`