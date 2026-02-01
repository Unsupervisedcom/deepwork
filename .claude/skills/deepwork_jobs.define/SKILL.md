---
name: deepwork_jobs.define
description: "Creates a job.yml specification by gathering workflow requirements through structured questions. Use when starting a new multi-step workflow."
user-invocable: false
context: fork
agent: experts

---

# deepwork_jobs.define

**Step 1/3** in **new_job** workflow

> Create a new DeepWork job from scratch through definition, review, and implementation

> Creates and manages multi-step AI workflows. Use when defining, implementing, or improving DeepWork jobs.


## Instructions

**Goal**: Creates a job.yml specification by gathering workflow requirements through structured questions. Use when starting a new multi-step workflow.

# Define Job Specification

## Objective

Create a `job.yml` specification file that defines a new DeepWork job by understanding the user's workflow requirements through interactive questioning.

## Task

Guide the user through defining a job specification by asking structured questions. The output is **only** the `job.yml` file - step instruction files are created in the `implement` step.

### Phase 1: Understand the Job Purpose

Ask structured questions to understand the workflow:

1. **Overall goal** - What complex task are they trying to accomplish? What domain (research, marketing, development, reporting)?

2. **Success criteria** - What's the final deliverable? Who is the audience? What quality matters most?

3. **Major phases** - What are the distinct stages from start to finish? Any dependencies between phases?

### Phase 2: Detect Document-Oriented Workflows

Check for document-focused patterns in the user's description:
- Keywords: "report", "summary", "document", "monthly", "quarterly", "for stakeholders"
- Final deliverable is a specific document type
- Recurring documents with consistent structure

**If detected**, offer to create a doc spec:
1. Inform the user: "This workflow produces a specific document type. I recommend defining a doc spec first."
2. Ask if they want to create a doc spec, use existing one, or skip

**If creating a doc spec**, gather:
- Document name and purpose
- Target audience and frequency
- Quality criteria (3-5, focused on the output document itself)
- Document structure (sections, required elements)

Create at `.deepwork/doc_specs/[doc_spec_name].md`. Reference `.deepwork/doc_specs/job_spec.md` for an example.

### Phase 3: Define Each Step

For each major phase, gather:

1. **Purpose** - What does this step accomplish? What are inputs and outputs?

2. **Inputs**:
   - User-provided parameters (e.g., topic, target audience)?
   - Files from previous steps?

3. **Outputs**:
   - What files does this step produce?
   - Format (markdown, YAML, JSON)?
   - Where to save? (Use meaningful paths like `competitive_research/analysis.md`, not `.deepwork/outputs/`)
   - Does this output have a doc spec?

4. **Dependencies** - Which previous steps must complete first?

5. **Process** - Key activities? Quality checks needed?

6. **Agent Delegation** - Should this step run via a specific agent? Use `agent: experts` for domain-specific expertise.

#### Output Path Guidelines

- Place outputs in main repo, not dot-directories
- Use job name as top-level folder for job-specific outputs
- Include dates for periodic outputs that accumulate (monthly reports)
- Omit dates for current-state outputs that get updated in place
- Use `_dataroom` folders for supporting materials

### Phase 4: Validate the Workflow

After gathering all step information:

1. **Review the flow** - Summarize the complete workflow, show how outputs feed into next steps
2. **Check for gaps** - Undefined inputs? Unused outputs? Circular dependencies?
3. **Confirm details** - Job name (lowercase_underscores), summary (max 200 chars), description (detailed), version (1.0.0)

### Phase 5: Create the Job

Create the directory structure:

```bash
.deepwork/jobs/deepwork_jobs/make_new_job.sh [job_name]
```

Create `job.yml` at `.deepwork/jobs/[job_name]/job.yml`.

**Reference**: See `.deepwork/jobs/deepwork_jobs/templates/job.yml.template` for structure and `.deepwork/jobs/deepwork_jobs/templates/job.yml.example` for a complete example.

**Validation rules**:
- Job name: lowercase, underscores, no spaces
- Version: semantic versioning (1.0.0)
- Summary: under 200 characters
- Step IDs: unique, lowercase with underscores
- Dependencies must reference existing steps
- File inputs with `from_step` must be in dependencies
- At least one output per step

