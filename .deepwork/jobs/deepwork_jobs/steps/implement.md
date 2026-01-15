# Implement Job Steps

## Objective

Generate step instruction files for each step based on the `job.yml` specification created in the define step.

**Reference**: See `deepwork_jobs.md` for job structure, step instruction format, and templates.

## Task

Read the `job.yml` specification and create instruction files to make the job functional.

### Step 1: Create Directory Structure (if needed)

If directory doesn't exist, run:
```bash
.deepwork/jobs/deepwork_jobs/make_new_job.sh [job_name]
```

Or manually create missing directories:
```bash
mkdir -p .deepwork/jobs/[job_name]/hooks .deepwork/jobs/[job_name]/templates
touch .deepwork/jobs/[job_name]/hooks/.gitkeep .deepwork/jobs/[job_name]/templates/.gitkeep
```

### Step 2: Read and Validate Specification

1. Read `.deepwork/jobs/[job_name]/job.yml`
2. Validate schema (name, version, summary, description, steps)
3. Check dependencies reference existing steps, no circular dependencies
4. Extract job name, version, summary, description, and step details

### Step 3: Generate Step Instruction Files

For each step, create `.deepwork/jobs/[job_name]/steps/[step_id].md`.

**Templates**: See `.deepwork/jobs/deepwork_jobs/templates/step_instruction.md.template` and `step_instruction.md.example`

**Guidelines:**
- Use the job description for context
- Be specific, not generic
- Provide output examples
- Explain the "why"
- Align quality criteria with stop hooks

### Handling Stop Hooks

If step has `stop_hooks`, the instruction file's Quality Criteria section must match what hooks validate. Include the promise pattern: `<promise>✓ Quality Criteria Met</promise>`

### Step 4: Sync Commands

```bash
deepwork sync
```

### Step 5: Relay Reload Instructions

Tell user how to reload commands:
- **Claude Code**: Type `exit` then run `claude --resume`
- **Gemini CLI**: Run `/memory refresh`

### Step 6: Consider Policies

Think about whether policies would help maintain consistency for this job's domain.

**Policies** are guardrails in `.deepwork.policy.yml` that trigger when files change.

Consider:
- Does this job produce outputs other files depend on?
- Should documentation be updated when outputs change?
- Are there quality checks that should happen on certain file changes?

If policies would help, explain what they'd do and offer to run `/deepwork_policy.define`.

## Completion Checklist

- [ ] job.yml validated
- [ ] All step instruction files created (complete, not stubs)
- [ ] Each instruction is specific and actionable
- [ ] Output examples provided
- [ ] `deepwork sync` executed
- [ ] User informed about reload instructions
- [ ] Policies considered (suggest if relevant)

## Quality Criteria

- Job directory structure correct
- All instruction files complete (not stubs)
- Instructions specific and actionable
- Output examples provided
- Quality criteria defined for each step
- Sync completed successfully
- Commands available for use
- Policies thoughtfully considered
