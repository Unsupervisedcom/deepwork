# Learn from Job Execution

## Objective

Reflect on the conversation to identify learnings from DeepWork job executions, improve job instructions with generalizable insights, and capture bespoke (run-specific) learnings in AGENTS.md.

**Reference**: See `deepwork_jobs.md` for job structure and templates.

## Task

Analyze conversation history to extract learnings:
- **Generalizable learnings** → Update job instruction files
- **Bespoke learnings** (specific to this run) → Add to AGENTS.md in working folder

### Step 1: Analyze Conversation

1. Scan for DeepWork slash commands (`/job_name.step_id`)
2. Identify working folder from conversation or `git diff`
3. If no job specified, ask user which job to analyze

### Step 2: Identify Issues

Look for:
- **Confusion** - Unnecessary questions, misunderstandings, incorrect outputs
- **Inefficiency** - Extra iterations, repeated information, missing context
- **Errors** - Failed validations, misunderstood criteria, unhandled edge cases
- **Successes** - What worked well, efficient approaches, good examples

### Step 3: Classify Learnings

**Generalizable** (update instructions):
- Helps ANY future run
- Fixes unclear/missing guidance
- Adds helpful examples
- Example: "Instructions should mention X format is required"

**Bespoke** (add to AGENTS.md):
- Specific to THIS project/codebase
- References local conventions/files
- Example: "API endpoints are in `src/api/`"

### Step 4: Update Instructions (Generalizable)

1. Edit `.deepwork/jobs/[job_name]/steps/[step_id].md`
2. Add missing context, examples, clarifications
3. Keep concise - avoid redundancy
4. Track changes for changelog

### Step 4b: Extract Shared Content

Review instruction files for duplicated or lengthy content. Extract to `.deepwork/jobs/[job_name]/steps/shared/`:
- `conventions.md` - Formatting conventions
- `examples.md` - Common examples
- `schemas.md` - Data structures

Reference from instructions: "Follow conventions in `shared/conventions.md`"

### Step 5: Create/Update AGENTS.md (Bespoke)

Place AGENTS.md in the working folder where job outputs live.

**Use file references** instead of duplicating content:
```markdown
# Good
- API endpoints follow REST conventions. See `src/api/routes.ts` for examples.

# Avoid
- API endpoints should return JSON with format: { status: ..., data: ... }
```

**Template**: See `.deepwork/jobs/deepwork_jobs/templates/agents.md.template`

### Step 6: Update Version and Changelog

If instructions modified:
1. Bump version in job.yml (patch for improvements, minor for criteria changes)
2. Add changelog entry

### Step 7: Sync and Relay

```bash
deepwork sync
```

Tell user how to reload commands.

## Quality Criteria

- Conversation analyzed for job executions
- Confusion and inefficiency identified
- Learnings correctly classified (generalizable vs bespoke)
- Instructions updated for generalizable improvements
- Instructions concise - no redundancy
- Shared content extracted where appropriate
- AGENTS.md created/updated with bespoke learnings
- File references used instead of duplicating content
- AGENTS.md in correct working folder
- When all criteria are met, include `<promise>✓ Quality Criteria Met</promise>`

## Edge Cases

- **No job executions found**: Ask which job to analyze
- **Multiple jobs**: Analyze each separately
- **AGENTS.md exists**: Append to appropriate sections
- **No issues found**: Document what worked well
- **Sensitive info**: Never include secrets/credentials - reference config files instead
