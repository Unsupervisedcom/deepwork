---
description: Create the job.yml specification file by understanding workflow requirements
---

# deepwork_jobs.define

**Step 1 of 3** in the **deepwork_jobs** workflow

**Summary**: DeepWork job management commands

## Job Overview

Core commands for managing DeepWork jobs. These commands help you define new multi-step
workflows and refine existing ones.

The `define` command guides you through an interactive process to create a new job by
asking detailed questions about your workflow, understanding each step's inputs and outputs,
and generating all necessary files.

The `refine` command helps you modify existing jobs safely by understanding what you want
to change, validating the impact, and ensuring consistency across your workflow.



## Instructions

# Define Job Specification

## Objective

Create a `job.yml` specification file that defines the structure of a new DeepWork job by thoroughly understanding the user's workflow requirements through an interactive question-and-answer process.

## Task

Guide the user through defining a job specification by asking clarifying questions. **Do not attempt to create the specification without first fully understanding the user's needs.**

The output of this step is **only** the `job.yml` file - a complete specification of the workflow. The actual step instruction files will be created in the next step (`implement`).

### Step 1: Understand the Job Purpose

Start by asking questions to understand what the user wants to accomplish:

1. **What is the overall goal of this workflow?**
   - What complex task are they trying to accomplish?
   - What domain is this in? (e.g., research, marketing, development, reporting)
   - How often will they run this workflow?

2. **What does success look like?**
   - What's the final deliverable or outcome?
   - Who is the audience for the output?
   - What quality criteria matter most?

3. **What are the major phases?**
   - Ask them to describe the workflow at a high level
   - What are the distinct stages from start to finish?
   - Are there any dependencies between phases?

### Step 2: Define Each Step

For each major phase they mentioned, ask detailed questions:

1. **Step Purpose**
   - What exactly does this step accomplish?
   - What is the input to this step?
   - What is the output from this step?

2. **Step Inputs**
   - What information is needed to start this step?
   - Does it need user-provided parameters? (e.g., topic, target audience)
   - Does it need files from previous steps?
   - What format should inputs be in?

3. **Step Outputs**
   - What files or artifacts does this step produce?
   - What format should the output be in? (markdown, YAML, JSON, etc.)
   - Where should each output be saved? (filename/path)
   - Should outputs be organized in subdirectories? (e.g., `reports/`, `data/`, `drafts/`)
   - Will other steps need this output?

4. **Step Dependencies**
   - Which previous steps must complete before this one?
   - Are there any ordering constraints?

5. **Step Process** (high-level understanding)
   - What are the key activities in this step?
   - Are there any quality checks or validation needed?
   - What makes a good vs. bad output for this step?

**Note**: You're gathering this information to understand what instructions will be needed, but you won't create the instruction files yet - that happens in the `implement` step.

### Step 3: Validate the Workflow

After gathering information about all steps:

1. **Review the flow**
   - Summarize the complete workflow
   - Show how outputs from one step feed into the next
   - Ask if anything is missing

2. **Check for gaps**
   - Are there any steps where the input isn't clearly defined?
   - Are there any outputs that aren't used by later steps?
   - Are there circular dependencies?

3. **Confirm details**
   - Job name (lowercase, underscores, descriptive)
   - Job summary (one clear sentence, max 200 chars)
   - Job description (detailed multi-line explanation)
   - Version number (start with 1.0.0)

### Step 4: Create the job.yml Specification

Only after you have complete understanding, create the `job.yml` file:

**File Location**: `deepwork/[job_name]/job.yml`

