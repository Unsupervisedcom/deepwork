# DeepWork Template Design Review

This document presents the three Jinja2 templates for review. These templates are the **core interface between DeepWork and AI agents** - they must be correct before implementation can proceed.

## Overview

Three templates have been designed:

1. **`skill-job-step.md.jinja`** - Individual step skill (MOST CRITICAL)
2. **`skill-deepwork.define.md.jinja`** - Job definition wizard
3. **`skill-deepwork.refine.md.jinja`** - Job refinement tool

## Review Requirements

For approval, each template needs:
- ✅ Correct Claude Code skill format
- ✅ Clear instructions AI agents can follow
- ✅ Proper context passing between steps
- ✅ Good user experience
- ✅ Handles all cases (simple jobs, complex jobs, edge cases)

---

## Template 1: skill-job-step.md.jinja ⭐ MOST CRITICAL

**Purpose**: Generates individual skill files for each step in a job workflow.

**Location**: `src/deepwork/templates/claude/skill-job-step.md.jinja`

### Template Features

✅ **Follows Claude Code skill format**:
- Name: job.step
- Description
- Sections: Overview, Instructions, Inputs, Work Branch, Outputs, Completion

✅ **Handles all input types**:
- User parameters (name + description)
- File inputs from previous steps
- No inputs (template adapts)

✅ **Conditional sections**:
- Prerequisites (only if dependencies exist)
- Next step (only if not final step)
- Workflow complete (only for final step)

✅ **Clear work branch management**:
- Consistent naming: `work/[job_name]-[instance]-[date]`
- Instructions for checking/creating branches
- All outputs in work directory

✅ **Context preservation**:
- Embeds step instructions from .md file
- Lists required files with locations
- Points to job definition and step files

### Template Variables

```python
context = {
    "job_name": str,              # e.g., "competitive_research"
    "job_version": str,           # e.g., "1.0.0"
    "job_description": str,       # e.g., "Systematic competitive analysis workflow"

    "step_id": str,               # e.g., "primary_research"
    "step_name": str,             # e.g., "Primary Research"
    "step_description": str,      # e.g., "Analyze competitors' self-presentation"
    "step_number": int,           # e.g., 2
    "total_steps": int,           # e.g., 4

    "instructions_file": str,     # e.g., "steps/primary_research.md"
    "instructions_content": str,  # Full markdown content from the file

    "user_inputs": list[dict],    # [{"name": "param", "description": "..."}]
    "file_inputs": list[dict],    # [{"file": "data.md", "from_step": "step1"}]
    "outputs": list[str],         # ["output.md", "directory/"]
    "dependencies": list[str],    # ["step1", "step2"]

    "next_step": str | None,      # "step3" or None if final
    "prev_step": str | None,      # "step1" or None if first
}
```

### Rendered Examples

See full rendered examples:
- **Example 1**: Simple job with user inputs
  - File: `doc/template_examples/example1_simple_job_user_inputs.md`
  - Shows: Single-step job, user parameters, final step handling

- **Example 2**: Complex job with file inputs
  - File: `doc/template_examples/example2_complex_job_file_inputs.md`
  - Shows: Mid-workflow step, file dependencies, next step guidance

- **Example 3**: Final step with multiple inputs
  - File: `doc/template_examples/example3_final_step_multiple_inputs.md`
  - Shows: Multiple file inputs, multiple dependencies, workflow completion

### Key Design Decisions

1. **Work branch format**: `work/[job_name]-[instance]-[date]`
   - Allows multiple concurrent instances of same job
   - Clear namespace separation
   - Git-friendly naming

2. **File location references**: Always show full path `work/[branch-name]/file.md`
   - Prevents confusion about file locations
   - Makes it easy for AI to find inputs

3. **Step numbering**: "Step X of Y"
   - Gives user progress context
   - Helps AI understand workflow position

4. **Conditional sections**: Only show relevant information
   - No "Prerequisites" if first step
   - No "Next Step" if final step
   - Cleaner, less confusing output

5. **Embedded instructions**: Full step instructions in skill file
   - AI has all context in one place
   - Reduces file reads during execution
   - Single source of truth

### Potential Issues to Consider

🤔 **Questions for Review**:

1. **Work branch naming**: Is `work/[job_name]-[instance]-[date]` clear enough? Should we provide more guidance on what `[instance]` should be?

2. **File input locations**: Do we need to validate files exist before step starts? Or trust the AI to handle missing files gracefully?

3. **Instruction embedding**: Should we embed the full markdown content or just reference the file path?

4. **Error handling**: What should AI do if prerequisites aren't met? Should template include fallback instructions?

5. **Output directories**: How should AI handle directory outputs (ending with `/`)? Create empty dir or populate it?

---

## Template 2: skill-deepwork.define.md.jinja

**Purpose**: Interactive wizard to help users define new job workflows.

**Location**: `src/deepwork/templates/claude/skill-deepwork.define.md.jinja`

### Template Features

✅ **Step-by-step wizard**:
- Job metadata → Define steps → Review → Create

✅ **Validation rules**:
- Job name pattern
- Semantic versioning
- Dependency validation
- No circular dependencies

✅ **Helpful guidance**:
- Tips for breaking down workflows
- Examples of good step design
- Clear error messages

✅ **Complete file generation**:
- job.yml with full schema
- Step instruction files (.md)
- Skill files for all steps

### Template Structure

1. **Overview**: Explains what the wizard does
2. **Step 1**: Gather job metadata
3. **Step 2**: Define each workflow step
4. **Step 3**: Review and confirm
5. **Step 4**: Create all files
6. **Step 5**: Confirm completion

