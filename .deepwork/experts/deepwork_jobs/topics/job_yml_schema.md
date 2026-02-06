---
name: job.yml Schema Reference
keywords:
  - schema
  - yaml
  - validation
  - fields
  - structure
last_updated: 2025-01-30
---

# job.yml Schema Reference

Complete reference for the job.yml specification file.

## Required Fields

### name
- Type: string
- Pattern: `^[a-z][a-z0-9_]*$`
- Must start with lowercase letter, can contain lowercase letters, numbers, underscores
- Examples: `competitive_research`, `monthly_report`, `feature_dev`

### version
- Type: string
- Pattern: `^\d+\.\d+\.\d+$`
- Semantic versioning format
- Examples: `1.0.0`, `2.1.3`

### summary
- Type: string
- Length: 1-200 characters
- Brief one-line description of the job
- Used in skill descriptions and menus

### steps
- Type: array
- Minimum items: 1
- Each item is a step definition object

## Optional Fields

### description
- Type: string
- Multi-line detailed explanation
- Included in generated skill files for context
- Good for: problem solved, process overview, target users

### workflows
- Type: array
- Named sequences grouping steps
- See Workflow Schema section

### changelog
- Type: array
- Version history entries
- Each entry has `version` (string) and `changes` (string)

## Step Schema

### Required Step Fields

```yaml
steps:
  - id: identify_competitors        # unique, lowercase_underscores
    name: "Identify Competitors"    # human-readable
    description: "Find and list..."  # what it does
    instructions_file: steps/identify.md  # path to instructions
    outputs:                        # at least one output
      - competitors_list.md
```

### Optional Step Fields

```yaml
  - id: research
    # ... required fields ...
    inputs:
      - name: market_segment
        description: "Target market"
      - file: competitors_list.md
        from_step: identify_competitors
    dependencies:
      - identify_competitors
    exposed: true           # show in user menus
    quality_criteria:
      - "All competitors have descriptions"
      - "Sources are cited"
    agent: deepwork-jobs    # delegate to expert (see Agent Delegation)
    hooks:
      after_agent:
        - script: hooks/validate.sh
```

### Agent Delegation (The `agent` Field)

The `agent` field specifies which expert should execute this step. When set:
1. The generated skill includes `context: fork` (runs in isolated context)
2. The generated skill includes `agent: [expert-name]` (loads that expert's knowledge)
3. The step runs with all the expert's topics, learnings, and domain knowledge available

**This is how you make a step "run via" an expert.**

```yaml
steps:
  - id: define
    name: "Define Job Specification"
    description: "Creates a job.yml specification..."
    instructions_file: steps/define.md
    agent: deepwork-jobs    # Runs with deepwork-jobs expert loaded
    outputs:
      - job.yml
```

Common agent values:
- `deepwork-jobs` - Expert for DeepWork job creation and management
- `deepwork-rules` - Expert for DeepWork rule creation
- Custom experts you've defined in `.deepwork/experts/`

See the **Step Delegation** topic for detailed examples and patterns.

## Output Formats

Simple string:
```yaml
outputs:
  - report.md
  - data/
```

With doc spec:
```yaml
outputs:
  - file: reports/analysis.md
    doc_spec: .deepwork/doc_specs/analysis.md
```

Doc spec path must match pattern: `^\.deepwork/doc_specs/[a-z][a-z0-9_-]*\.md$`

## Workflow Schema

```yaml
workflows:
  - name: full_analysis
    summary: "Complete competitive analysis workflow"
    steps:
      - identify
      - research
      - analyze
      - report
```

Concurrent steps:
```yaml
steps:
  - identify
  - [research_a, research_b]  # parallel execution
  - synthesize
```

## Hook Schema

```yaml
hooks:
  after_agent:
    - prompt: "Verify criteria are met"       # inline
    - prompt_file: hooks/check.md             # from file
    - script: hooks/run_tests.sh              # shell script
```

Each hook action must have exactly one of: `prompt`, `prompt_file`, or `script`.

## Validation Rules

1. Step IDs must be unique within the job
2. Dependencies must reference existing step IDs
3. File inputs with `from_step` must have that step in dependencies
4. No circular dependencies allowed
5. Workflow steps must reference existing step IDs
6. No duplicate steps within a workflow
