---
name: experts.implement
description: "Generate step instruction files and sync skills from the validated workflow.yml"

---

# experts.implement

**Step 3/3** in **new_workflow** workflow

> Create a new multi-step DeepWork workflow with spec definition, review, and implementation

## Prerequisites (Verify First)

Before proceeding, confirm these steps are complete:
- `/experts.review_workflow_spec`

## Instructions

**Goal**: Generate step instruction files and sync skills from the validated workflow.yml

# Implement Workflow Steps

## Objective

Generate the step instruction files for each step in the validated `workflow.yml` specification, then sync the skills.

## Task

Read the `workflow.yml` specification and create all necessary files to make the workflow functional, then sync the commands.

### Step 1: Create Directory Structure

Create the workflow directories:

```bash
mkdir -p .deepwork/experts/[expert_name]/workflows/[workflow_name]/{steps,hooks}
```

This creates:
- `.deepwork/experts/[expert_name]/workflows/[workflow_name]/` - Main workflow directory
- `.deepwork/experts/[expert_name]/workflows/[workflow_name]/steps/` - Step instruction files
- `.deepwork/experts/[expert_name]/workflows/[workflow_name]/hooks/` - Custom validation scripts

**Note**: If directory exists from define step, skip or just create missing subdirectories.

### Step 2: Read and Validate the Specification

1. Read `.deepwork/experts/[expert_name]/workflows/[workflow_name]/workflow.yml`
2. Validate: name, version, summary, steps are present
3. Check dependencies reference existing steps, no circular dependencies
4. Verify file inputs match dependencies

### Step 3: Generate Step Instruction Files

For each step in workflow.yml, create `.deepwork/experts/[expert_name]/workflows/[workflow_name]/steps/[step_id].md`.

**Guidelines**:

1. **Use the workflow description** - It provides crucial context
2. **Be specific** - Tailor instructions to the step's purpose, not generic
3. **Provide examples** - Show what good output looks like
4. **Explain the "why"** - Help understand the step's role in the workflow
5. **Ask structured questions** - Steps with user inputs MUST explicitly tell the agent to "ask structured questions"
6. **Align with hooks** - If step has hooks, ensure quality criteria match

Each instruction file should include:
- **Objective** - What this step accomplishes
- **Task** - Detailed process
- **Output Format** - Examples of expected outputs
- **Quality Criteria** - How to verify completion

### Step 4: Verify workflow.yml Location

Ensure `workflow.yml` is at `.deepwork/experts/[expert_name]/workflows/[workflow_name]/workflow.yml`.

### Step 5: Sync Skills

Run:

```bash
deepwork sync
```

This generates skills in `.claude/skills/` (or appropriate platform directory).

### Step 6: Consider Rules

After implementing, consider whether **rules** would help this workflow's domain.

**What are rules?** Automated guardrails that trigger when certain files change, ensuring:
- Documentation stays in sync
- Team guidelines are followed
- Quality standards are maintained

**When to suggest rules:**
- Does this workflow produce outputs that other files depend on?
- Are there docs that should update when outputs change?
- Could changes impact other parts of the project?

**Examples**:
| Workflow Type | Potential Rule |
|---------------|----------------|
| API Design | "Update API docs when endpoint definitions change" |
| Competitive Research | "Update strategy docs when competitor analysis changes" |
| Feature Development | "Update changelog when feature files change" |

If you identify helpful rules, explain what they would do and offer: "Would you like me to create this rule? I can run `/deepwork-rules.define` to set it up."

**Note**: Not every workflow needs rules. Only suggest when genuinely helpful.

## Completion Checklist

- [ ] workflow.yml in correct location
- [ ] All step instruction files created (not stubs)
- [ ] Instructions are specific and actionable
- [ ] Output examples provided
- [ ] Quality criteria defined for each step
- [ ] `deepwork sync` executed successfully
- [ ] Considered relevant rules for this workflow


### Workflow Context

Guide the user through creating a new DeepWork workflow by:
1. Understanding their workflow requirements through interactive questioning
2. Creating a validated workflow.yml specification
3. Reviewing the spec against quality criteria
4. Generating step instruction files and syncing skills


## Required Inputs


**Files from Previous Steps** - Read these first:
- `.deepwork/experts/{expert_name}/workflows/{workflow_name}/workflow.yml` (from `review_workflow_spec`)

## Work Branch

Use branch format: `deepwork/experts-new_workflow-[instance]-YYYYMMDD`

- If on a matching work branch: continue using it
- If on main/master: create new branch with `git checkout -b deepwork/experts-new_workflow-[instance]-$(date +%Y%m%d)`

## Outputs

**Required outputs**:
- `.deepwork/experts/{expert_name}/workflows/{workflow_name}/steps/` (directory)

## Guardrails

- Do NOT skip prerequisite verification if this step has dependencies
- Do NOT produce partial outputs; complete all required outputs before finishing
- Do NOT proceed without required inputs; ask the user if any are missing
- Do NOT modify files outside the scope of this step's defined outputs

## On Completion

1. Verify outputs are created
2. Inform user: "new_workflow step 3/3 complete, outputs: .deepwork/experts/{expert_name}/workflows/{workflow_name}/steps/"
3. **new_workflow workflow complete**: All steps finished. Consider creating a PR to merge the work branch.

---

**Reference files**: `.deepwork/experts/experts/workflows/new_workflow/workflow.yml`, `.deepwork/experts/experts/workflows/new_workflow/steps/implement.md`