### Key Design Decisions

1. **Interactive approach**: Conversational wizard vs. single prompt
   - Easier for users to think through one step at a time
   - AI can validate as it goes
   - More user-friendly

2. **Validation points**: Validate early and often
   - Job name immediately after input
   - Dependencies when added
   - Full graph validation at review

3. **File generation**: Create everything atomically
   - All files created together
   - Reduces partial state issues
   - Clear success/failure

### Template Variables

This template doesn't use variables - it's static instructions for the AI agent.

### Example Usage Flow

```
User: /deepwork.define

AI: I'll help you define a new job! What would you like to call it?

User: competitive_research

AI: Great! What does this workflow accomplish?

User: Systematic competitive analysis

AI: Perfect! Now let's define the steps. What's the first step?

[... interactive dialog continues ...]

AI: ✓ Job "competitive_research" v1.0.0 has been defined!
```

### Potential Issues to Consider

🤔 **Questions for Review**:

1. **Complexity**: Is the wizard too complex? Should we support a "simple mode" for basic jobs?

2. **Step instruction creation**: Should AI help write step instructions or require user to provide them?

3. **Templates for outputs**: Should we support output templates (e.g., "Create a markdown file with these sections")?

4. **Validation feedback**: Are the validation rules clear enough for users to understand what's required?

---

## Template 3: skill-deepwork.refine.md.jinja

**Purpose**: Modify existing job definitions safely.

**Location**: `src/deepwork/templates/claude/skill-deepwork.refine.md.jinja`

### Template Features

✅ **Safe modifications**:
- Validates impact before changes
- Warns about breaking changes
- Prevents invalid states

✅ **Multiple operations**:
- Add/remove steps
- Modify instructions
- Update inputs/outputs
- Adjust dependencies
- Change metadata

✅ **Smart regeneration**:
- Only regenerates affected skills
- Updates step numbers when needed
- Maintains consistency

### Template Structure

1. **Overview**: Explains refinement capabilities
2. **Step 1**: Select job to refine
3. **Step 2**: Choose operation
4. **Step 3**: Make changes
5. **Step 4**: Regenerate skills
6. **Step 5**: Confirm changes

### Key Design Decisions

1. **Safety first**: Validate impact before allowing changes
   - Check if other steps depend on removed steps
   - Warn if breaking changes detected
   - Suggest fixes

2. **Selective regeneration**: Only update what changed
   - Faster for small changes
   - Preserves unchanged skills
   - Clear about what was modified

3. **Version guidance**: Help with semantic versioning
   - Major: Breaking changes
   - Minor: New features
   - Patch: Bug fixes

### Template Variables

This template doesn't use variables - it's static instructions for the AI agent.

### Example Usage Flow

```
User: /deepwork.refine

AI: Available jobs:
1. competitive_research v1.0.0
Which one?

User: 1

AI: What would you like to do?
1. Add a new step
2. Modify step instructions
[... options ...]

User: 1

AI: Where should I insert the new step?

[... continues ...]
```

### Potential Issues to Consider

🤔 **Questions for Review**:

1. **Breaking change detection**: Is the logic for detecting breaking changes comprehensive enough?

2. **Rollback support**: Should we support undo/rollback if changes break the job?

3. **Batch operations**: Should users be able to make multiple changes at once?

4. **Diff preview**: Should we show a diff before applying changes?

---

## Comparison with Existing Tools

### vs. GitHub Spec-Kit

DeepWork improves on spec-kit by:
- ✅ **Multi-step workflows** (spec-kit is single-task)
- ✅ **Dependency management** (spec-kit has no dependencies)
- ✅ **Reusable job definitions** (spec-kit is one-off)
- ✅ **Work branch organization** (spec-kit doesn't manage branches)

### vs. Manual Claude Prompts

DeepWork improves on manual prompts by:
- ✅ **Consistent structure** (no ad-hoc prompting)
- ✅ **Context preservation** (automatic file references)
- ✅ **Progress tracking** (clear step numbers)
- ✅ **Reproducibility** (same job definition works every time)

---

## Testing Plan

Once approved, these templates will be tested with:

1. **Unit tests**: Template rendering with various contexts
2. **Integration tests**: Full job definition → skill generation → execution
3. **Real-world examples**:
   - Simple single-step job
   - Complex multi-step job with dependencies
   - Job with mixed input types

---

## Approval Checklist

Before proceeding with implementation:

- [ ] Template 1 (skill-job-step): Approved
- [ ] Template 2 (deepwork.define): Approved
- [ ] Template 3 (deepwork.refine): Approved
- [ ] Rendered examples look correct
- [ ] No missing functionality identified
- [ ] Design questions resolved

---

## Next Steps After Approval

1. ✅ Templates are already created in `src/deepwork/templates/claude/`
2. Implement template renderer (Step 10)
3. Write unit tests for template rendering
4. Test with fixture jobs
5. Proceed to CLI implementation (Step 11)

---

## Files for Review

**Templates**:
- `src/deepwork/templates/claude/skill-job-step.md.jinja`
- `src/deepwork/templates/claude/skill-deepwork.define.md.jinja`
- `src/deepwork/templates/claude/skill-deepwork.refine.md.jinja`

**Examples**:
- `doc/template_examples/example1_simple_job_user_inputs.md`
- `doc/template_examples/example2_complex_job_file_inputs.md`
- `doc/template_examples/example3_final_step_multiple_inputs.md`

**This Review**:
- `doc/TEMPLATE_REVIEW.md`

---

**Ready for review!** Please provide feedback on:
1. Template structure and content
2. Design decisions
3. Any missing functionality
4. Answers to the "Questions for Review"
