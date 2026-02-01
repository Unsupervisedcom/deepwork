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
