---
name: deepwork_jobs
description: "Creates and manages multi-step AI workflows. Use when defining, implementing, or improving DeepWork jobs."
---

# deepwork_jobs Agent

Creates and manages multi-step AI workflows. Use when defining, implementing, or improving DeepWork jobs.

Core commands for managing DeepWork jobs. These commands help you define new multi-step
workflows and learn from running them.

The `new_job` workflow guides you through defining and implementing a new job by
asking structured questions about your workflow, understanding each step's inputs and outputs,
reviewing the specification, and generating all necessary files.

The `learn` skill reflects on conversations where DeepWork jobs were run, identifies
confusion or inefficiencies, and improves job instructions. It also captures bespoke
learnings specific to the current run into AGENTS.md files in the working folder.


## Agent Overview

This agent handles the **deepwork_jobs** job with 4 skills.

**Workflows**: new_job
**Standalone Skills**: learn
---

## How to Use This Agent

### Workflows
- **new_job**: Create a new DeepWork job from scratch through definition, review, and implementation (define → review_job_spec → implement)
  - Start: `define`

### Standalone Skills (run anytime)
- **learn**: Analyzes conversation history to improve job instructions and capture learnings. Use after running a job to refine it.

### All Skills
- `define` - Creates a job.yml specification by gathering workflow requirements through structured questions. Use when starting a new multi-step workflow.
- `review_job_spec` - Reviews job.yml against quality criteria using a sub-agent for unbiased validation. Use after defining a job specification.
- `implement` - Generates step instruction files and syncs slash commands from the job.yml specification. Use after job spec review passes.
- `learn` - Analyzes conversation history to improve job instructions and capture learnings. Use after running a job to refine it.

---

## Agent Execution Instructions

When invoked, follow these steps:

### Step 1: Understand Intent

Parse the user's request to determine:
1. Which workflow or skill to execute
2. Any parameters or context provided
3. Whether this is a continuation of previous work

### Step 2: Check Work Branch

Before executing any skill:
1. Check current git branch
2. If on a `deepwork/deepwork_jobs-*` branch: continue using it
3. If on main/master: create new branch `deepwork/deepwork_jobs-[instance]-$(date +%Y%m%d)`

### Step 3: Execute the Appropriate Skill

Navigate to the relevant skill section below and follow its instructions.

### Step 4: Workflow Continuation

After completing a workflow step:
1. Inform the user of completion and outputs created
2. Automatically proceed to the next step if one exists
3. Continue until the workflow is complete or the user intervenes

---

## Skills

### Skill: define

**Type**: Workflow step 1/3 in **new_job**

**Description**: Creates a job.yml specification by gathering workflow requirements through structured questions. Use when starting a new multi-step workflow.


#### Required User Input

Gather these from the user before starting:
- **job_purpose**: What complex task or workflow are you trying to accomplish?


#### Instructions

# Define Job Specification

## Objective

Create a `job.yml` specification file that defines the structure of a new DeepWork job by thoroughly understanding the user's workflow requirements through an interactive question-and-answer process.

## Task

Guide the user through defining a job specification by asking structured questions. **Do not attempt to create the specification without first fully understanding the user's needs.**

**Important**: Use the AskUserQuestion tool to ask structured questions when gathering information from the user. This provides a better user experience with clear options and guided choices.

The output of this step is **only** the `job.yml` file - a complete specification of the workflow. The actual step instruction files will be created in the next step (`implement`).

### Step 1: Understand the Job Purpose

Start by asking structured questions to understand what the user wants to accomplish:

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

### Step 1.5: Detect Document-Oriented Workflows

**Check for document-focused patterns** in the user's description:
- Keywords: "report", "summary", "document", "create", "monthly", "quarterly", "for stakeholders", "for leadership"
- Final deliverable is a specific document (e.g., "AWS spending report", "competitive analysis", "sprint summary")
- Recurring documents with consistent structure

**If a document-oriented workflow is detected:**

1. Inform the user: "This workflow produces a specific document type. I recommend defining a doc spec first to ensure consistent quality."

2. Ask structured questions to understand if they want to:
   - Create a doc spec for this document
   - Use an existing doc spec (if any exist in `.deepwork/doc_specs/`)
   - Skip doc spec and proceed with simple outputs

### Step 1.6: Define the Doc Spec (if needed)

When creating a doc spec, gather the following information:

1. **Document Identity**
   - What is the document called? (e.g., "Monthly AWS Spending Report")
   - Brief description of its purpose
   - Where should these documents be stored? (path patterns like `finance/aws-reports/*.md`)

2. **Audience and Context**
   - Who reads this document? (target audience)
   - How often is it produced? (frequency)

3. **Quality Criteria** (3-5 criteria, each with name and description)
   Examples for a spending report:
   - **Visualization**: Must include charts showing spend breakdown by service
   - **Variance Analysis**: Must compare current month against previous with percentages
   - **Action Items**: Must include recommended cost optimization actions

4. **Document Structure**
   - What sections should it have?
   - Any required elements (tables, charts, summaries)?

### Step 1.7: Create the doc spec File (if needed)

Create the doc spec file at `.deepwork/doc_specs/[doc_spec_name].md`:

