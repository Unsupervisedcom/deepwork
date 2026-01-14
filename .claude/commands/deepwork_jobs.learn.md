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
            4. **Bespoke Learnings Captured**: Were run-specific learnings added to AGENTS.md?
            5. **File References Used**: Do AGENTS.md entries reference other files where appropriate?
            6. **Working Folder Correct**: Is AGENTS.md in the correct working folder for the job?
            7. **Generalizable Separated**: Are generalizable improvements in instructions, not AGENTS.md?
            8. **Sync Complete**: Has `deepwork sync` been run if instructions were modified?

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

Reflect on the current conversation to identify learnings from DeepWork job executions, improve job instructions with generalizable insights, and capture bespoke (run-specific) learnings in AGENTS.md files in the appropriate working folder.

## Task

Analyze the conversation history to extract learnings and improvements, then apply them appropriately:
- **Generalizable learnings** → Update job instruction files
- **Bespoke learnings** (specific to this run) → Add to AGENTS.md in working folder

### Step 1: Analyze Conversation for Job Executions

1. **Scan the conversation** for DeepWork slash commands that were run
   - Look for patterns like `/job_name.step_id`
   - Identify which jobs and steps were executed
   - Note the order of execution

2. **Identify the working folder**
   - Find where outputs were created during job execution
   - This is typically specified in the job's working directory
   - Common patterns: project root, `./output/`, or job-specific directories

3. **If no job was specified**, ask the user:
   - "Which DeepWork job would you like me to learn from?"
   - List available jobs from `.deepwork/jobs/`

### Step 2: Identify Points of Confusion and Inefficiency

Review the conversation for:

1. **Confusion signals**
   - Questions the agent asked that shouldn't have been necessary
   - Misunderstandings about what a step required
   - Incorrect outputs that needed correction
   - Ambiguous instructions that led to wrong interpretations

2. **Inefficiency signals**
   - Extra steps or iterations that were needed
   - Information that had to be repeated
   - Context that was missing from instructions
   - Dependencies that weren't clear

3. **Error patterns**
   - Failed validations and why they failed
   - Quality criteria that were misunderstood
   - Edge cases that weren't handled

4. **Success patterns**
   - What worked particularly well
   - Efficient approaches worth preserving
   - Good examples that could be added to instructions

### Step 3: Classify Learnings

For each learning identified, determine if it is:

**Generalizable** (should improve instructions):
- Would help ANY future run of this job
- Addresses unclear or missing guidance
- Fixes incorrect assumptions in instructions
- Adds helpful examples or context
- Examples:
  - "Step instructions should mention that X format is required"
  - "Quality criteria should include checking for Y"
  - "Add example of correct output format"

**Bespoke** (should go in AGENTS.md):
- Specific to THIS project/codebase/run
- Depends on local conventions or structure
- References specific files or paths
- Would not apply to other uses of this job
- Examples:
  - "In this codebase, API endpoints are in `src/api/`"
  - "This project uses camelCase for function names"
  - "The main config file is at `config/settings.yml`"

### Step 4: Update Job Instructions (Generalizable Learnings)

For each generalizable learning:

1. **Locate the instruction file**
   - Path: `.deepwork/jobs/[job_name]/steps/[step_id].md`

2. **Make targeted improvements**
   - Add missing context or clarification
   - Include helpful examples
   - Clarify ambiguous instructions
   - Update quality criteria if needed

3. **Preserve instruction structure**
   - Keep existing sections (Objective, Task, Process, Output Format, Quality Criteria)
   - Add to appropriate sections rather than restructuring
   - Maintain consistency with other steps

4. **Track changes for changelog**
   - Note what was changed and why
   - Prepare changelog entry for job.yml

### Step 5: Create/Update AGENTS.md (Bespoke Learnings)

The AGENTS.md file captures project-specific knowledge that helps future agent runs.

1. **Determine the correct location**
   - Place AGENTS.md in the working folder where job outputs live
   - This ensures the knowledge is available when working in that context
   - If uncertain, place at the project root

2. **Use file references where possible**
   - Instead of duplicating information, reference source files
   - This keeps AGENTS.md in sync as the codebase evolves
   - Pattern: "See `path/to/file.ext` for [description]"

3. **AGENTS.md structure**:

```markdown
# Project Context for [Job Name]

## Codebase Structure

<!-- Reference files rather than duplicating content -->
- Project structure: See `README.md` for overview
- API documentation: See `docs/api.md`
- Configuration: See `config/README.md`

## Conventions

### Naming Conventions
- [Convention]: See example in `path/to/example.ext:LINE`

### File Organization
- [Pattern]: Reference `path/to/pattern/`

## Job-Specific Context

### [Job Name]

#### [Step Name]
- [Learning]: Reference `relevant/file.ext`
- [Context]: [Brief explanation with file reference]

## Known Issues and Workarounds

- [Issue]: [Workaround with file reference if applicable]

## Last Updated
- Date: [YYYY-MM-DD]
- From conversation about: [Brief description]
```

