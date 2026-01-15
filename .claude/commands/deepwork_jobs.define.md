---
description: Create the job.yml specification file by understanding workflow requirements
hooks:
  Stop:
    - hooks:
        - type: prompt
          prompt: |
            You must evaluate whether Claude has met all the below quality criteria for the request.

            ## Quality Criteria

            Verify the job.yml output meets ALL quality criteria before completing:

            1. **User Understanding**: Did you fully understand the user's workflow through interactive Q&A?
            2. **Clear Inputs/Outputs**: Does every step have clearly defined inputs and outputs?
            3. **Logical Dependencies**: Do step dependencies make sense and avoid circular references?
            4. **Concise Summary**: Is the summary under 200 characters and descriptive?
            5. **Rich Description**: Does the description provide enough context for future refinement?
            6. **Valid Schema**: Does the job.yml follow the required schema (name, version, summary, steps)?
            7. **File Created**: Has the job.yml file been created in `.deepwork/jobs/[job_name]/job.yml`?

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

# deepwork_jobs.define

**Step 1 of 3** in the **deepwork_jobs** workflow

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

# Define Job Specification

## Objective

Create a `job.yml` specification file that defines the structure of a new DeepWork job by understanding the user's workflow requirements through interactive Q&A.

**Reference**: See `deepwork_jobs.md` for job.yml schema, validation rules, and templates.

## Task

Guide the user through defining a job specification by asking clarifying questions. **Do not create the specification without first fully understanding the user's needs.**

The output is **only** the `job.yml` file. Step instruction files are created in the `implement` step.

### Step 1: Understand the Job Purpose

Ask questions to understand the workflow:

1. **Overall goal** - What task? What domain? How often run?
2. **Success criteria** - Final deliverable? Audience? Quality criteria?
3. **Major phases** - High-level stages? Dependencies between phases?

### Step 2: Define Each Step

For each phase, gather:

1. **Purpose** - What does it accomplish? Input? Output?
2. **Inputs** - User parameters? Files from previous steps? Format?
3. **Outputs** - Files produced? Format? Location (filename/path)?
4. **Dependencies** - Which steps must complete first?
5. **Process** - Key activities? Quality checks?

### Capability Considerations

If any step requires browser automation (web scraping, form filling, research requiring website visits), ask what browser tools are available. For Claude Code users, **Claude in Chrome** is recommended.

### Step 3: Validate the Workflow

1. **Review** - Summarize workflow, show how outputs feed into next steps
2. **Check gaps** - Undefined inputs? Unused outputs? Circular dependencies?
3. **Confirm details** - Job name, summary (<200 chars), description, version (1.0.0)

### Step 4: Define Quality Validation (Stop Hooks)

For each step, consider if it needs quality validation loops. Ask:
- "Are there specific quality criteria for this step?"
- "Would you like the agent to validate its work before completing?"

Stop hooks are valuable for complex outputs, critical deliverables, or subjective quality criteria.

**Hook types**: `prompt` (inline), `prompt_file` (external file), `script` (programmatic)

### Step 5: Create the Job

1. **Create directory** using the script:
   ```bash
   .deepwork/jobs/deepwork_jobs/make_new_job.sh [job_name]
   ```

2. **Create job.yml** at `.deepwork/jobs/[job_name]/job.yml`

**Templates**: See `.deepwork/jobs/deepwork_jobs/templates/job.yml.template` and `job.yml.example`

## Example Dialog

```
Claude: What complex task or workflow are you trying to create?

User: Competitive research reports for my company

Claude: Let's dig into that:
1. Final deliverable - report, presentation, other?
2. Audience - team, executives, clients?
3. How comprehensive?

User: Written report for product team, analyzing 3-5 competitors.

Claude: What are the major phases?

User: 1. Identify competitors, 2. Research each, 3. Comparison analysis, 4. Positioning recommendations

Claude: For "Identify competitors":
1. What inputs do you need?
2. What should the output look like?

[continues gathering details for each step...]

Claude: Let me summarize the workflow:
**Job: competitive_research**
Step 1: identify_competitors → competitors_list.md
Step 2: research_competitors → research_notes.md
Step 3: comparative_analysis → comparison_matrix.md
Step 4: positioning_recommendations → positioning_report.md

Does this capture your workflow?

User: Yes!

[Creates job.yml]
```

## Output Format

### job.yml

Location: `.deepwork/jobs/[job_name]/job.yml`

After creating:
1. Inform user the specification is complete
2. Tell them to run `/deepwork_jobs.implement` next

## Quality Criteria

- User fully understands what job they're creating
- All steps have clear inputs and outputs
- Dependencies make logical sense
- Summary is concise (<200 chars) and descriptive
- Description provides rich context
- Valid YAML following the schema
- Ready for implementation step


## Inputs

### User Parameters

Please gather the following information from the user:
- **job_purpose**: What complex task or workflow are you trying to accomplish?


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
- `job.yml`
Ensure all outputs are:
- Well-formatted and complete
- Ready for review or use by subsequent steps

## Quality Validation Loop

This step uses an iterative quality validation loop. After completing your work, stop hook(s) will evaluate whether the outputs meet quality criteria. If criteria are not met, you will be prompted to continue refining.

### Quality Criteria
Verify the job.yml output meets ALL quality criteria before completing:

1. **User Understanding**: Did you fully understand the user's workflow through interactive Q&A?
2. **Clear Inputs/Outputs**: Does every step have clearly defined inputs and outputs?
3. **Logical Dependencies**: Do step dependencies make sense and avoid circular references?
4. **Concise Summary**: Is the summary under 200 characters and descriptive?
5. **Rich Description**: Does the description provide enough context for future refinement?
6. **Valid Schema**: Does the job.yml follow the required schema (name, version, summary, steps)?
7. **File Created**: Has the job.yml file been created in `.deepwork/jobs/[job_name]/job.yml`?

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
   - Step 1 of 3 is complete
   - Outputs created: job.yml
   - Ready to proceed to next step: `/deepwork_jobs.implement`

## Next Step

To continue the workflow, run:
```
/deepwork_jobs.implement
```

---

## Context Files

- Job definition: `.deepwork/jobs/deepwork_jobs/job.yml`
- Step instructions: `.deepwork/jobs/deepwork_jobs/steps/define.md`