---
description: Reflect on conversation to improve job instructions and capture learnings
hooks:
  Stop:
    - hooks:
        - type: prompt
          prompt: |
            You must evaluate whether Claude has met all the below quality criteria for the request.

            ## Quality Criteria

            Verify the learning process meets ALL quality criteria before completing:

            1. **Conversation Analyzed**: Did you review the conversation for DeepWork job executions?
            2. **Confusion Identified**: Did you identify points of confusion, errors, or inefficiencies?
            3. **Instructions Improved**: Were job instructions updated to address identified issues?
            4. **Instructions Concise**: Are instructions free of redundancy and unnecessary verbosity?
            5. **Shared Content Extracted**: Is lengthy/duplicated content extracted into referenced files?
            6. **Bespoke Learnings Captured**: Were run-specific learnings added to AGENTS.md?
            7. **File References Used**: Do AGENTS.md entries reference other files where appropriate?
            8. **Working Folder Correct**: Is AGENTS.md in the correct working folder for the job?
            9. **Generalizable Separated**: Are generalizable improvements in instructions, not AGENTS.md?
            10. **Sync Complete**: Has `deepwork sync` been run if instructions were modified?

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

# deepwork_jobs.learn

**Standalone command** in the **deepwork_jobs** job - can be run anytime

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



## Instructions

# Learn from Job Execution

## Objective

Reflect on the conversation to identify learnings from DeepWork job executions, improve job instructions with generalizable insights, and capture bespoke (run-specific) learnings in AGENTS.md.

**Reference**: See `deepwork_jobs.md` for job structure and templates.

## Task

Analyze conversation history to extract learnings:
- **Generalizable learnings** → Update job instruction files
- **Bespoke learnings** (specific to this run) → Add to AGENTS.md in working folder

### Step 1: Analyze Conversation

1. Scan for DeepWork slash commands (`/job_name.step_id`)
2. Identify working folder from conversation or `git diff`
3. If no job specified, ask user which job to analyze

### Step 2: Identify Issues

Look for:
- **Confusion** - Unnecessary questions, misunderstandings, incorrect outputs
- **Inefficiency** - Extra iterations, repeated information, missing context
- **Errors** - Failed validations, misunderstood criteria, unhandled edge cases
- **Successes** - What worked well, efficient approaches, good examples

### Step 3: Classify Learnings

**Generalizable** (update instructions):
- Helps ANY future run
- Fixes unclear/missing guidance
- Adds helpful examples
- Example: "Instructions should mention X format is required"

**Bespoke** (add to AGENTS.md):
- Specific to THIS project/codebase
- References local conventions/files
- Example: "API endpoints are in `src/api/`"

### Step 4: Update Instructions (Generalizable)

1. Edit `.deepwork/jobs/[job_name]/steps/[step_id].md`
2. Add missing context, examples, clarifications
3. Keep concise - avoid redundancy
4. Track changes for changelog

### Step 4b: Extract Shared Content

Review instruction files for duplicated or lengthy content. Extract to `.deepwork/jobs/[job_name]/steps/shared/`:
- `conventions.md` - Formatting conventions
- `examples.md` - Common examples
- `schemas.md` - Data structures

Reference from instructions: "Follow conventions in `shared/conventions.md`"

### Step 5: Create/Update AGENTS.md (Bespoke)

Place AGENTS.md in the working folder where job outputs live.

**Use file references** instead of duplicating content:
```markdown
# Good
- API endpoints follow REST conventions. See `src/api/routes.ts` for examples.

# Avoid
- API endpoints should return JSON with format: { status: ..., data: ... }
```

**Template**: See `.deepwork/jobs/deepwork_jobs/templates/agents.md.template`

### Step 6: Update Version and Changelog

If instructions modified:
1. Bump version in job.yml (patch for improvements, minor for criteria changes)
2. Add changelog entry

### Step 7: Sync and Relay

```bash
deepwork sync
```

Tell user how to reload commands.

## Quality Criteria

- Conversation analyzed for job executions
- Confusion and inefficiency identified
- Learnings correctly classified (generalizable vs bespoke)
- Instructions updated for generalizable improvements
- Instructions concise - no redundancy
- Shared content extracted where appropriate
- AGENTS.md created/updated with bespoke learnings
- File references used instead of duplicating content
- AGENTS.md in correct working folder
- When all criteria are met, include `<promise>✓ Quality Criteria Met</promise>`

## Edge Cases

- **No job executions found**: Ask which job to analyze
- **Multiple jobs**: Analyze each separately
- **AGENTS.md exists**: Append to appropriate sections
- **No issues found**: Document what worked well
- **Sensitive info**: Never include secrets/credentials - reference config files instead


## Inputs

### User Parameters

Please gather the following information from the user:
- **job_name**: Name of the job that was run (optional - will auto-detect from conversation)


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
- `AGENTS.md`
Ensure all outputs are:
- Well-formatted and complete
- Ready for review or use by subsequent steps

## Quality Validation Loop

This step uses an iterative quality validation loop. After completing your work, stop hook(s) will evaluate whether the outputs meet quality criteria. If criteria are not met, you will be prompted to continue refining.

### Quality Criteria
Verify the learning process meets ALL quality criteria before completing:

1. **Conversation Analyzed**: Did you review the conversation for DeepWork job executions?
2. **Confusion Identified**: Did you identify points of confusion, errors, or inefficiencies?
3. **Instructions Improved**: Were job instructions updated to address identified issues?
4. **Instructions Concise**: Are instructions free of redundancy and unnecessary verbosity?
5. **Shared Content Extracted**: Is lengthy/duplicated content extracted into referenced files?
6. **Bespoke Learnings Captured**: Were run-specific learnings added to AGENTS.md?
7. **File References Used**: Do AGENTS.md entries reference other files where appropriate?
8. **Working Folder Correct**: Is AGENTS.md in the correct working folder for the job?
9. **Generalizable Separated**: Are generalizable improvements in instructions, not AGENTS.md?
10. **Sync Complete**: Has `deepwork sync` been run if instructions were modified?

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
   - The learn command is complete
   - Outputs created: AGENTS.md
   - This command can be run again anytime to make further changes

## Command Complete

This is a standalone command that can be run anytime. The outputs are ready for use.

Consider:
- Reviewing the outputs
- Running `deepwork sync` if job definitions were changed
- Re-running this command later if further changes are needed

---

## Context Files

- Job definition: `.deepwork/jobs/deepwork_jobs/job.yml`
- Step instructions: `.deepwork/jobs/deepwork_jobs/steps/learn.md`