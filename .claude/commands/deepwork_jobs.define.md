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

### Step 4: Define Quality Validation (Stop Hooks)

For each step, consider whether it would benefit from **quality validation loops**. Stop hooks allow the AI agent to iteratively refine its work until quality criteria are met.

**Ask the user about quality validation:**
- "Are there specific quality criteria that must be met for this step?"
- "Would you like the agent to validate its work before completing?"
- "What would make you send the work back for revision?"

**Stop hooks are particularly valuable for:**
- Steps with complex outputs that need multiple checks
- Steps where quality is critical (final deliverables)
- Steps with subjective quality criteria that benefit from AI self-review

**Three types of stop hooks are supported:**

1. **Inline Prompt** (`prompt`) - Best for simple quality criteria
   ```yaml
   stop_hooks:
     - prompt: |
         Verify the output meets these criteria:
         1. Contains at least 5 competitors
         2. Each competitor has a description
         3. Selection rationale is clear
   ```

2. **Prompt File** (`prompt_file`) - For detailed/reusable criteria
   ```yaml
   stop_hooks:
     - prompt_file: hooks/quality_check.md
   ```

3. **Script** (`script`) - For programmatic validation (tests, linting)
   ```yaml
   stop_hooks:
     - script: hooks/run_tests.sh
   ```

**Multiple hooks can be combined:**
```yaml
stop_hooks:
  - script: hooks/lint_output.sh
  - prompt: "Verify the content is comprehensive and well-organized"
```

**Encourage prompt-based hooks** - They leverage the AI's ability to understand context and make nuanced quality judgments. Script hooks are best for objective checks (syntax, format, tests).

### Step 5: Create the job.yml Specification

Only after you have complete understanding, create the `job.yml` file:

**File Location**: `.deepwork/jobs/[job_name]/job.yml`

(Where `[job_name]` is the name of the NEW job you're creating, e.g., `.deepwork/jobs/competitive_research/job.yml`)

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
    # Optional: Quality validation hooks
    stop_hooks:
      - prompt: |
          Verify this step's output meets quality criteria:
          1. [Criterion 1]
          2. [Criterion 2]
          If ALL criteria are met, include `<promise>✓ Quality Criteria Met</promise>`.

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
2. Should it go in the project root, or in a subdirectory like `research/` or `data/`?

User: Just call it `competitors_list.md` in the project root.

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

[Creates .deepwork/jobs/competitive_research/job.yml with the complete spec]

✓ Job specification created!

**File created:**
- .deepwork/jobs/competitive_research/job.yml

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

The complete YAML specification file (example shown in Step 5 above).

**Location**: `.deepwork/jobs/[job_name]/job.yml`

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