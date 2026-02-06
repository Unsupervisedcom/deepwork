# Define Job Specification

## Objective

Create a `job.yml` specification file that defines the structure of a new DeepWork job by thoroughly understanding the user's workflow requirements through an interactive question-and-answer process.

## Task

Guide the user through defining a job specification by asking structured questions. **Do not attempt to create the specification without first fully understanding the user's needs.**

**Important**: Use the AskUserQuestion tool to ask structured questions when gathering information from the user. This provides a better user experience with clear options and guided choices.

The output of this step is **only** the `job.yml` file - a complete specification of the workflow. The actual step instruction files will be created in the next step (`implement`).

### Step 0.5: Determine Job Scope (Local or Global)

Before starting the workflow definition, ask the user where they want this job to be installed:

**Ask structured questions:**
- "Where would you like this job to be installed?"
  - **Local** - Available only in this project (stored in `.deepwork/jobs/`)
  - **Global** - Available across all projects with DeepWork installed (stored in `~/.deepwork/jobs/`)

**Store this decision** to use later when creating the job directory. Most users will want local jobs (project-specific workflows), but global jobs are useful for workflows that apply across many projects (e.g., generic documentation tasks, code review processes).

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

   **Important**: Doc spec quality criteria define requirements for the **output document itself**, not the process of creating it. Focus on what the finished document must contain or achieve.

   Examples for a spending report:
   - **Visualization**: Must include charts showing spend breakdown by service
   - **Variance Analysis**: Must compare current month against previous with percentages
   - **Action Items**: Must include recommended cost optimization actions

   **Note**: When a doc spec is created for a step's output, the step should generally NOT have separate `quality_criteria` in the job.yml. The doc spec's criteria cover output quality. Only add step-level quality_criteria if there are essential process requirements (e.g., "must use specific tool"), and minimize these when possible.

4. **Document Structure**
   - What sections should it have?
   - Any required elements (tables, charts, summaries)?

### Step 1.7: Create the doc spec File (if needed)

Create the doc spec file at `.deepwork/doc_specs/[doc_spec_name].md`:

**Template reference**: See `.deepwork/jobs/deepwork_jobs/templates/doc_spec.md.template` for the standard structure.

**Complete example**: See `.deepwork/doc_specs/job_spec.md` for a fully worked example (the doc spec for job.yml files).

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
   - **Does this output have a doc spec?** If a doc spec was created in Step 1.6/1.7, reference it for the appropriate output

   #### Work Product Storage Guidelines

   **Key principle**: Job outputs belong in the main repository directory structure, not in dot-directories. The `.deepwork/` directory is for job definitions and configuration only.

   **Why this matters**:
   - **Version control**: Work products in the main repo are tracked by git and visible in PRs
   - **Discoverability**: Team members can find outputs without knowing about DeepWork internals
   - **Tooling compatibility**: IDEs, search tools, and CI/CD work naturally with standard paths
   - **Glob patterns**: Well-structured paths enable powerful file matching (e.g., `competitive_research/**/*.md`)

   **Good output path patterns**:
   ```
   competitive_research/competitors_list.md
   competitive_research/acme_corp/research.md
   operations/reports/2026-01/spending_analysis.md
   docs/api/endpoints.md
   ```

   **Avoid these patterns**:
   ```
   .deepwork/outputs/report.md          # Hidden in dot-directory
   output.md                            # Too generic, no context
   research.md                          # Unclear which research
   temp/draft.md                        # Transient-sounding paths
   ```

   **Organizing multi-file outputs**:
   - Use the job name as a top-level folder when outputs are job-specific
   - Use parameterized paths for per-entity outputs: `competitive_research/[competitor_name]/`
   - Match existing project conventions when extending a codebase

   **When to include dates in paths**:
   - **Include date** for periodic outputs where each version is retained (e.g., monthly reports, quarterly reviews, weekly summaries). These accumulate over time and historical versions remain useful.
     ```
     operations/reports/2026-01/spending_analysis.md              # Monthly report - keep history
     hr/employees/[employee_name]/quarterly_reviews/2026-Q1.pdf   # Per-employee quarterly review
     ```
   - **Omit date** for current-state outputs that represent the latest understanding and get updated in place. Previous versions live in git history, not separate files.
     ```
     competitive_research/acme_corp/swot.md  # Current SWOT - updated over time
     docs/architecture/overview.md           # Living document
     ```

   **Supporting materials and intermediate outputs**:
   - Content generated in earlier steps to support the final output (research notes, data extracts, drafts) should be placed in a `_dataroom` folder that is a peer to the final output
   - Name the dataroom folder by replacing the file extension with `_dataroom`
     ```
     operations/reports/2026-01/spending_analysis.md           # Final output
     operations/reports/2026-01/spending_analysis_dataroom/    # Supporting materials
         raw_data.csv
         vendor_breakdown.md
         notes.md
     ```
   - This keeps supporting materials organized and discoverable without cluttering the main output location

4. **Step Dependencies**
   - Which previous steps must complete before this one?
   - Are there any ordering constraints?

5. **Step Process** (high-level understanding)
   - What are the key activities in this step?
   - Are there any quality checks or validation needed?
   - What makes a good vs. bad output for this step?

6. **Agent Delegation** (optional)
   - Should this step be executed by a specific agent type?
   - Use the `agent` field when the step should run in a forked context with a specific agent
   - When `agent` is set, the generated skill automatically includes `context: fork`
   - Available agent types:
     - `general-purpose` - Standard agent for multi-step tasks

   ```yaml
   steps:
     - id: research_step
       agent: general-purpose  # Delegates to the general-purpose agent
   ```

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