**Template reference**: See `.deepwork/jobs/deepwork_jobs/templates/doc_spec.md.template` for the standard structure.

**Complete example**: See `.deepwork/jobs/deepwork_jobs/templates/doc_spec.md.example` for a fully worked example.

After creating the doc spec, proceed to Step 2 with the doc spec reference for the final step's output.

### Step 2: Define Each Step

For each major phase they mentioned, ask structured questions to gather details:

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

   **Important**: Output paths should always be within the main repository directory structure, not in dot-directories like `.deepwork/`. Dot-directories are for configuration and job definitions, not for job outputs. Use paths like `research/competitors/report.md` rather than `.deepwork/outputs/report.md`.
   - **Does this output have a doc spec?** If a doc spec was created in Step 1.6/1.7, reference it for the appropriate output

4. **Step Dependencies**
   - Which previous steps must complete before this one?
   - Are there any ordering constraints?

5. **Step Process** (high-level understanding)
   - What are the key activities in this step?
   - Are there any quality checks or validation needed?
   - What makes a good vs. bad output for this step?

**Note**: You're gathering this information to understand what instructions will be needed, but you won't create the instruction files yet - that happens in the `implement` step.

#### Doc Spec-Aware Output Format

When a step produces a document with a doc spec reference, use this format in job.yml:

```yaml
outputs:
  - file: reports/monthly_spending.md
    doc_spec: .deepwork/doc_specs/monthly_aws_report.md
```

The doc spec's quality criteria will automatically be included in the generated skill, ensuring consistent document quality.

### Capability Considerations

When defining steps, identify any that require specialized tools:

**Browser Automation**: If any step involves web scraping, form filling, interactive browsing, UI testing, or research requiring website visits, ask the user what browser tools they have available. For Claude Code users, **Claude in Chrome** (Anthropic's browser extension) has been tested with DeepWork and is recommended for new users. Don't assume a default—confirm the tool before designing browser-dependent steps.

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

**Ask structured questions about quality validation:**
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

### Step 5: Create the Job Directory and Specification

Only after you have complete understanding, create the job directory and `job.yml` file:

**First, create the directory structure** using the `make_new_job.sh` script:

```bash
.deepwork/jobs/deepwork_jobs/make_new_job.sh [job_name]
```

This creates:
- `.deepwork/jobs/[job_name]/` - Main job directory
- `.deepwork/jobs/[job_name]/steps/` - For step instruction files
- `.deepwork/jobs/[job_name]/hooks/` - For custom validation scripts
- `.deepwork/jobs/[job_name]/templates/` - For example file formats
- `.deepwork/jobs/[job_name]/AGENTS.md` - Job management guidance

**Then create the job.yml file** at `.deepwork/jobs/[job_name]/job.yml`

(Where `[job_name]` is the name of the NEW job you're creating, e.g., `competitive_research`)

**Doc Spec**: See `.deepwork/doc_specs/job_spec.md` for the complete specification with quality criteria.

**Template reference**: See `.deepwork/jobs/deepwork_jobs/templates/job.yml.template` for the standard structure.

**Complete example**: See `.deepwork/jobs/deepwork_jobs/templates/job.yml.example` for a fully worked example.

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
Run `/deepwork_jobs.review_job_spec` to validate the specification against quality criteria.
```

## Important Guidelines

1. **Focus on specification only** - Don't create instruction files yet
2. **Ask structured questions** - Never skip the discovery phase; use the AskUserQuestion tool
3. **Rich context in description** - This helps with future refinement
4. **Validate understanding** - Summarize and confirm before creating
5. **Use examples** - Help users understand what good specifications look like
6. **Understand file organization** - Always ask structured questions about where outputs should be saved and if subdirectories are needed

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
3. Tell them to run `/deepwork_jobs.review_job_spec` next

## Quality Criteria

- Asked structured questions to fully understand user requirements
- User fully understands what job they're creating
- All steps have clear inputs and outputs
- Dependencies make logical sense
- Summary is concise and descriptive
- Description provides rich context for future refinement
- Specification is valid YAML and follows the schema
- Ready for implementation step


#### Outputs

Create these files/directories:
- `job.yml`
  **Doc Spec**: DeepWork Job Specification
  > YAML specification file that defines a multi-step workflow job for AI agents
  **Quality Criteria**:
  - **Valid Identifier**: Job name must be lowercase with underscores, no spaces or special characters (e.g., `competitive_research`, `monthly_report`)
  - **Semantic Version**: Version must follow semantic versioning format X.Y.Z (e.g., `1.0.0`, `2.1.3`)
  - **Concise Summary**: Summary must be under 200 characters and clearly describe what the job accomplishes
  - **Rich Description**: Description must be multi-line and explain: the problem solved, the process, expected outcomes, and target users
  - **Changelog Present**: Must include a changelog array with at least the initial version entry. Changelog should only include one entry per branch at most
  - **Complete Steps**: Each step must have: id (lowercase_underscores), name, description, instructions_file, outputs (at least one), and dependencies array
  - **Valid Dependencies**: Dependencies must reference existing step IDs with no circular references
  - **Input Consistency**: File inputs with `from_step` must reference a step that is in the dependencies array
  - **Output Paths**: Outputs must be valid filenames or paths within the main repo (not in dot-directories). Use specific, descriptive paths that lend themselves to glob patterns, e.g., `competitive_research/competitors_list.md` or `competitive_research/[competitor_name]/research.md`. Avoid generic names like `output.md`.
  - **Concise Instructions**: The content of the file, particularly the description, must not have excessively redundant information. It should be concise and to the point given that extra tokens will confuse the AI.

#### Quality Validation

Before completing this skill, verify:
1. **User Understanding**: Did the agent fully understand the user's workflow by asking structured questions?
2. **Structured Questions Used**: Did the agent ask structured questions (using the AskUserQuestion tool) to gather user input?
3. **Document Detection**: For document-oriented workflows, did the agent detect patterns and offer doc spec creation?
4. **doc spec Created (if applicable)**: If a doc spec was needed, was it created in `.deepwork/doc_specs/[doc_spec_name].md` with proper quality criteria?
5. **doc spec References**: Are document outputs properly linked to their doc specs using `{file, doc_spec}` format?
6. **Valid Against doc spec**: Does the job.yml conform to the job.yml doc spec quality criteria (valid identifier, semantic version, concise summary, rich description, complete steps, valid dependencies)?
7. **Clear Inputs/Outputs**: Does every step have clearly defined inputs and outputs?
8. **Logical Dependencies**: Do step dependencies make sense and avoid circular references?
9. **Concise Summary**: Is the summary under 200 characters and descriptive?
10. **Rich Description**: Does the description provide enough context for future refinement?
11. **Valid Schema**: Does the job.yml follow the required schema (name, version, summary, steps)?
12. **File Created**: Has the job.yml file been created in `.deepwork/jobs/[job_name]/job.yml`?

Use a sub-agent (Haiku model) to review your work against these criteria before marking complete.

#### On Completion

1. Verify outputs are created
2. Inform user: "define complete, outputs: job.yml"
3. **Continue to next skill**: Proceed to `review_job_spec`

---

### Skill: review_job_spec

**Type**: Workflow step 2/3 in **new_job**

**Description**: Reviews job.yml against quality criteria using a sub-agent for unbiased validation. Use after defining a job specification.

#### Prerequisites

Before running this skill, ensure these are complete:
- `define`


#### Input Files

Read these files (from previous steps):
- `job.yml` (from `define`)

#### Instructions

# Review Job Specification

## Objective

Review the `job.yml` created in the define step against the doc spec quality criteria using a sub-agent for unbiased evaluation, then iterate on fixes until all criteria pass.

## Why This Step Exists

The define step focuses on understanding user requirements and creating a job specification. This review step ensures the specification meets quality standards before implementation. Using a sub-agent provides an unbiased "fresh eyes" review that catches issues the main agent might miss after being deeply involved in the definition process.

## Task

Use a sub-agent to review the job.yml against all 9 doc spec quality criteria, then fix any failed criteria. Repeat until all criteria pass.

### Step 1: Read the Job Specification

Read the `job.yml` file created in the define step:

```
.deepwork/jobs/[job_name]/job.yml
```

Also read the doc spec for reference:

```
.deepwork/doc_specs/job_spec.md
```

### Step 2: Spawn Review Sub-Agent

Use the Task tool to spawn a sub-agent that will provide an unbiased review:

```
Task tool parameters:
- subagent_type: "general-purpose"
- model: "haiku"
- description: "Review job.yml against doc spec"
- prompt: [see below]
```

**Sub-agent prompt template:**

```
Review this job.yml against the following 9 quality criteria from the doc spec.

For each criterion, respond with:
- PASS or FAIL
- If FAIL: specific issue and suggested fix

## job.yml Content

[paste the full job.yml content here]

## Quality Criteria

1. **Valid Identifier**: Job name must be lowercase with underscores, no spaces or special characters (e.g., `competitive_research`, `monthly_report`)

2. **Semantic Version**: Version must follow semantic versioning format X.Y.Z (e.g., `1.0.0`, `2.1.3`)

3. **Concise Summary**: Summary must be under 200 characters and clearly describe what the job accomplishes

4. **Rich Description**: Description must be multi-line and explain: the problem solved, the process, expected outcomes, and target users

5. **Changelog Present**: Must include a changelog array with at least the initial version entry

6. **Complete Steps**: Each step must have: id (lowercase_underscores), name, description, instructions_file, outputs (at least one), and dependencies array

7. **Valid Dependencies**: Dependencies must reference existing step IDs with no circular references

8. **Input Consistency**: File inputs with `from_step` must reference a step that is in the dependencies array

9. **Output Paths**: Outputs must be valid filenames or paths (e.g., `report.md` or `reports/analysis.md`)

## Response Format

Respond with a structured evaluation:

### Overall: [X/9 PASS]

### Criterion Results

1. Valid Identifier: [PASS/FAIL]
   [If FAIL: Issue and fix]

2. Semantic Version: [PASS/FAIL]
   [If FAIL: Issue and fix]

[... continue for all 9 criteria ...]

### Summary of Required Fixes

[List any fixes needed, or "No fixes required - all criteria pass"]
```

### Step 3: Review Sub-Agent Findings

Parse the sub-agent's response:

1. **Count passing criteria** - How many of the 9 criteria passed?
2. **Identify failures** - List specific criteria that failed
3. **Note suggested fixes** - What changes does the sub-agent recommend?

### Step 4: Fix Failed Criteria

For each failed criterion, edit the job.yml to address the issue:

**Common fixes by criterion:**

| Criterion | Common Issue | Fix |
|-----------|-------------|-----|
| Valid Identifier | Spaces or uppercase | Convert to lowercase_underscores |
| Semantic Version | Missing or invalid format | Set to `"1.0.0"` or fix format |
| Concise Summary | Too long or vague | Shorten to <200 chars, be specific |
| Rich Description | Single line or missing context | Add multi-line explanation with problem/process/outcome/users |
| Changelog Present | Missing changelog | Add `changelog:` with initial version entry |
| Complete Steps | Missing required fields | Add id, name, description, instructions_file, outputs, dependencies |
| Valid Dependencies | Non-existent step or circular | Fix step ID reference or reorder dependencies |
| Input Consistency | from_step not in dependencies | Add the referenced step to dependencies array |
| Output Paths | Invalid characters or format | Use valid filename/path format |

### Step 5: Re-Run Review (If Needed)

If any criteria failed:

1. **Spawn a new sub-agent** with the updated job.yml content
2. **Review the new findings**
3. **Fix any remaining issues**
4. **Repeat until all 9 criteria pass**

### Step 6: Confirm Completion

When all 9 criteria pass:

1. **Announce success**: "All 9 doc spec quality criteria pass."
2. **List what was validated**:
   - Valid Identifier
   - Semantic Version
   - Concise Summary
   - Rich Description
   - Changelog Present
   - Complete Steps
   - Valid Dependencies
   - Input Consistency
   - Output Paths
3. **Include the promise**: `<promise>Quality Criteria Met</promise>`
4. **Guide to next step**: "Run `/deepwork_jobs.implement` to generate the step instruction files."

## Example Review Cycle

```
Claude: Let me review the job.yml against the doc spec quality criteria.

[Spawns sub-agent with haiku model]

Sub-agent response:
### Overall: 7/9 PASS

### Criterion Results
1. Valid Identifier: PASS
2. Semantic Version: PASS
3. Concise Summary: FAIL
   Issue: Summary is 245 characters, exceeds 200 char limit
   Fix: Shorten to "Competitive analysis workflow for product positioning"
4. Rich Description: PASS
5. Changelog Present: FAIL
   Issue: No changelog array present
   Fix: Add changelog with initial version entry
6. Complete Steps: PASS
7. Valid Dependencies: PASS
8. Input Consistency: PASS
9. Output Paths: PASS

### Summary of Required Fixes
1. Shorten summary to under 200 characters
2. Add changelog array with initial version

Claude: I found 2 issues. Let me fix them.

[Edits job.yml to shorten summary and add changelog]

Claude: Let me verify the fixes with another review.

[Spawns new sub-agent]

Sub-agent response:
### Overall: 9/9 PASS

### Summary of Required Fixes
No fixes required - all criteria pass

Claude: All 9 doc spec quality criteria pass.

<promise>Quality Criteria Met</promise>

**Next step:** Run `/deepwork_jobs.implement` to generate the step instruction files.
```

## Quality Criteria

- **Sub-Agent Used**: A sub-agent was spawned to provide unbiased review (not just self-review)
- **All doc spec Criteria Evaluated**: The sub-agent assessed all 9 quality criteria from the doc spec
- **Findings Addressed**: All failed criteria were fixed by the main agent
- **Validation Loop Complete**: The review-fix cycle continued until all criteria passed
- **Promise Included**: The response includes `<promise>Quality Criteria Met</promise>` when complete

## Output

The validated `job.yml` file at `.deepwork/jobs/[job_name]/job.yml` that passes all 9 doc spec quality criteria.


#### Outputs

Create these files/directories:
- `job.yml`
  **Doc Spec**: DeepWork Job Specification
  > YAML specification file that defines a multi-step workflow job for AI agents
  **Quality Criteria**:
  - **Valid Identifier**: Job name must be lowercase with underscores, no spaces or special characters (e.g., `competitive_research`, `monthly_report`)
  - **Semantic Version**: Version must follow semantic versioning format X.Y.Z (e.g., `1.0.0`, `2.1.3`)
  - **Concise Summary**: Summary must be under 200 characters and clearly describe what the job accomplishes
  - **Rich Description**: Description must be multi-line and explain: the problem solved, the process, expected outcomes, and target users
  - **Changelog Present**: Must include a changelog array with at least the initial version entry. Changelog should only include one entry per branch at most
  - **Complete Steps**: Each step must have: id (lowercase_underscores), name, description, instructions_file, outputs (at least one), and dependencies array
  - **Valid Dependencies**: Dependencies must reference existing step IDs with no circular references
  - **Input Consistency**: File inputs with `from_step` must reference a step that is in the dependencies array
  - **Output Paths**: Outputs must be valid filenames or paths within the main repo (not in dot-directories). Use specific, descriptive paths that lend themselves to glob patterns, e.g., `competitive_research/competitors_list.md` or `competitive_research/[competitor_name]/research.md`. Avoid generic names like `output.md`.
  - **Concise Instructions**: The content of the file, particularly the description, must not have excessively redundant information. It should be concise and to the point given that extra tokens will confuse the AI.

#### Quality Validation

Before completing this skill, verify:
1. **Sub-Agent Used**: Was a sub-agent spawned to provide unbiased review?
2. **All doc spec Criteria Evaluated**: Did the sub-agent assess all 9 quality criteria?
3. **Findings Addressed**: Were all failed criteria addressed by the main agent?
4. **Validation Loop Complete**: Did the review-fix cycle continue until all criteria passed?

Use a sub-agent (Haiku model) to review your work against these criteria before marking complete.

#### On Completion

1. Verify outputs are created
2. Inform user: "review_job_spec complete, outputs: job.yml"
3. **Continue to next skill**: Proceed to `implement`

---

### Skill: implement

**Type**: Workflow step 3/3 in **new_job**

**Description**: Generates step instruction files and syncs slash commands from the job.yml specification. Use after job spec review passes.

#### Prerequisites

Before running this skill, ensure these are complete:
- `review_job_spec`


#### Input Files

Read these files (from previous steps):
- `job.yml` (from `review_job_spec`)

#### Instructions

# Implement Job Steps

## Objective

Generate the DeepWork job directory structure and instruction files for each step based on the validated `job.yml` specification from the review_job_spec step.

## Task

Read the `job.yml` specification file and create all the necessary files to make the job functional, including directory structure and step instruction files. Then sync the commands to make them available.

### Step 1: Create Directory Structure Using Script

Run the `make_new_job.sh` script to create the standard directory structure:

```bash
.deepwork/jobs/deepwork_jobs/make_new_job.sh [job_name]
```

This creates:
- `.deepwork/jobs/[job_name]/` - Main job directory
- `.deepwork/jobs/[job_name]/steps/` - Step instruction files
- `.deepwork/jobs/[job_name]/hooks/` - Custom validation scripts (with .gitkeep)
- `.deepwork/jobs/[job_name]/templates/` - Example file formats (with .gitkeep)
- `.deepwork/jobs/[job_name]/AGENTS.md` - Job management guidance

**Note**: If the directory already exists (e.g., job.yml was created by define step), you can skip this step or manually create the additional directories:
```bash
mkdir -p .deepwork/jobs/[job_name]/hooks .deepwork/jobs/[job_name]/templates
touch .deepwork/jobs/[job_name]/hooks/.gitkeep .deepwork/jobs/[job_name]/templates/.gitkeep
```

### Step 2: Read and Validate the Specification

1. **Locate the job.yml file**
   - Read `.deepwork/jobs/[job_name]/job.yml` from the review_job_spec step
   - Parse the YAML content

2. **Validate the specification**
   - Ensure it follows the schema (name, version, summary, description, steps)
   - Check that all dependencies reference existing steps
   - Verify no circular dependencies
   - Confirm file inputs match dependencies

3. **Extract key information**
   - Job name, version, summary, description
   - List of all steps with their details
   - Understand the workflow structure

### Step 3: Generate Step Instruction Files

For each step in the job.yml, create a comprehensive instruction file at `.deepwork/jobs/[job_name]/steps/[step_id].md`.

**Template reference**: See `.deepwork/jobs/deepwork_jobs/templates/step_instruction.md.template` for the standard structure.

**Complete example**: See `.deepwork/jobs/deepwork_jobs/templates/step_instruction.md.example` for a fully worked example.

**Available templates in `.deepwork/jobs/deepwork_jobs/templates/`:**
- `job.yml.template` - Job specification structure
- `step_instruction.md.template` - Step instruction file structure
- `agents.md.template` - AGENTS.md file structure
- `job.yml.example` - Complete job specification example
- `step_instruction.md.example` - Complete step instruction example

**Guidelines for generating instructions:**

1. **Use the job description** - The detailed description from job.yml provides crucial context
2. **Be specific** - Don't write generic instructions; tailor them to the step's purpose
3. **Provide examples** - Show what good output looks like
4. **Explain the "why"** - Help the user understand the step's role in the workflow
5. **Quality over quantity** - Detailed, actionable instructions are better than vague ones
6. **Align with stop hooks** - If the step has `stop_hooks` defined, ensure the quality criteria in the instruction file match the validation criteria in the hooks
7. **Ask structured questions** - When a step has user inputs, the instructions MUST explicitly tell the agent to "ask structured questions" using the AskUserQuestion tool to gather that information. Never use generic phrasing like "ask the user" - always use "ask structured questions"

### Handling Stop Hooks

If a step in the job.yml has `stop_hooks` defined, the generated instruction file should:

1. **Mirror the quality criteria** - The "Quality Criteria" section should match what the stop hooks will validate
2. **Be explicit about success** - Help the agent understand when the step is truly complete
3. **Include the promise pattern** - Mention that `<promise>✓ Quality Criteria Met</promise>` should be included when criteria are met

**Example: If the job.yml has:**
```yaml
- id: research_competitors
  name: "Research Competitors"
  stop_hooks:
    - prompt: |
        Verify the research meets criteria:
        1. Each competitor has at least 3 data points
        2. Sources are cited
        3. Information is current (within last year)
```

**The instruction file should include:**
```markdown
## Quality Criteria

- Each competitor has at least 3 distinct data points
- All information is sourced with citations
- Data is current (from within the last year)
- When all criteria are met, include `<promise>✓ Quality Criteria Met</promise>` in your response
```

This alignment ensures the AI agent knows exactly what will be validated and can self-check before completing.

### Using Supplementary Reference Files

Step instructions can include additional `.md` files in the `steps/` directory for detailed examples, templates, or reference material. Reference them using the full path from the project root.

See `.deepwork/jobs/deepwork_jobs/steps/supplemental_file_references.md` for detailed documentation and examples.

### Step 4: Verify job.yml Location

Verify that `job.yml` is in the correct location at `.deepwork/jobs/[job_name]/job.yml`. The define and review_job_spec steps should have created and validated it. If for some reason it's not there, you may need to create or move it.

### Step 5: Sync Skills

Run `deepwork sync` to generate the skills for this job:

```bash
deepwork sync
```

This will:
- Parse the job definition
- Generate skills for each step
- Make the skills available in `.claude/skills/` (or appropriate platform directory)

### Step 6: Relay Reload Instructions

After running `deepwork sync`, look at the "To use the new skills" section in the output. **Relay these exact reload instructions to the user** so they know how to pick up the new skills. Don't just reference the sync output - tell them directly what they need to do (e.g., "Type 'exit' then run 'claude --resume'" for Claude Code, or "Run '/memory refresh'" for Gemini CLI).

### Step 7: Consider Rules for the New Job

After implementing the job, consider whether there are **rules** that would help enforce quality or consistency when working with this job's domain.

**What are rules?**

Rules are automated guardrails stored as markdown files in `.deepwork/rules/` that trigger when certain files change during an AI session. They help ensure:
- Documentation stays in sync with code
- Team guidelines are followed
- Architectural decisions are respected
- Quality standards are maintained

**When to suggest rules:**

Think about the job you just implemented and ask:
- Does this job produce outputs that other files depend on?
- Are there documentation files that should be updated when this job's outputs change?
- Are there quality checks or reviews that should happen when certain files in this domain change?
- Could changes to the job's output files impact other parts of the project?

**Examples of rules that might make sense:**

| Job Type | Potential Rule |
|----------|----------------|
| API Design | "Update API docs when endpoint definitions change" |
| Database Schema | "Review migrations when schema files change" |
| Competitive Research | "Update strategy docs when competitor analysis changes" |
| Feature Development | "Update changelog when feature files change" |
| Configuration Management | "Update install guide when config files change" |

**How to offer rule creation:**

If you identify one or more rules that would benefit the user, explain:
1. **What the rule would do** - What triggers it and what action it prompts
2. **Why it would help** - How it prevents common mistakes or keeps things in sync
3. **What files it would watch** - The trigger patterns

Then ask the user:

> "Would you like me to create this rule for you? I can run `/deepwork_rules.define` to set it up."

If the user agrees, invoke the `/deepwork_rules.define` command to guide them through creating the rule.

**Example dialogue:**

```
Based on the competitive_research job you just created, I noticed that when
competitor analysis files change, it would be helpful to remind you to update
your strategy documentation.

I'd suggest a rule like:
- **Name**: "Update strategy when competitor analysis changes"
- **Trigger**: `**/positioning_report.md`
- **Action**: Prompt to review and update `docs/strategy.md`

Would you like me to create this rule? I can run `/deepwork_rules.define` to set it up.
```

**Note:** Not every job needs rules. Only suggest them when they would genuinely help maintain consistency or quality. Don't force rules where they don't make sense.

## Example Implementation

For a complete worked example showing a job.yml and corresponding step instruction file, see:
- **Job specification**: `.deepwork/jobs/deepwork_jobs/templates/job.yml.example`
- **Step instruction**: `.deepwork/jobs/deepwork_jobs/templates/step_instruction.md.example`

## Important Guidelines

1. **Read the spec carefully** - Understand the job's intent from the description
2. **Generate complete instructions** - Don't create placeholder or stub files
3. **Maintain consistency** - Use the same structure for all step instruction files
4. **Provide examples** - Show what good output looks like
5. **Use context** - The job description provides valuable context for each step
6. **Be specific** - Tailor instructions to the specific step, not generic advice

## Validation Before Sync

Before running `deepwork sync`, verify:
- All directories exist
- `job.yml` is in place
- All step instruction files exist (one per step)
- No file system errors

## Completion Checklist

Before marking this step complete, ensure:
- [ ] job.yml validated and copied to job directory
- [ ] All step instruction files created
- [ ] Each instruction file is complete and actionable
- [ ] `deepwork sync` executed successfully
- [ ] Skills generated in platform directory
- [ ] User informed to follow reload instructions from `deepwork sync`
- [ ] Considered whether rules would benefit this job (Step 7)
- [ ] If rules suggested, offered to run `/deepwork_rules.define`

## Quality Criteria

- Job directory structure is correct
- All instruction files are complete (not stubs)
- Instructions are specific and actionable
- Output examples are provided in each instruction file
- Quality criteria defined for each step
- Steps with user inputs explicitly use "ask structured questions" phrasing
- Sync completed successfully
- Skills available for use
- Thoughtfully considered relevant rules for the job domain


#### Outputs

Create these files/directories:
- `steps/` (directory)
#### Quality Validation

Before completing this skill, verify:
1. **Directory Structure**: Is `.deepwork/jobs/[job_name]/` created correctly?
2. **Complete Instructions**: Are ALL step instruction files complete (not stubs or placeholders)?
3. **Specific & Actionable**: Are instructions tailored to each step's purpose, not generic?
4. **Output Examples**: Does each instruction file show what good output looks like?
5. **Quality Criteria**: Does each instruction file define quality criteria for its outputs?
6. **Ask Structured Questions**: Do step instructions that gather user input explicitly use the phrase "ask structured questions"?
7. **Sync Complete**: Has `deepwork sync` been run successfully?
8. **Commands Available**: Are the slash-commands generated in `.claude/commands/`?
9. **Rules Considered**: Has the agent thought about whether rules would benefit this job? If relevant rules were identified, did they explain them and offer to run `/deepwork_rules.define`? Not every job needs rules - only suggest when genuinely helpful.

Use a sub-agent (Haiku model) to review your work against these criteria before marking complete.

#### On Completion

1. Verify outputs are created
2. Inform user: "new_job workflow complete, outputs: steps/"
3. Consider creating a PR to merge the work branch

---

### Skill: learn

**Type**: Standalone (can be run anytime)

**Description**: Analyzes conversation history to improve job instructions and capture learnings. Use after running a job to refine it.


#### Required User Input

Gather these from the user before starting:
- **job_name**: Name of the job that was run (optional - will auto-detect from conversation)


#### Instructions

# Learn from Job Execution

## Objective

Think deeply about this task. Reflect on the current conversation to identify learnings from DeepWork job executions, improve job instructions with generalizable insights, and capture bespoke (run-specific) learnings in AGENTS.md files in the deepest common folder that would contain all work on the topic in the future.

## Task

Analyze the conversation history to extract learnings and improvements, then apply them appropriately:
- **Generalizable learnings** → Update job instruction files
- **Bespoke learnings** (specific to this run) → Add to AGENTS.md in the deepest common folder for the topic

### Step 1: Analyze Conversation for Job Executions

1. **Scan the conversation** for DeepWork slash commands that were run
   - Look for patterns like `/job_name.step_id`
   - Identify which jobs and steps were executed
   - Note the order of execution

2. **Identify the target folder**
   - This should be the deepest common folder that would contain all work on the topic in the future
   - Should be clear from conversation history where work was done
   - If unclear, run `git diff` to see where changes were made on the branch

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

**doc spec-Related** (should improve doc spec files):
- Improvements to document quality criteria
- Changes to document structure or format
- Updated audience or frequency information
- Examples:
  - "The report should include a summary table"
  - "Quality criterion 'Visualization' needs clearer requirements"
  - "Documents need a section for action items"

**Bespoke** (should go in AGENTS.md):
- Specific to THIS project/codebase/run
- Depends on local conventions or structure
- References specific files or paths
- Would not apply to other uses of this job
- Examples:
  - "In this codebase, API endpoints are in `src/api/`"
  - "This project uses camelCase for function names"
  - "The main config file is at `config/settings.yml`"

### Step 3.5: Identify doc spec-Related Learnings

Review the conversation for doc spec-related improvements:

1. **Quality Criteria Changes**
   - Were any quality criteria unclear or insufficient?
   - Did the agent repeatedly fail certain criteria?
   - Are there new criteria that should be added?

2. **Document Structure Changes**
   - Did the user request different sections?
   - Were parts of the document format confusing?
   - Should the example document be updated?

3. **Metadata Updates**
   - Has the target audience changed?
   - Should frequency or path patterns be updated?

**Signals for doc spec improvements:**
- User asked for changes to document format
- Repeated validation failures on specific criteria
- Feedback about missing sections or information
- Changes to how documents are organized/stored

### Step 4: Update Job Instructions (Generalizable Learnings)

For each generalizable learning:

1. **Locate the instruction file**
   - Path: `.deepwork/jobs/[job_name]/steps/[step_id].md`

2. **Make targeted improvements**
   - Add missing context or clarification
   - Include helpful examples
   - Clarify ambiguous instructions
   - Update quality criteria if needed

3. **Keep instructions concise**
   - Avoid redundancy - don't repeat the same guidance in multiple places
   - Be direct - remove verbose explanations that don't add value
   - Prefer bullet points over paragraphs where appropriate

4. **Preserve instruction structure**
   - Keep existing sections (Objective, Task, Process, Output Format, Quality Criteria)
   - Add to appropriate sections rather than restructuring
   - Maintain consistency with other steps

5. **Track changes for changelog**
   - Note what was changed and why
   - Prepare changelog entry for job.yml

### Step 4b: Extract Shared Content into Referenced Files

Review all instruction files for the job and identify content that:
- Appears in multiple step instructions (duplicated)
- Is lengthy and could be extracted for clarity
- Would benefit from being maintained in one place

**Extract to shared files:**

1. **Create shared files** in `.deepwork/jobs/[job_name]/steps/shared/`
   - `conventions.md` - Coding/formatting conventions used across steps
   - `examples.md` - Common examples referenced by multiple steps
   - `schemas.md` - Data structures or formats used throughout

2. **Reference from instructions** using markdown includes or explicit references:
   ```markdown
   ## Conventions

   Follow the conventions defined in `shared/conventions.md`.
   ```

3. **Benefits of extraction:**
   - Single source of truth - update once, applies everywhere
   - Shorter instruction files - easier to read and maintain
   - Consistent guidance across steps

### Step 4.5: Update doc spec Files (doc spec-Related Learnings)

If doc spec-related learnings were identified:

1. **Locate the doc spec file**
   - Find doc spec references in job.yml outputs (look for `doc_spec: .deepwork/doc_specs/[doc_spec_name].md`)
   - doc spec files are at `.deepwork/doc_specs/[doc_spec_name].md`

2. **Update quality_criteria array**
   - Add new criteria with name and description
   - Modify existing criteria descriptions for clarity
   - Remove criteria that are no longer relevant

3. **Update example document**
   - Modify the markdown body to reflect structure changes
   - Ensure the example matches updated criteria

4. **Update metadata as needed**
   - target_audience: If audience has changed
   - frequency: If production cadence has changed
   - path_patterns: If storage location has changed

**Example doc spec update:**
```yaml
# Before
quality_criteria:
  - name: Visualization
    description: Include charts

# After
quality_criteria:
  - name: Visualization
    description: Include Mermaid.js charts showing spend breakdown by service and month-over-month trend
```

### Step 5: Create/Update AGENTS.md (Bespoke Learnings)

The AGENTS.md file captures project-specific knowledge that helps future agent runs.

1. **Determine the correct location**
   - Place AGENTS.md in the deepest common folder that would contain all work on the topic in the future
   - This ensures the knowledge is available when working in that context
   - If uncertain, place at the project root

2. **Use file references where possible**
   - Instead of duplicating information, reference source files
   - This keeps AGENTS.md in sync as the codebase evolves
   - Pattern: "See `path/to/file.ext` for [description]"

3. **AGENTS.md structure**: See `.deepwork/jobs/deepwork_jobs/templates/agents.md.template` for the standard format.

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

### Step 7: Sync and Relay Instructions

1. **Run deepwork sync** (if instructions were modified)
   ```bash
   deepwork sync
   ```

2. **If skills were regenerated**, look at the "To use the new skills" section in the `deepwork sync` output and **relay these exact reload instructions to the user** (e.g., "Type 'exit' then run 'claude --resume'" for Claude Code)

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
- Instructions are concise - no redundancy or unnecessary verbosity
- Shared/lengthy content extracted into referenced files where appropriate
- AGENTS.md created/updated with bespoke learnings
- File references used instead of duplicating content
- AGENTS.md is in the correct folder (the deepest common folder for the topic)
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

Updated job instructions and created AGENTS.md with bespoke learnings. To get the updated skills, type 'exit' then run 'claude --resume'.
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


#### Outputs

Create these files/directories:
- `AGENTS.md`
#### Quality Validation

Before completing this skill, verify:
1. **Conversation Analyzed**: Did the agent review the conversation for DeepWork job executions?
2. **Confusion Identified**: Did the agent identify points of confusion, errors, or inefficiencies?
3. **Instructions Improved**: Were job instructions updated to address identified issues?
4. **Instructions Concise**: Are instructions free of redundancy and unnecessary verbosity?
5. **Shared Content Extracted**: Is lengthy/duplicated content extracted into referenced files?
6. **doc spec Reviewed (if applicable)**: For jobs with doc spec outputs, were doc spec-related learnings identified?
7. **doc spec Updated (if applicable)**: Were doc spec files updated with improved quality criteria or structure?
8. **Bespoke Learnings Captured**: Were run-specific learnings added to AGENTS.md?
9. **File References Used**: Do AGENTS.md entries reference other files where appropriate?
10. **Working Folder Correct**: Is AGENTS.md in the correct working folder for the job?
11. **Generalizable Separated**: Are generalizable improvements in instructions, not AGENTS.md?
12. **Sync Complete**: Has `deepwork sync` been run if instructions were modified?

Use a sub-agent (Haiku model) to review your work against these criteria before marking complete.

#### On Completion

1. Verify outputs are created
2. Inform user: "learn complete, outputs: AGENTS.md"

---

## Guardrails

- **Never skip prerequisites**: Always verify required steps are complete before running a skill
- **Never produce partial outputs**: Complete all required outputs before marking a skill done
- **Always use the work branch**: Never commit directly to main/master
- **Follow quality criteria**: Use sub-agent review when quality criteria are specified
- **Ask for clarification**: If user intent is unclear, ask before proceeding

## Context Files

- Job definition: `.deepwork/jobs/deepwork_jobs/job.yml`
- define instructions: `.deepwork/jobs/deepwork_jobs/steps/define.md`
- review_job_spec instructions: `.deepwork/jobs/deepwork_jobs/steps/review_job_spec.md`
- implement instructions: `.deepwork/jobs/deepwork_jobs/steps/implement.md`
- learn instructions: `.deepwork/jobs/deepwork_jobs/steps/learn.md`