(Where `[job_name]` is the name of the NEW job you're creating, e.g., `deepwork/competitive_research/job.yml`)

**Format**:
```yaml
name: [job_name]
version: "1.0.0"
summary: "[Brief one-line summary of what this job accomplishes]"
description: |
  [Detailed multi-line description of the job's purpose, process, and goals.

  This should explain:
  - What problem this workflow solves
  - What the overall process looks like
  - What the end result will be
  - Who the intended users are
  - Any important context about the workflow]

changelog:
  - version: "1.0.0"
    changes: "Initial job creation"

steps:
  - id: [step_id]
    name: "[Step Name]"
    description: "[What this step does]"
    instructions_file: steps/[step_id].md
    inputs:
      - name: [param_name]
        description: "[What user needs to provide]"
      # OR for file inputs from previous steps:
      # - file: [filename_or_path]
      #   from_step: [previous_step_id]
    outputs:
      - [output_filename_or_path]  # e.g., "report.md" or "reports/analysis.md"
    dependencies: []  # List of step IDs that must complete first

  - id: [another_step]
    name: "[Another Step]"
    description: "[What this step does]"
    instructions_file: steps/[another_step].md
    inputs:
      - file: [output_filename_or_path]
        from_step: [step_id]
    outputs:
      - [another_output_path]
    dependencies:
      - [step_id]  # This step requires the previous step
```

**Important**:
- Use lowercase with underscores for job name and step IDs
- Ensure file inputs reference steps in dependencies
- No circular dependencies
- At least one output per step
- The `summary` should be concise (max 200 chars)
- The `description` should provide rich context for future refinement
- Include a `changelog` section with an initial entry for version 1.0.0

## Example Dialog

```
Claude: I'll help you define a new DeepWork job. Let's start by understanding what you're trying to accomplish.

What complex task or workflow are you trying to create? What's the overall goal?

User: I want to create competitive research reports for my company

Claude: Great! Let's dig into that. A few questions:

1. What's the final deliverable? Is it a written report, a presentation, or something else?
2. Who is the audience? Your team, executives, clients?
3. How comprehensive should these reports be?

User: It's a written report for our product team. Should be comprehensive - analyzing 3-5 competitors.

Claude: Perfect. Now let's think about the major phases of creating this report. What are the main stages you go through? For example:
- Identifying which competitors to analyze?
- Gathering information about them?
- Analyzing the data?
- Writing the report?

Or is your process different?

User: Yes, that's close. I would say:
1. Identify competitors
2. Research each one
3. Create comparison analysis
4. Write positioning recommendations

Claude: Excellent! Now let's define each step in detail. Starting with "Identify competitors":

1. What inputs do you need to start? Do you already have a market segment in mind, or do you need to specify that?
2. What should the output look like? A list of competitor names? More detailed?
3. How many competitors should be identified?

User: I need to specify the market segment and product category as inputs. The output should be a markdown file with 5-7 competitors and brief descriptions of each.

Claude: Perfect. A few more questions about that output:
1. What should the file be called? Something like `competitors_list.md`?
2. Should it go directly in the deepwork/competitive_research/ folder, or in a subdirectory like `research/` or `data/`?

User: Just call it `competitors_list.md` in the main folder.

Claude: Great. Now for the "Research each one" step:
1. Does it use the competitor list from the first step as input?
2. What kind of research - product features, pricing, marketing, all of the above?
3. What format should the research output be in?
4. Where should that research be saved?

[continues for each step...]

[After gathering all information:]

Claude: Let me summarize the workflow I've designed based on our conversation:

**Job: competitive_research**
Summary: Systematic competitive analysis workflow for product positioning

Description:
A comprehensive workflow for analyzing competitors in your market segment. This job helps product teams understand the competitive landscape by systematically identifying competitors, researching their offerings, creating comparison matrices, and developing strategic positioning recommendations.

The workflow produces:
- A vetted list of key competitors
- Detailed research notes on each competitor
- A comparison matrix highlighting key differentiators
- Strategic positioning recommendations

Designed for product teams conducting quarterly competitive analysis.

**Steps:**

Step 1: identify_competitors
- Input: market_segment (user), product_category (user)
- Output: competitors_list.md (5-7 competitors with descriptions)

Step 2: research_competitors
- Input: competitors_list.md (from step 1)
- Output: research_notes.md (detailed findings for each competitor)
- Depends on: identify_competitors

Step 3: comparative_analysis
- Input: research_notes.md (from step 2)
- Output: comparison_matrix.md (side-by-side analysis)
- Depends on: research_competitors

Step 4: positioning_recommendations
- Input: comparison_matrix.md (from step 3)
- Output: positioning_report.md (strategic recommendations)
- Depends on: comparative_analysis

Does this accurately capture your workflow? Any changes needed?

User: Yes, that's perfect!

Claude: Great! Creating the job.yml specification now...

[Creates deepwork/competitive_research/job.yml with the complete spec]

✓ Job specification created!

**File created:**
- deepwork/competitive_research/job.yml

**Next step:**
Run `/deepwork_jobs.implement` to generate the instruction files for each step based on this specification.
```

## Important Guidelines

1. **Focus on specification only** - Don't create instruction files yet
2. **Ask clarifying questions** - Never skip the discovery phase
3. **Rich context in description** - This helps with future refinement
4. **Validate understanding** - Summarize and confirm before creating
5. **Use examples** - Help users understand what good specifications look like
6. **Understand file organization** - Always ask where outputs should be saved and if subdirectories are needed

## Validation Rules

Before creating the job.yml, ensure:
- Job name: lowercase, underscores, no spaces
- Version: semantic versioning (1.0.0)
- Summary: concise, under 200 characters
- Description: detailed, provides context
- Step IDs: unique, descriptive, lowercase with underscores
- Dependencies: must reference existing step IDs
- File inputs: `from_step` must be in dependencies
- At least one output per step
- Outputs can be filenames (e.g., `report.md`) or paths (e.g., `reports/analysis.md`)
- File paths in outputs should match where files will actually be created
- No circular dependencies

## Output Format

### job.yml

The complete YAML specification file (example shown in Step 4 above).

**Location**: `deepwork/[job_name]/job.yml`

(Where `[job_name]` is the name of the new job being created)

After creating the file:
1. Inform the user that the specification is complete
2. Recommend that they review the job.yml file
3. Tell them to run `/deepwork_jobs.implement` next

## Quality Criteria

- User fully understands what job they're creating
- All steps have clear inputs and outputs
- Dependencies make logical sense
- Summary is concise and descriptive
- Description provides rich context for future refinement
- Specification is valid YAML and follows the schema
- Ready for implementation step
- Output artifacts have quality criteria defined


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

3. **All outputs go in the work directory**:
   - Create files in: `deepwork/deepwork_jobs/`
   - This keeps work products organized by job

## Output Requirements

Create the following output(s) in the work directory:
- `deepwork/deepwork_jobs/job.yml`
Ensure all outputs are:
- Well-formatted and complete
- Ready for review or use by subsequent steps

## Completion

After completing this step:

1. **Verify outputs**: Confirm all required files have been created

2. **Inform the user**:
   - Step 1 of 2 is complete
   - Outputs created: job.yml
   - They should review the job.yml file before proceeding
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