## Output

**File**: `.deepwork/jobs/[job_name]/job.yml`

After creating the file, tell the user to run `/deepwork_jobs.review_job_spec` next.


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

**User Parameters** - Gather from user before starting:
- **job_purpose**: What complex task or workflow are you trying to accomplish?


## Work Branch

Use branch format: `deepwork/deepwork_jobs-[instance]-YYYYMMDD`

- If on a matching work branch: continue using it
- If on main/master: create new branch with `git checkout -b deepwork/deepwork_jobs-[instance]-$(date +%Y%m%d)`

## Outputs

**Required outputs**:
- `job.yml`
  **Doc Spec**: DeepWork Job Specification
  > YAML specification file that defines a multi-step workflow job for AI agents
  **Definition**: `.deepwork/doc_specs/job_spec.md`
  **Target Audience**: AI agents executing jobs and developers defining workflows
  **Quality Criteria**:
  1. **Valid Identifier**: Job name must be lowercase with underscores, no spaces or special characters (e.g., `competitive_research`, `monthly_report`)
  2. **Semantic Version**: Version must follow semantic versioning format X.Y.Z (e.g., `1.0.0`, `2.1.3`)
  3. **Concise Summary**: Summary must be under 200 characters and clearly describe what the job accomplishes
  4. **Rich Description**: Description must be multi-line and explain: the problem solved, the process, expected outcomes, and target users
  5. **Changelog Present**: Must include a changelog array with at least the initial version entry. Changelog should only include one entry per branch at most
  6. **Complete Steps**: Each step must have: id (lowercase_underscores), name, description, instructions_file, outputs (at least one), and dependencies array
  7. **Valid Dependencies**: Dependencies must reference existing step IDs with no circular references
  8. **Input Consistency**: File inputs with `from_step` must reference a step that is in the dependencies array
  9. **Output Paths**: Outputs must be valid filenames or paths within the main repo directory structure, never in dot-directories like `.deepwork/`. Use specific, descriptive paths that lend themselves to glob patterns (e.g., `competitive_research/acme_corp/swot.md` or `operations/reports/2026-01/spending_analysis.md`). Parameterized paths like `[competitor_name]/` are encouraged for per-entity outputs. Avoid generic names (`output.md`, `analysis.md`) and transient-sounding paths (`temp/`, `draft.md`). Supporting materials for a final output should go in a peer `_dataroom` folder (e.g., `spending_analysis_dataroom/`).
  10. **Concise Instructions**: The content of the file, particularly the description, must not have excessively redundant information. It should be concise and to the point given that extra tokens will confuse the AI.

  <details>
  <summary>Example Document Structure</summary>

  ```markdown
  # DeepWork Job Specification: [job_name]

  A `job.yml` file defines a complete multi-step workflow that AI agents can execute. Each job breaks down a complex task into reviewable steps with clear inputs and outputs.

  ## Required Fields

  ### Top-Level Metadata

  ```yaml
  name: job_name                    # lowercase, underscores only
  version: "1.0.0"                  # semantic versioning
  summary: "Brief description"      # max 200 characters
  description: |                    # detailed multi-line explanation
    [Explain what this workflow does, why it exists,
    what outputs it produces, and who should use it]
  ```

  ### Changelog

  ```yaml
  changelog:
    - version: "1.0.0"
      changes: "Initial job creation"
    - version: "1.1.0"
      changes: "Added quality validation hooks"
  ```

  ### Steps Array

  ```yaml
  steps:
    - id: step_id                   # unique, lowercase_underscores
      name: "Human Readable Name"
      description: "What this step accomplishes"
      instructions_file: steps/step_id.md
      inputs:
        # User-provided inputs:
        - name: param_name
          description: "What the user provides"
        # File inputs from previous steps:
        - file: output.md
          from_step: previous_step_id
      outputs:
        - competitive_research/competitors_list.md           # descriptive path
        - competitive_research/[competitor_name]/research.md # parameterized path
        # With doc spec reference:
        - file: competitive_research/final_report.md
          doc_spec: .deepwork/doc_specs/report_type.md
      dependencies:
        - previous_step_id          # steps that must complete first
  ```

  ## Optional Fields

  ### Exposed Steps

  ```yaml
  steps:
    - id: learn
      exposed: true                 # Makes step available without running dependencies
  ```

  ### Agent Delegation

  When a step should be executed by a specific agent type, use the `agent` field. This automatically sets `context: fork` in the generated skill.

  ```yaml
  steps:
    - id: research_step
      agent: general-purpose        # Delegates to the general-purpose agent
  ```

  Available agent types:
  - `general-purpose` - Standard agent for multi-step tasks

  ### Quality Hooks

  ```yaml
  steps:
    - id: step_id
      hooks:
        after_agent:
          # Inline prompt for quality validation:
          - prompt: |
              Verify the output meets criteria:
              1. [Criterion 1]
              2. [Criterion 2]
              If ALL criteria are met, include `<promise>...</promise>`.
          # External prompt file:
          - prompt_file: hooks/quality_check.md
          # Script for programmatic validation:
          - script: hooks/run_tests.sh
  ```

  ### Stop Hooks (Legacy)

  ```yaml
  steps:
    - id: step_id
      stop_hooks:
        - prompt: "Validation prompt..."
        - prompt_file: hooks/check.md
        - script: hooks/validate.sh
  ```

  ## Validation Rules

  1. **No circular dependencies**: Step A cannot depend on Step B if Step B depends on Step A
  2. **File inputs require dependencies**: If a step uses `from_step: X`, then X must be in its dependencies
  3. **Unique step IDs**: No two steps can have the same id
  4. **Valid file paths**: Output paths must not contain invalid characters and should be in the main repo (not dot-directories)
  5. **Instructions files exist**: Each `instructions_file` path should have a corresponding file created

  ## Example: Complete Job Specification

  ```yaml
  name: competitive_research
  version: "1.0.0"
  summary: "Systematic competitive analysis workflow"
  description: |
    A comprehensive workflow for analyzing competitors in your market segment.
    Helps product teams understand the competitive landscape through systematic
    identification, research, comparison, and positioning recommendations.

    Produces:
    - Vetted competitor list
    - Research notes per competitor
    - Comparison matrix
    - Strategic positioning report

  changelog:
    - version: "1.0.0"
      changes: "Initial job creation"

  steps:
    - id: identify_competitors
      name: "Identify Competitors"
      description: "Identify 5-7 key competitors in the target market"
      instructions_file: steps/identify_competitors.md
      inputs:
        - name: market_segment
          description: "The market segment to analyze"
        - name: product_category
          description: "The product category"
      outputs:
        - competitive_research/competitors_list.md
      dependencies: []

    - id: research_competitors
      name: "Research Competitors"
      description: "Deep dive research on each identified competitor"
      instructions_file: steps/research_competitors.md
      inputs:
        - file: competitive_research/competitors_list.md
          from_step: identify_competitors
      outputs:
        - competitive_research/[competitor_name]/research.md
      dependencies:
        - identify_competitors

    - id: positioning_report
      name: "Positioning Report"
      description: "Strategic positioning recommendations"
      instructions_file: steps/positioning_report.md
      inputs:
        - file: competitive_research/[competitor_name]/research.md
          from_step: research_competitors
      outputs:
        - file: competitive_research/positioning_report.md
          doc_spec: .deepwork/doc_specs/positioning_report.md
      dependencies:
        - research_competitors
  ```
  ```

  </details>

## Guardrails

- Do NOT skip prerequisite verification if this step has dependencies
- Do NOT produce partial outputs; complete all required outputs before finishing
- Do NOT proceed without required inputs; ask the user if any are missing
- Do NOT modify files outside the scope of this step's defined outputs

## On Completion

1. Verify outputs are created
2. Inform user: "new_job step 1/3 complete, outputs: job.yml"
3. **Continue workflow**: Use Skill tool to invoke `/deepwork_jobs.review_job_spec`

---

**Reference files**: `.deepwork/jobs/deepwork_jobs/job.yml`, `.deepwork/jobs/deepwork_jobs/steps/define.md`