---
description: Generate instruction files for each step based on the job.yml specification
hooks:
  Stop:
    - hooks:
        - type: prompt
          prompt: |
            You must evaluate whether Claude has met all the below quality criteria for the request.

            ## Quality Criteria

            Verify the implementation meets ALL quality criteria before completing:

            1. **Directory Structure**: Is `.deepwork/jobs/[job_name]/` created correctly?
            2. **Complete Instructions**: Are ALL step instruction files complete (not stubs or placeholders)?
            3. **Specific & Actionable**: Are instructions tailored to each step's purpose, not generic?
            4. **Output Examples**: Does each instruction file show what good output looks like?
            5. **Quality Criteria**: Does each instruction file define quality criteria for its outputs?
            6. **Sync Complete**: Has `deepwork sync` been run successfully?
            7. **Commands Available**: Are the slash-commands generated in `.claude/commands/`?
            8. **Policies Considered**: Have you thought about whether policies would benefit this job?
               - If relevant policies were identified, did you explain them and offer to run `/deepwork_policy.define`?
               - Not every job needs policies - only suggest when genuinely helpful.

            If ANY criterion is not met, continue working to address it.
            If ALL criteria are satisfied, include `<promise>✓ Quality Criteria Met</promise>` in your response.


            ## Instructions

            Review the conversation and determine if ALL quality criteria above have been satisfied.
            Look for evidence that each criterion has been addressed.

            If the agent has included `<promise>✓ Quality Criteria Met</promise>` in their response AND
            all criteria appear to be met, respond with: {"ok": true}

            If criteria are NOT met AND the promise tag is missing, respond with:
            {"ok": false, "reason": "Continue working. [specific feedback on what's wrong]"}
---

# deepwork_jobs.implement

**Step 2 of 3** in the **deepwork_jobs** workflow

**Summary**: DeepWork job management commands

## Job Overview

Core commands for managing DeepWork jobs. These commands help you define new multi-step
workflows and learn from running them.

The `define` command guides you through an interactive process to create a new job by
asking detailed questions about your workflow, understanding each step's inputs and outputs,
and generating all necessary files.

The `learn` command reflects on conversations where DeepWork jobs were run, identifies
confusion or inefficiencies, and improves job instructions. It also captures bespoke
learnings specific to the current run into AGENTS.md files in the working folder.


## Prerequisites

This step requires completion of the following step(s):
- `/deepwork_jobs.define`

Please ensure these steps have been completed before proceeding.

## Instructions

# Implement Job Steps

## Objective

Generate step instruction files for each step based on the `job.yml` specification created in the define step.

**Reference**: See `deepwork_jobs.md` for job structure, step instruction format, and templates.

## Task

Read the `job.yml` specification and create instruction files to make the job functional.

### Step 1: Create Directory Structure (if needed)

If directory doesn't exist, run:
```bash
.deepwork/jobs/deepwork_jobs/make_new_job.sh [job_name]
```

Or manually create missing directories:
```bash
mkdir -p .deepwork/jobs/[job_name]/hooks .deepwork/jobs/[job_name]/templates
touch .deepwork/jobs/[job_name]/hooks/.gitkeep .deepwork/jobs/[job_name]/templates/.gitkeep
```

### Step 2: Read and Validate Specification

1. Read `.deepwork/jobs/[job_name]/job.yml`
2. Validate schema (name, version, summary, description, steps)
3. Check dependencies reference existing steps, no circular dependencies
4. Extract job name, version, summary, description, and step details

### Step 3: Generate Step Instruction Files

For each step, create `.deepwork/jobs/[job_name]/steps/[step_id].md`.

**Templates**: See `.deepwork/jobs/deepwork_jobs/templates/step_instruction.md.template` and `step_instruction.md.example`

**Guidelines:**
- Use the job description for context
- Be specific, not generic
- Provide output examples
- Explain the "why"
- Align quality criteria with stop hooks

### Handling Stop Hooks

If step has `stop_hooks`, the instruction file's Quality Criteria section must match what hooks validate. Include the promise pattern: `<promise>✓ Quality Criteria Met</promise>`

