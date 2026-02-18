---
name: "Agentic Process Data Flow"
keywords:
  - data flow
  - inputs
  - outputs
  - dependencies
  - workflows
  - steps
  - coherence
last_updated: "2026-02-18"
---

## How Data Flows Through Workflows

A DeepWork workflow is a directed acyclic graph (DAG) of steps. Data flows through explicit input/output declarations:

1. A step declares `outputs` — named artifacts it produces
2. A downstream step declares `inputs` with `file` and `from_step` — pulling specific outputs from prior steps
3. The `dependencies` array must include any step whose outputs are consumed

## Dependency Rules

- If step B has an input `from_step: A`, then `A` must appear in B's `dependencies` (directly or transitively through the workflow ordering)
- Concurrent steps (written as `[step_a, step_b]` in workflow lists) must be genuinely independent — no input/output relationships between them
- Circular dependencies are invalid and will cause runtime failures

## Workflow Step Ordering

```yaml
workflows:
  - name: example
    steps:
      - step_a           # runs first
      - step_b           # runs after step_a
      - [step_c, step_d] # run concurrently after step_b
      - step_e           # runs after both step_c and step_d
```

## Common Data Flow Issues

- **Dangling outputs**: A step produces an output that no downstream step consumes. Not an error, but worth questioning whether the step belongs in the workflow or the output should be removed.
- **Missing dependencies**: Step B uses output from step A but doesn't declare the dependency. This will fail at runtime.
- **Phantom inputs**: Step B references `from_step: X` but step X doesn't exist or doesn't produce the named output.
- **Concurrent mutation**: Two concurrent steps both write to the same file path. This creates a race condition.

## Review Coverage for Data Flow

When step B depends on step A's output, check:
- Does step A's review validate the structural aspects that step B's instructions assume?
- If step A's output has specific format requirements (YAML structure, section headings, etc.), are those in A's quality criteria?
- If the review misses a structural issue, it will propagate silently to step B.