4. **Writing entries**
   - Be concise but specific
   - Always prefer file references over inline content
   - Use line numbers when referencing specific code: `file.ext:42`
   - Group related learnings together

### Step 6: Update Job Version and Changelog

If instruction files were modified:

1. **Bump version in job.yml**
   - Patch version (0.0.x) for instruction improvements
   - Minor version (0.x.0) if quality criteria changed

2. **Add changelog entry**
   ```yaml
   - version: "[new_version]"
     changes: "Improved [step] instructions based on execution learnings: [brief description]"
   ```

### Step 7: Sync and Summarize

1. **Run deepwork sync** (if instructions were modified)
   ```bash
   deepwork sync
   ```

2. **Create learning_summary.md** in the working folder:
   ```markdown
   # Learning Summary

   ## Job Analyzed
   - Job: [job_name]
   - Steps executed: [list of steps]

   ## Generalizable Improvements Made
   - [Step]: [What was improved]

   ## Bespoke Learnings Captured
   - Location: [path to AGENTS.md]
   - Entries added: [list of entries]

   ## Files Modified
   - [List of files changed]

   ## Recommendations
   - [Any additional suggestions]
   ```

3. **Instruct user to reload** if commands were regenerated

## File Reference Patterns

When adding entries to AGENTS.md, prefer these patterns:

**Good (references)**:
```markdown
- API endpoints follow REST conventions. See `src/api/routes.ts` for examples.
- Error handling pattern: See `src/utils/errors.ts:15-30`
- Configuration schema: Defined in `config/schema.json`
```

**Avoid (duplicating)**:
```markdown
- API endpoints should return JSON with this format: { status: ..., data: ... }
- Error handling should use try/catch with custom error classes
- Configuration requires these fields: name, version, ...
```

## Quality Criteria

- Conversation has been analyzed for job executions
- Points of confusion and inefficiency are identified
- Learnings are correctly classified (generalizable vs bespoke)
- Job instructions updated for generalizable improvements
- AGENTS.md created/updated with bespoke learnings
- File references used instead of duplicating content
- AGENTS.md is in the correct working folder
- learning_summary.md documents all changes
- When all criteria are met, include `<promise>✓ Quality Criteria Met</promise>`

## Example Dialog

```
User: /deepwork_jobs.learn

Claude: I'll analyze this conversation for learnings from DeepWork job executions.

**Conversation Analysis**

I found the following job executions:
1. `/competitive_research.identify_competitors` - Completed
2. `/competitive_research.research_competitors` - Completed with 2 iterations
3. `/competitive_research.comparative_analysis` - Completed

**Identified Issues**

1. **Confusion in step 2**: The instructions didn't specify that competitor research should include pricing information. This caused an extra iteration.

2. **Missing context**: The agent had to ask about the industry focus, which should have been carried forward from step 1.

**Classification**

- Generalizable: Add pricing to research requirements in instructions
- Bespoke: This project focuses on B2B SaaS in the HR tech space

**Actions Taken**

1. Updated `.deepwork/jobs/competitive_research/steps/research_competitors.md`:
   - Added "Include pricing information (tiers, models, approximate ranges)" to research requirements
   - Added note about carrying forward industry context from previous step

2. Created `./competitive_research_output/AGENTS.md`:
   ```markdown
   # Project Context for Competitive Research

   ## Job-Specific Context

   ### competitive_research

   #### Industry Focus
   - Domain: B2B SaaS, HR Technology sector
   - See `identify_competitors_output.md` for market definition

   #### Competitors Identified
   - Reference: `competitor_list.md` for full details

   ## Last Updated
   - Date: 2024-01-15
   - From conversation about: Initial competitive analysis run
   ```

3. Updated job.yml version to 1.0.1 with changelog entry

4. Ran `deepwork sync`

**Summary**

Created `learning_summary.md` documenting all changes. Please run `/reload` to get the updated commands.
```

## Handling Edge Cases

**No job executions found**:
- Ask user which job they'd like to analyze
- Or offer to review available jobs

**Multiple jobs executed**:
- Analyze each job separately
- Create separate AGENTS.md entries or files as appropriate

**AGENTS.md already exists**:
- Read existing content
- Append new learnings to appropriate sections
- Update "Last Updated" section

**No issues found**:
- Document what worked well
- Consider if any successful patterns should be added to instructions as examples

**Sensitive information**:
- Never include secrets, credentials, or PII in AGENTS.md
- Reference config files instead of including values


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
- `learning_summary.md`
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
4. **Bespoke Learnings Captured**: Were run-specific learnings added to AGENTS.md?
5. **File References Used**: Do AGENTS.md entries reference other files where appropriate?
6. **Working Folder Correct**: Is AGENTS.md in the correct working folder for the job?
7. **Generalizable Separated**: Are generalizable improvements in instructions, not AGENTS.md?
8. **Sync Complete**: Has `deepwork sync` been run if instructions were modified?

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
   - Outputs created: learning_summary.md
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