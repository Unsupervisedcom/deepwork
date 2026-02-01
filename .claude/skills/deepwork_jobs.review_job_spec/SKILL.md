---
name: deepwork_jobs.review_job_spec
description: "Reviews job.yml against quality criteria using a sub-agent for unbiased validation. Use after defining a job specification."
user-invocable: false
context: fork
agent: deepwork-jobs

---

# deepwork_jobs.review_job_spec

**Step 2/3** in **new_job** workflow

> Create a new DeepWork job from scratch through definition, review, and implementation

> Creates and manages multi-step AI workflows. Use when defining, implementing, or improving DeepWork jobs.

## Prerequisites (Verify First)

Before proceeding, confirm these steps are complete:
- `/deepwork_jobs.define`

## Instructions

**Goal**: Reviews job.yml against quality criteria using a sub-agent for unbiased validation. Use after defining a job specification.

# Review Job Specification

## Objective

Review the `job.yml` created in the define step against quality criteria using a sub-agent for unbiased evaluation, then iterate on fixes until all criteria pass.

## Why This Step Exists

The define step focuses on understanding user requirements. This review step ensures the specification meets quality standards before implementation. A sub-agent provides "fresh eyes" that catch issues the main agent might miss.

## Task

Use a sub-agent to review the job.yml against doc spec quality criteria, fix any failures, and repeat until all pass.

### Step 1: Read the Job Specification

Read both files:
- `.deepwork/jobs/[job_name]/job.yml` - The specification to review
- `.deepwork/doc_specs/job_spec.md` - The quality criteria

### Step 2: Spawn Review Sub-Agent

Use the Task tool with:
- `subagent_type`: "general-purpose"
- `model`: "haiku"
- `description`: "Review job.yml against doc spec"

**Sub-agent prompt**:

```
Review this job.yml against the following 9 quality criteria.

For each criterion, respond with PASS or FAIL.
If FAIL: provide the specific issue and suggested fix.

## job.yml Content

[paste full job.yml content]

## Quality Criteria

1. **Valid Identifier**: Job name lowercase with underscores (e.g., `competitive_research`)
2. **Semantic Version**: Format X.Y.Z (e.g., `1.0.0`)
3. **Concise Summary**: Under 200 characters, describes what job accomplishes
4. **Rich Description**: Multi-line explaining problem, process, outcomes, users
5. **Changelog Present**: Array with at least initial version entry
6. **Complete Steps**: Each has id, name, description, instructions_file, outputs, dependencies
7. **Valid Dependencies**: Reference existing step IDs, no circular references
8. **Input Consistency**: File inputs with `from_step` reference a step in dependencies
9. **Output Paths**: Valid filenames or paths

## Response Format

### Overall: [X/9 PASS]

### Criterion Results
1. Valid Identifier: [PASS/FAIL]
   [If FAIL: Issue and fix]
...

### Summary of Required Fixes
[List fixes needed, or "No fixes required"]
```

### Step 3: Review Findings

Parse the sub-agent's response:
1. Count passing criteria
2. Identify failures
3. Note suggested fixes

### Step 4: Fix Failed Criteria

Edit job.yml to address each failure:

| Criterion | Common Fix |
|-----------|-----------|
| Valid Identifier | Convert to lowercase_underscores |
| Semantic Version | Set to `"1.0.0"` or fix format |
| Concise Summary | Shorten to <200 chars |
| Rich Description | Add multi-line explanation |
| Changelog Present | Add `changelog:` array |
| Complete Steps | Add missing required fields |
| Valid Dependencies | Fix step ID reference |
| Input Consistency | Add referenced step to dependencies |
| Output Paths | Use valid filename/path format |

### Step 5: Re-Run Review (If Needed)

If any criteria failed:
1. Spawn a new sub-agent with updated job.yml
2. Review new findings
3. Fix remaining issues
4. Repeat until all 9 criteria pass

### Step 6: Confirm Completion

When all 9 criteria pass:

1. Announce: "All 9 doc spec quality criteria pass."
2. Include: `<promise>Quality Criteria Met</promise>`
3. Guide: "Run `/deepwork_jobs.implement` to generate step instruction files."

## Output

The validated `job.yml` file at `.deepwork/jobs/[job_name]/job.yml` passing all 9 quality criteria.


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


**Files from Previous Steps** - Read these first:
- `job.yml` (from `define`)

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

## Quality Validation

**Before completing this step, you MUST have your work reviewed against the quality criteria below.**

Use a sub-agent (Haiku model) to review your work against these criteria:

**Criteria (all must be satisfied)**:
1. **Sub-Agent Used**: Was a sub-agent spawned to provide unbiased review?
2. **All doc spec Criteria Evaluated**: Did the sub-agent assess all 9 quality criteria?
3. **Findings Addressed**: Were all failed criteria addressed by the main agent?
4. **Validation Loop Complete**: Did the review-fix cycle continue until all criteria passed?
**Review Process**:
1. Once you believe your work is complete, spawn a sub-agent using Haiku to review your work against the quality criteria above
2. The sub-agent should examine your outputs and verify each criterion is met
3. If the sub-agent identifies valid issues, fix them
4. Have the sub-agent review again until all valid feedback has been addressed
5. Only mark the step complete when the sub-agent confirms all criteria are satisfied

## On Completion

1. Verify outputs are created
2. Inform user: "new_job step 2/3 complete, outputs: job.yml"
3. **Continue workflow**: Use Skill tool to invoke `/deepwork_jobs.implement`

---

**Reference files**: `.deepwork/jobs/deepwork_jobs/job.yml`, `.deepwork/jobs/deepwork_jobs/steps/review_job_spec.md`