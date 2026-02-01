---
name: deepwork_jobs.learn
description: "Analyzes conversation history to improve job instructions and capture learnings. Use after running a job to refine it."
context: fork
agent: deepwork-jobs

---

# deepwork_jobs.learn

**Standalone skill** - can be run anytime

> Creates and manages multi-step AI workflows. Use when defining, implementing, or improving DeepWork jobs.


## Instructions

**Goal**: Analyzes conversation history to improve job instructions and capture learnings. Use after running a job to refine it.

# Learn from Job Execution

## Objective

Reflect on the current conversation to identify learnings from DeepWork job executions, improve job instructions with generalizable insights, and capture bespoke learnings in AGENTS.md.

## Task

Analyze the conversation history to extract learnings and apply them appropriately:
- **Generalizable learnings** -> Update job instruction files
- **Bespoke learnings** (run-specific) -> Add to AGENTS.md

### Step 1: Analyze Conversation for Job Executions

1. **Scan for DeepWork commands** - Look for `/job_name.step_id` patterns
2. **Identify the target folder** - Deepest common folder for future work on this topic
3. **If no job specified**, ask the user which job to analyze

### Step 2: Identify Issues

Review the conversation for:

**Confusion signals**:
- Unnecessary questions from the agent
- Misunderstandings about step requirements
- Incorrect outputs needing correction

**Inefficiency signals**:
- Extra iterations needed
- Information repeated multiple times
- Missing context or dependencies

**Error patterns**:
- Failed validations and why
- Misunderstood quality criteria
- Unhandled edge cases

**Success patterns**:
- What worked well
- Efficient approaches to preserve

### Step 3: Classify Learnings

**Generalizable** (update instructions):
- Would help ANY future run of this job
- Addresses unclear or missing guidance
- Adds helpful examples

**Doc spec-related** (update doc spec files):
- Improvements to document quality criteria
- Changes to document structure
- Updated audience or format info

**Bespoke** (add to AGENTS.md):
- Specific to THIS project/codebase/run
- References specific files or paths
- Local conventions

### Step 4: Update Job Instructions

For generalizable learnings:

1. Edit `.deepwork/jobs/[job_name]/steps/[step_id].md`
2. Make targeted improvements - add context, examples, clarify ambiguity
3. Keep instructions concise - no redundancy
4. Preserve structure (Objective, Task, Output Format, Quality Criteria)
5. Note changes for changelog

**Extract shared content**: If content appears in multiple steps, move to `.deepwork/jobs/[job_name]/steps/shared/`.

### Step 5: Update Doc Spec Files (If Applicable)

If doc spec learnings were identified:

1. Find doc spec references in job.yml outputs
2. Update quality criteria with clearer requirements
3. Update example document if structure changed
4. Update metadata (audience, frequency, paths)

### Step 6: Create/Update AGENTS.md

For bespoke learnings:

1. **Determine location** - Deepest common folder for the topic
2. **Use file references** - Link to source files rather than duplicating content
3. **Structure**: See `.deepwork/jobs/deepwork_jobs/templates/agents.md.template`

**Good patterns** (references):
```markdown
- API endpoints follow REST conventions. See `src/api/routes.ts` for examples.
- Error handling pattern: See `src/utils/errors.ts:15-30`
```

**Avoid** (duplicating):
```markdown
- API endpoints should return JSON with this format: { status: ..., data: ... }
```

### Step 7: Update Job Version and Changelog

If instruction files were modified:

1. Bump version (patch for improvements, minor for criteria changes)
2. Add changelog entry:
   ```yaml
   - version: "[new_version]"
     changes: "Improved [step] based on execution learnings: [brief description]"
   ```

### Step 8: Sync Skills

If instructions were modified:
```bash
deepwork sync
```

## Quality Criteria

- Conversation analyzed for job executions
- Learnings correctly classified (generalizable vs bespoke)
- Instructions updated for generalizable improvements
- Instructions remain concise
- Shared content extracted where appropriate
- AGENTS.md in correct folder with file references
- Sync complete if instructions modified
- When complete: `<promise>Quality Criteria Met</promise>`

## Edge Cases

**No job executions found**: Ask user which job to analyze

**Multiple jobs executed**: Analyze each separately

**AGENTS.md exists**: Read existing, append new learnings, update "Last Updated"

**No issues found**: Document what worked well, consider adding as examples

**Sensitive information**: Never include secrets or PII - reference config files instead


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
- **job_name**: Name of the job that was run (optional - will auto-detect from conversation)


## Work Branch

Use branch format: `deepwork/deepwork_jobs-[instance]-YYYYMMDD`

- If on a matching work branch: continue using it
- If on main/master: create new branch with `git checkout -b deepwork/deepwork_jobs-[instance]-$(date +%Y%m%d)`

## Outputs

**Required outputs**:
- `AGENTS.md`

## Guardrails

- Do NOT skip prerequisite verification if this step has dependencies
- Do NOT produce partial outputs; complete all required outputs before finishing
- Do NOT proceed without required inputs; ask the user if any are missing
- Do NOT modify files outside the scope of this step's defined outputs

## Quality Validation

**Before completing this step, you MUST have your work reviewed against the quality criteria below.**

Use a sub-agent (Haiku model) to review your work against these criteria:

**Criteria (all must be satisfied)**:
1. **Conversation Analyzed**: Did the agent review the conversation for DeepWork job executions?
2. **Confusion Identified**: Did the agent identify points of confusion, errors, or inefficiencies?
3. **Instructions Improved**: Were job instructions updated to address identified issues?
4. **Instructions Concise**: Are instructions free of redundancy and unnecessary verbosity?
5. **Shared Content Extracted**: Is lengthy/duplicated content extracted into referenced files?
6. **doc spec Reviewed (if applicable)**: For jobs with doc spec outputs, were doc spec-related learnings identified?
7. **doc spec Updated (if applicable)**: Were doc spec files updated with improved quality criteria or structure?
8. **Bespoke Learnings Captured**: Were run-specific learnings added to AGENTS.md?
9. **File References Used**: Do AGENTS.md entries reference other files where appropriate?
10. **Working Folder Correct**: Is AGENTS.md in the correct working folder for the job?
11. **Generalizable Separated**: Are generalizable improvements in instructions, not AGENTS.md?
12. **Sync Complete**: Has `deepwork sync` been run if instructions were modified?
**Review Process**:
1. Once you believe your work is complete, spawn a sub-agent using Haiku to review your work against the quality criteria above
2. The sub-agent should examine your outputs and verify each criterion is met
3. If the sub-agent identifies valid issues, fix them
4. Have the sub-agent review again until all valid feedback has been addressed
5. Only mark the step complete when the sub-agent confirms all criteria are satisfied

## On Completion

1. Verify outputs are created
2. Inform user: "learn complete, outputs: AGENTS.md"

This standalone skill can be re-run anytime.

---

**Reference files**: `.deepwork/jobs/deepwork_jobs/job.yml`, `.deepwork/jobs/deepwork_jobs/steps/learn.md`