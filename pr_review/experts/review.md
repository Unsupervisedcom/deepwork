# experts Review

**PR**: #197
**Date**: 2026-02-01
**Reviewer**: experts expert

## Summary

This PR merges the jobs system into the experts framework, creating a unified architecture where workflows are now owned by experts rather than being standalone entities. The change represents a significant restructuring:

1. **Terminology shift**: "job" -> "workflow", "job.yml" -> "workflow.yml"
2. **Structural change**: Workflows now live inside expert directories (`.deepwork/experts/[expert]/workflows/[workflow]/`) rather than separately (`.deepwork/jobs/[job]/`)
3. **Schema evolution**: `job_schema.py` renamed to `workflow_schema.py`, with appropriate field updates
4. **Skill naming**: Skills now use `expert-name.step-id` format instead of `job-name.step-id`

The overall architecture is sound - embedding workflows within experts creates a cohesive domain knowledge + action system. The expert.yml schema remains minimal (just `discovery_description` and `full_expertise`), while workflow.yml carries the complex step definitions. Topics and learnings continue to follow the documented frontmatter patterns.

## Issues Found

### Issue 1
- **File**: `src/deepwork/cli/install.py`
- **Line(s)**: 438-439
- **Severity**: Minor
- **Issue**: The "Next steps" output message still references the old naming convention `/deepwork-jobs.define`. This should be updated to reflect the new workflow naming under the experts system.
- **Suggestion**: Update line 438 to say `"/experts.define"` or `"/experts.new_workflow"` to match the new skill naming convention.

### Issue 2
- **File**: `src/deepwork/standard/experts/experts/workflows/new_workflow/workflow.yml`
- **Line(s)**: 35
- **Severity**: Major
- **Issue**: The `review_workflow_spec` step has `agent: general-purpose`, but `general-purpose` is not a defined expert. According to the step delegation topic, valid agent values should reference actual experts. Using `general-purpose` will cause the skill generation to include `agent: general-purpose` in the frontmatter, which will fail at runtime when Claude Code tries to load a non-existent expert agent.
- **Suggestion**: Either remove the `agent` field from this step (letting it run in the main context) or set it to `experts` if the expert knowledge is needed. The `quality_criteria` field alone triggers sub-agent validation without requiring expert context.

### Issue 3
- **File**: `src/deepwork/standard/experts/experts/topics/workflow_yml_schema.md`
- **Line(s)**: 10
- **Severity**: Suggestion
- **Issue**: The topic has "workflow" as a keyword, but according to the keyword guidelines, topics should avoid broad domain terms. Since this is a topic within the "experts" expert which is about the experts system (including workflows), "workflow" is arguably too broad.
- **Suggestion**: Consider removing "workflow" and using more specific keywords like "workflow.yml", "specification", "required fields".

### Issue 4
- **File**: `src/deepwork/standard/experts/experts/expert.yml`
- **Line(s)**: 232-234
- **Severity**: Minor
- **Issue**: The Skill Generation section documents step skills but doesn't mention workflow meta-skills which also get generated (`expert-name.workflow-name/SKILL.md`).
- **Suggestion**: Add a line clarifying workflow meta-skill naming: "Workflow meta-skill: `.claude/skills/[expert-name].[workflow-name]/SKILL.md`"

### Issue 5
- **File**: `src/deepwork/standard/experts/experts/expert.yml`
- **Line(s)**: 299-305
- **Severity**: Suggestion
- **Issue**: The "Common Patterns" section references `/experts.define` and `/experts.implement` but could be confusing since there are multiple workflows.
- **Suggestion**: Add clarification that `/experts` without a step suffix invokes the `new_workflow` meta-skill.

### Issue 6
- **File**: `src/deepwork/templates/claude/skill-workflow-meta.md.jinja`
- **Line(s)**: 90
- **Severity**: Minor
- **Issue**: The template uses `expert_name | replace('-', '_')` to convert back to folder naming. This transformation works for simple cases but could break with edge cases.
- **Suggestion**: Consider having the generator pass the original folder name to the template.

## Code Suggestions

### Suggestion 1: Fix outdated install message

**File**: `src/deepwork/cli/install.py`

Before:
```python
    console.print("[bold]Next steps:[/bold]")
    console.print("  1. Start your agent CLI (ex. [cyan]claude[/cyan] or [cyan]gemini[/cyan])")
    console.print("  2. Define your first workflow using [cyan]/deepwork-jobs.define[/cyan]")
```

After:
```python
    console.print("[bold]Next steps:[/bold]")
    console.print("  1. Start your agent CLI (ex. [cyan]claude[/cyan] or [cyan]gemini[/cyan])")
    console.print("  2. Define your first workflow using [cyan]/experts.define[/cyan]")
```

**Rationale**: The skill naming has changed from `deepwork-jobs.step` to `experts.step` as workflows are now owned by experts.

### Suggestion 2: Fix invalid agent reference in workflow

**File**: `src/deepwork/standard/experts/experts/workflows/new_workflow/workflow.yml`

Before:
```yaml
  - id: review_workflow_spec
    name: "Review Workflow Specification"
    description: "Review workflow.yml against quality criteria using a sub-agent for unbiased validation"
    instructions_file: steps/review_workflow_spec.md
    ...
    agent: general-purpose
    quality_criteria:
      - "Workflow name is lowercase with underscores, no spaces or special characters"
```

After:
```yaml
  - id: review_workflow_spec
    name: "Review Workflow Specification"
    description: "Review workflow.yml against quality criteria using a sub-agent for unbiased validation"
    instructions_file: steps/review_workflow_spec.md
    ...
    quality_criteria:
      - "Workflow name is lowercase with underscores, no spaces or special characters"
```

**Rationale**: `general-purpose` is not a valid expert name. The `quality_criteria` field alone triggers sub-agent validation without requiring expert context, which achieves the stated goal of "unbiased validation."

## Approval Status

**CHANGES_REQUESTED**

The invalid `agent: general-purpose` reference in the new_workflow workflow.yml is a blocking issue that will cause runtime failures when the generated skill tries to load a non-existent expert. This must be fixed before merging.
