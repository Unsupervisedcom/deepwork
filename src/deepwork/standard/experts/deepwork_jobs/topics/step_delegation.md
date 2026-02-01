---
name: Step Delegation to Experts
keywords:
  - agent
  - expert
  - delegation
  - context fork
  - sub-agent
last_updated: 2025-02-01
---

# Step Delegation to Experts

How to make job steps run via experts using the `agent` field.

## The `agent` Field

The `agent` field in a step definition specifies which expert should execute that step. This is the primary mechanism for making steps "run via" an expert.

```yaml
steps:
  - id: define
    name: "Define Job Specification"
    description: "Creates a job.yml specification..."
    instructions_file: steps/define.md
    agent: deepwork-jobs    # <-- This step runs via the deepwork-jobs expert
    outputs:
      - job.yml
```

## What Happens When You Set `agent`

When a step has `agent: expert-name`, the generated skill includes:

1. **`context: fork`** - The step runs in an isolated context (sub-agent)
2. **`agent: expert-name`** - The expert's knowledge is loaded into that context

The resulting skill frontmatter looks like:

```yaml
---
name: my_job.define
description: "Creates a job.yml specification..."
context: fork
agent: deepwork-jobs
---
```

## How Expert Knowledge Flows

When the skill runs:

1. A forked context (sub-agent) is created
2. The expert file (e.g., `.claude/agents/dwe_deepwork-jobs.md`) is loaded
3. All expert topics, learnings, and domain knowledge become available
4. The step instructions execute with this enhanced context
5. The sub-agent completes and returns to the parent context

## Real-World Example: deepwork_jobs

The `deepwork_jobs` job itself uses expert delegation. All steps run via the `deepwork-jobs` expert:

```yaml
steps:
  - id: define
    name: "Define Job Specification"
    description: "Creates a job.yml specification..."
    instructions_file: steps/define.md
    agent: deepwork-jobs    # Runs with job schema knowledge
    outputs:
      - file: job.yml
        doc_spec: .deepwork/doc_specs/job_spec.md

  - id: review_job_spec
    name: "Review Job Specification"
    description: "Reviews job.yml against quality criteria..."
    instructions_file: steps/review_job_spec.md
    agent: deepwork-jobs    # Same expert, different step
    inputs:
      - file: job.yml
        from_step: define
    outputs:
      - file: job.yml
        doc_spec: .deepwork/doc_specs/job_spec.md

  - id: implement
    name: "Implement Job Steps"
    description: "Generates step instruction files..."
    instructions_file: steps/implement.md
    agent: deepwork-jobs    # Expert knowledge helps write good instructions
    inputs:
      - file: job.yml
        from_step: review_job_spec
    outputs:
      - steps/
```

## When to Use Expert Delegation

Use `agent: expert-name` when:

1. **Domain expertise is needed** - The step requires specialized knowledge that an expert provides
2. **Consistency across steps** - Multiple steps in a job should use the same expert context
3. **Complex validation** - The expert has knowledge about quality criteria or best practices
4. **Template awareness** - The expert knows about file formats, schemas, or conventions

## Available Experts

Standard experts that ship with DeepWork:

- `deepwork-jobs` - Expert on job.yml schema, step instructions, skill generation
- `deepwork-rules` - Expert on rule creation and file-change triggers

Custom experts can be created in `.deepwork/experts/` and referenced by name.

## Expert vs. Sub-Agent Quality Review

Note the difference between:

1. **Expert delegation** (`agent: deepwork-jobs`) - The entire step runs with expert knowledge loaded
2. **Sub-agent quality review** (`quality_criteria` field) - A Haiku sub-agent validates outputs against criteria

These can be combined - a step can run via an expert AND have quality criteria validated by a sub-agent:

```yaml
steps:
  - id: implement
    instructions_file: steps/implement.md
    agent: deepwork-jobs              # Expert knowledge during execution
    quality_criteria:                  # Sub-agent validates outputs
      - "All instruction files are complete"
      - "No placeholder content remains"
```

## Troubleshooting

**Step not using expert knowledge?**
- Verify `agent: expert-name` is set in job.yml
- Run `deepwork sync` to regenerate skills
- Check the generated skill has `agent:` in its frontmatter

**Expert not found?**
- Ensure the expert exists in `.deepwork/experts/[expert-name]/`
- Run `deepwork sync` to generate the expert agent file
- Check `.claude/agents/dwe_[expert-name].md` exists
