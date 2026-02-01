---
name: deepwork_jobs.implement
description: "Generates step instruction files and syncs slash commands from the job.yml specification. Use after job spec review passes."
user-invocable: false
context: fork
agent: deepwork-jobs

---

# deepwork_jobs.implement

**Step 3/3** in **new_job** workflow

> Create a new DeepWork job from scratch through definition, review, and implementation

> Creates and manages multi-step AI workflows. Use when defining, implementing, or improving DeepWork jobs.

## Prerequisites (Verify First)

Before proceeding, confirm these steps are complete:
- `/deepwork_jobs.review_job_spec`

## Instructions

**Goal**: Generates step instruction files and syncs slash commands from the job.yml specification. Use after job spec review passes.

# Implement Job Steps

## Objective

Generate the DeepWork job directory structure and instruction files for each step based on the validated `job.yml` specification.

## Task

Read the `job.yml` specification and create all necessary files to make the job functional.

### Step 1: Create Directory Structure

Run the setup script:
```bash
.deepwork/jobs/deepwork_jobs/make_new_job.sh [job_name]
```

This creates:
- `.deepwork/jobs/[job_name]/steps/` - Step instruction files
- `.deepwork/jobs/[job_name]/hooks/` - Validation scripts
- `.deepwork/jobs/[job_name]/templates/` - Example file formats
- `.deepwork/jobs/[job_name]/AGENTS.md` - Job management guidance

**Note**: If directory already exists from define step, create missing subdirectories manually.

### Step 2: Read and Validate the Specification

1. Read `.deepwork/jobs/[job_name]/job.yml`
2. Validate structure (name, version, summary, description, steps)
3. Check dependencies are valid and non-circular
4. Extract step details for instruction generation

### Step 3: Generate Step Instruction Files

Create `.deepwork/jobs/[job_name]/steps/[step_id].md` for each step.

**Templates**:
- `.deepwork/jobs/deepwork_jobs/templates/step_instruction.md.template` - Structure
- `.deepwork/jobs/deepwork_jobs/templates/step_instruction.md.example` - Complete example

**Guidelines**:

1. **Use the job description** - It provides crucial context
2. **Be specific** - Tailor instructions to each step's purpose
3. **Provide examples** - Show what good output looks like
4. **Explain the "why"** - Help understand the step's role in the workflow
5. **Ask structured questions** - When a step has user inputs, MUST use this phrase
6. **Align with hooks** - If step has `hooks` defined, match quality criteria

**Handling Hooks**:

If a step has hooks defined, the instruction file should:
- Mirror the quality criteria that hooks will validate
- Be explicit about what success looks like
- Mention the `<promise>Quality Criteria Met</promise>` pattern when criteria are met

### Step 4: Verify job.yml Location

Confirm `job.yml` exists at `.deepwork/jobs/[job_name]/job.yml`.

### Step 5: Sync Skills

Run:
```bash
deepwork sync
```

This generates skills for each step in `.claude/skills/` (or platform-specific directory).

### Step 6: Consider Rules

After implementing, consider whether **rules** would help enforce quality.

**What are rules?**
Automated guardrails in `.deepwork/rules/` that trigger when files change.

**When to suggest rules**:
- Job produces outputs that other files depend on
- Documentation should stay in sync with outputs
- Quality checks should happen when certain files change

**Examples**:
| Job Type | Potential Rule |
|----------|----------------|
| API Design | Update docs when endpoints change |
| Database Schema | Review migrations when schema changes |
| Competitive Research | Update strategy when analysis changes |

If a rule would help, explain what it would do and offer to run `/deepwork_rules.define`.

## Completion Checklist

Before marking complete:
- [ ] job.yml validated and in place
- [ ] All step instruction files created (complete, not stubs)
- [ ] Instructions are specific and actionable
- [ ] Output examples provided
- [ ] Quality criteria defined for each step
- [ ] User input steps use "ask structured questions"
- [ ] `deepwork sync` executed successfully
- [ ] Skills available in platform directory
- [ ] Considered relevant rules for job domain

## Output

Complete step instruction files at `.deepwork/jobs/[job_name]/steps/` and synced skills.


### Job Context

Core commands for managing DeepWork jobs. These commands help you define new multi-step
workflows and learn from running them.

The `new_job` workflow guides you through defining and implementing a new job by
asking structured questions about your workflow, understanding each step's inputs and outputs,
reviewing the specification, and generating all necessary files.

The `learn` skill reflects on conversations where DeepWork jobs were run, identifies
confusion or inefficiencies, and improves job instructions. It also captures bespoke
learnings specific to the current run into AGENTS.md files in the working folder.


## Required Inputs


**Files from Previous Steps** - Read these first:
- `job.yml` (from `review_job_spec`)

## Work Branch

Use branch format: `deepwork/deepwork_jobs-[instance]-YYYYMMDD`

- If on a matching work branch: continue using it
- If on main/master: create new branch with `git checkout -b deepwork/deepwork_jobs-[instance]-$(date +%Y%m%d)`

## Outputs

**Required outputs**:
- `steps/` (directory)

## Guardrails

- Do NOT skip prerequisite verification if this step has dependencies
- Do NOT produce partial outputs; complete all required outputs before finishing
- Do NOT proceed without required inputs; ask the user if any are missing
- Do NOT modify files outside the scope of this step's defined outputs

## Quality Validation

**Before completing this step, you MUST have your work reviewed against the quality criteria below.**

Use a sub-agent (Haiku model) to review your work against these criteria:

**Criteria (all must be satisfied)**:
1. **Directory Structure**: Is `.deepwork/jobs/[job_name]/` created correctly?
2. **Complete Instructions**: Are ALL step instruction files complete (not stubs or placeholders)?
3. **Specific & Actionable**: Are instructions tailored to each step's purpose, not generic?
4. **Output Examples**: Does each instruction file show what good output looks like?
5. **Quality Criteria**: Does each instruction file define quality criteria for its outputs?
6. **Ask Structured Questions**: Do step instructions that gather user input explicitly use the phrase "ask structured questions"?
7. **Sync Complete**: Has `deepwork sync` been run successfully?
8. **Commands Available**: Are the slash-commands generated in `.claude/commands/`?
9. **Rules Considered**: Has the agent thought about whether rules would benefit this job? If relevant rules were identified, did they explain them and offer to run `/deepwork_rules.define`? Not every job needs rules - only suggest when genuinely helpful.
**Review Process**:
1. Once you believe your work is complete, spawn a sub-agent using Haiku to review your work against the quality criteria above
2. The sub-agent should examine your outputs and verify each criterion is met
3. If the sub-agent identifies valid issues, fix them
4. Have the sub-agent review again until all valid feedback has been addressed
5. Only mark the step complete when the sub-agent confirms all criteria are satisfied

## On Completion

1. Verify outputs are created
2. Inform user: "new_job step 3/3 complete, outputs: steps/"
3. **new_job workflow complete**: All steps finished. Consider creating a PR to merge the work branch.

---

**Reference files**: `.deepwork/jobs/deepwork_jobs/job.yml`, `.deepwork/jobs/deepwork_jobs/steps/implement.md`