---
name: "DeepWork Job Specification"
description: "YAML specification file that defines a multi-step workflow job for AI agents"
path_patterns:
  - ".deepwork/jobs/*/job.yml"
target_audience: "AI agents executing jobs and developers defining workflows"
frequency: "Created once per job, updated as workflow evolves"
quality_criteria:
  - name: Valid Identifier
    description: "Job name must be lowercase with underscores, no spaces or special characters (e.g., `competitive_research`, `monthly_report`)"
  - name: Semantic Version
    description: "Version must follow semantic versioning format X.Y.Z (e.g., `1.0.0`, `2.1.3`)"
  - name: Concise Summary
    description: "Summary must be under 200 characters and clearly describe what the job accomplishes"
  - name: Rich Description
    description: "Description must be multi-line and explain: the problem solved, the process, expected outcomes, and target users"
  - name: Changelog Present
    description: "Must include a changelog array with at least the initial version entry. Changelog should only include one entry per branch at most"
  - name: Complete Steps
    description: "Each step must have: id (lowercase_underscores), name, description, instructions_file, outputs (at least one), and dependencies array"
  - name: Valid Dependencies
    description: "Dependencies must reference existing step IDs with no circular references"
  - name: Input Consistency
    description: "File inputs with `from_step` must reference a step that is in the dependencies array"
  - name: Output Paths
    description: "Outputs must be valid filenames or paths (e.g., `report.md` or `reports/analysis.md`)"
  - name: Concise Instructions
    description: "The content of the file, particularly the description, must not have excessively redundant information. It should be concise and to the point given that extra tokens will confuse the AI."
---

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
      - filename.md               # simple filename
      - reports/analysis.md       # path with directory
      # With doc spec reference:
      - file: report.md
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
4. **Valid file paths**: Output paths must not contain invalid characters
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
      - competitors_list.md
    dependencies: []

  - id: research_competitors
    name: "Research Competitors"
    description: "Deep dive research on each identified competitor"
    instructions_file: steps/research_competitors.md
    inputs:
      - file: competitors_list.md
        from_step: identify_competitors
    outputs:
      - research_notes.md
    dependencies:
      - identify_competitors

  - id: positioning_report
    name: "Positioning Report"
    description: "Strategic positioning recommendations"
    instructions_file: steps/positioning_report.md
    inputs:
      - file: research_notes.md
        from_step: research_competitors
    outputs:
      - file: positioning_report.md
        doc_spec: .deepwork/doc_specs/positioning_report.md
    dependencies:
      - research_competitors
```
