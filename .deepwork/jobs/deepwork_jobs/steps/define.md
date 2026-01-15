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
