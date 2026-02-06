---
name: deepwork_jobs.learn
description: "Analyzes conversation history to improve job instructions and capture learnings. Use after running a job to refine it."
context: fork
agent: experts

---

# deepwork_jobs.learn

**Standalone skill** - can be run anytime

> Creates and manages multi-step AI workflows. Use when defining, implementing, or improving DeepWork jobs.


## Instructions

**Goal**: Analyzes conversation history to improve job instructions and capture learnings. Use after running a job to refine it.

# Learn from Job Execution

## Objective

Reflect on the conversation to identify learnings from DeepWork job executions, improve job instructions with generalizable insights, and capture run-specific learnings in AGENTS.md files.

## Task

Analyze conversation history to extract learnings, then apply them:
- **Generalizable learnings** -> Update job instruction files
- **Bespoke learnings** (run-specific) -> Add to AGENTS.md in the working folder

### Step 1: Analyze Conversation for Job Executions

1. **Scan the conversation** for DeepWork slash commands (`/job_name.step_id`)
2. **Identify the target folder** - the deepest common folder for all work on the topic
3. **If no job specified**, ask which job to learn from

### Step 2: Identify Confusion and Inefficiency

Review the conversation for:

**Confusion signals**:
- Unnecessary questions the agent asked
- Misunderstandings about step requirements
- Incorrect outputs needing correction
- Ambiguous instructions causing wrong interpretations

**Inefficiency signals**:
- Extra iterations needed
- Repeated information
- Missing context
- Unclear dependencies

**Error patterns**:
- Failed validations and why
- Misunderstood quality criteria
- Unhandled edge cases

**Success patterns**:
- What worked well
- Efficient approaches worth preserving
- Good examples to add to instructions

### Step 3: Classify Learnings

For each learning, determine if it is:

**Generalizable** (update instructions):
- Would help ANY future run of this job
- Addresses unclear or missing guidance
- Fixes incorrect assumptions
- Adds helpful examples

**Doc spec-related** (update doc spec files):
- Improvements to document quality criteria
- Changes to document structure or format

**Bespoke** (add to AGENTS.md):
- Specific to THIS project/codebase/run
- Depends on local conventions
- References specific files or paths
- Would not apply to other uses

### Step 4: Update Job Instructions (Generalizable)

For each generalizable learning:

1. Locate `.deepwork/jobs/[job_name]/steps/[step_id].md`
2. Make targeted improvements:
   - Add missing context
   - Include helpful examples
   - Clarify ambiguous instructions
   - Update quality criteria
3. Keep instructions concise - avoid redundancy
4. Preserve structure (Objective, Task, Output Format, Quality Criteria)

### Step 5: Update Doc Specs (if applicable)

If doc spec-related learnings identified:

1. Locate doc spec at `.deepwork/doc_specs/[doc_spec_name].md`
2. Update quality_criteria, example document, or metadata as needed

### Step 6: Create/Update AGENTS.md (Bespoke)

1. Place in the deepest common folder for the topic
2. Use file references instead of duplicating content: "See `path/to/file.ext` for [description]"
3. Follow structure in `.deepwork/jobs/deepwork_jobs/templates/agents.md.template`

**Good patterns** (references):
```markdown
- API endpoints follow REST conventions. See `src/api/routes.ts` for examples.
- Configuration schema: Defined in `config/schema.json`
```

**Avoid** (duplicating):
```markdown
- API endpoints should return JSON with this format: { status: ..., data: ... }
```

### Step 7: Update Job Version and Sync

If instructions were modified:

1. Bump version in job.yml (patch for improvements, minor for quality criteria changes)
2. Add changelog entry
3. Run `deepwork sync`

## Output

- Updated job instructions (generalizable learnings)
- Updated doc specs (if applicable)
- AGENTS.md with bespoke learnings in the correct working folder


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

## On Completion

1. Verify outputs are created
2. Inform user: "learn complete, outputs: AGENTS.md"

This standalone skill can be re-run anytime.

---

**Reference files**: `.deepwork/jobs/deepwork_jobs/job.yml`, `.deepwork/jobs/deepwork_jobs/steps/learn.md`