### Step 4: Sync Commands

```bash
deepwork sync
```

### Step 5: Relay Reload Instructions

Tell user how to reload commands:
- **Claude Code**: Type `exit` then run `claude --resume`
- **Gemini CLI**: Run `/memory refresh`

### Step 6: Consider Policies

Think about whether policies would help maintain consistency for this job's domain.

**Policies** are guardrails in `.deepwork.policy.yml` that trigger when files change.

Consider:
- Does this job produce outputs other files depend on?
- Should documentation be updated when outputs change?
- Are there quality checks that should happen on certain file changes?

If policies would help, explain what they'd do and offer to run `/deepwork_policy.define`.

## Completion Checklist

- [ ] job.yml validated
- [ ] All step instruction files created (complete, not stubs)
- [ ] Each instruction is specific and actionable
- [ ] Output examples provided
- [ ] `deepwork sync` executed
- [ ] User informed about reload instructions
- [ ] Policies considered (suggest if relevant)

## Quality Criteria

- Job directory structure correct
- All instruction files complete (not stubs)
- Instructions specific and actionable
- Output examples provided
- Quality criteria defined for each step
- Sync completed successfully
- Commands available for use
- Policies thoughtfully considered


## Inputs


### Required Files

This step requires the following files from previous steps:
- `job.yml` (from step `define`)

Make sure to read and use these files as context for this step.

## Work Branch Management

All work for this job should be done on a dedicated work branch:

1. **Check current branch**:
   - If already on a work branch for this job (format: `deepwork/deepwork_jobs-[instance]-[date]`), continue using it
   - If on main/master, create a new work branch

2. **Create work branch** (if needed):
   ```bash
   git checkout -b deepwork/deepwork_jobs-[instance]-$(date +%Y%m%d)
   ```
   Replace `[instance]` with a descriptive identifier (e.g., `acme`, `q1-launch`, etc.)

## Output Requirements

Create the following output(s):
- `steps/` (directory)
Ensure all outputs are:
- Well-formatted and complete
- Ready for review or use by subsequent steps

## Quality Validation Loop

This step uses an iterative quality validation loop. After completing your work, stop hook(s) will evaluate whether the outputs meet quality criteria. If criteria are not met, you will be prompted to continue refining.

### Quality Criteria
Verify the implementation meets ALL quality criteria before completing:

1. **Directory Structure**: Is `.deepwork/jobs/[job_name]/` created correctly?
2. **Complete Instructions**: Are ALL step instruction files complete (not stubs or placeholders)?
3. **Specific & Actionable**: Are instructions tailored to each step's purpose, not generic?
4. **Output Examples**: Does each instruction file show what good output looks like?
5. **Quality Criteria**: Does each instruction file define quality criteria for its outputs?
6. **Sync Complete**: Has `deepwork sync` been run successfully?
7. **Commands Available**: Are the slash-commands generated in `.claude/commands/`?
8. **Policies Considered**: Have you thought about whether policies would benefit this job?
   - If relevant policies were identified, did you explain them and offer to run `/deepwork_policy.define`?
   - Not every job needs policies - only suggest when genuinely helpful.

If ANY criterion is not met, continue working to address it.
If ALL criteria are satisfied, include `<promise>✓ Quality Criteria Met</promise>` in your response.


### Completion Promise

To signal that all quality criteria have been met, include this tag in your final response:

```
<promise>✓ Quality Criteria Met</promise>
```

**Important**: Only include this promise tag when you have verified that ALL quality criteria above are satisfied. The validation loop will continue until this promise is detected.

## Completion

After completing this step:

1. **Verify outputs**: Confirm all required files have been created

2. **Inform the user**:
   - Step 2 of 3 is complete
   - Outputs created: steps/
   - Ready to proceed to next step: `/deepwork_jobs.learn`

## Next Step

To continue the workflow, run:
```
/deepwork_jobs.learn
```

---

## Context Files

- Job definition: `.deepwork/jobs/deepwork_jobs/job.yml`
- Step instructions: `.deepwork/jobs/deepwork_jobs/steps/implement.md`