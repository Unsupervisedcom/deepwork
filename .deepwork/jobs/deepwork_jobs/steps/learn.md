# Learn from Job Execution

## Objective

Reflect on the current conversation to identify learnings from DeepWork job executions, improve job instructions with generalizable insights, and capture bespoke (run-specific) learnings in AGENTS.md files.

## Task

Analyze the conversation history to extract learnings and apply them appropriately:
- **Generalizable learnings** - Update job instruction files
- **Bespoke learnings** - Add to AGENTS.md in the deepest common folder for the topic

### Process

1. **Analyze conversation for job executions**
   - Scan for DeepWork slash commands (`/job_name.step_id`)
   - Identify which jobs and steps were executed
   - If unclear, run `git diff` to see where changes were made

2. **Identify issues and patterns**
   - **Confusion**: unnecessary questions, misunderstandings, incorrect outputs
   - **Inefficiency**: extra iterations, repeated information, missing context
   - **Errors**: failed validations, edge cases, quality criteria issues
   - **Successes**: what worked well, efficient approaches

3. **Classify each learning**
   - **Generalizable**: would help ANY future run (update instructions)
   - **Doc spec-related**: improves document quality criteria (update doc specs)
   - **Bespoke**: specific to THIS project/codebase (add to AGENTS.md)

4. **Update job instructions** (generalizable learnings)
   - Edit `.deepwork/jobs/[job_name]/steps/[step_id].md`
   - Keep concise - avoid redundancy
   - Extract shared content to `steps/shared/` if needed

5. **Update doc specs** (if applicable)
   - Edit `.deepwork/doc_specs/[doc_spec_name].md`
   - Update quality criteria or document structure

6. **Create/update AGENTS.md** (bespoke learnings)
   - Place in deepest common folder for the topic
   - Use file references instead of duplicating content
   - Pattern: "See `path/to/file.ext` for [description]"

7. **Update version and sync**
   - Bump version in job.yml (patch for instructions, minor for criteria)
   - Add changelog entry
   - Run `deepwork sync` if instructions were modified

### File Reference Patterns

**Good (references)**:
```markdown
- API endpoints follow REST conventions. See `src/api/routes.ts` for examples.
- Error handling pattern: See `src/utils/errors.ts:15-30`
```

**Avoid (duplicating)**:
```markdown
- API endpoints should return JSON with this format: { status: ..., data: ... }
```

## Output

- Updated instruction files (generalizable improvements)
- Updated doc specs (if applicable)
- AGENTS.md in the correct working folder (bespoke learnings)

Include `<promise>Quality Criteria Met</promise>` when complete.
