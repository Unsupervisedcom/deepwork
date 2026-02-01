---
name: workflow.yml Schema Reference
keywords:
  - schema
  - yaml
  - validation
  - fields
  - structure
  - workflow
last_updated: 2025-02-01
---

# workflow.yml Schema Reference

Complete reference for the workflow.yml specification file.

## Required Fields

### name
- Type: string
- Pattern: `^[a-z][a-z0-9_]*$`
- Must start with lowercase letter, can contain lowercase letters, numbers, underscores
- Must match the workflow folder name
- Examples: `new_workflow`, `review_pr`, `learn`

### version
- Type: string
- Pattern: `^\d+\.\d+\.\d+$`
- Semantic versioning format
- Examples: `1.0.0`, `2.1.3`

### summary
- Type: string
- Length: 1-200 characters
- Brief one-line description of the workflow
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

### execution_order
- Type: array
- Explicit step ordering with concurrent support
- See Execution Order section

### changelog
- Type: array
- Version history entries
- Each entry has `version` (string) and `changes` (string)

## Step Schema

### Required Step Fields

```yaml
steps:
  - id: identify_competitors        # unique within expert, lowercase_underscores
    name: "Identify Competitors"    # human-readable
    description: "Find and list..."  # what it does
    instructions_file: steps/identify.md  # path relative to workflow dir
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
    agent: experts          # delegate to expert (see Agent Delegation)
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
    name: "Define Workflow Specification"
    description: "Creates a workflow.yml specification..."
    instructions_file: steps/define.md
    agent: experts    # Runs with experts expert loaded
    outputs:
      - workflow.yml
```

Common agent values:
- `experts` - Expert for DeepWork expert and workflow creation
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

## Execution Order

By default, steps execute in the order defined. Use `execution_order` for explicit control:

Sequential:
```yaml
execution_order:
  - identify
  - research
  - analyze
  - report
```

Concurrent steps:
```yaml
execution_order:
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

1. Step IDs must be unique within the expert (across all workflows)
2. Dependencies must reference existing step IDs
3. File inputs with `from_step` must have that step in dependencies
4. No circular dependencies allowed
5. Execution order steps must reference existing step IDs
