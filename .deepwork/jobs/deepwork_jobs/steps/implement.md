# Implement Job Steps

## Objective

Generate the step instruction files for each step based on the validated `job.yml` specification, then sync to create the slash commands.

## Task

Read the job.yml and create comprehensive instruction files for each step.

### Process

1. **Create directory structure** (if needed)
   ```bash
   .deepwork/jobs/deepwork_jobs/make_new_job.sh [job_name]
   ```

2. **Read and validate the specification**
   - Read `.deepwork/jobs/[job_name]/job.yml`
   - Extract job name, description, and step details
   - Understand the workflow structure

3. **Generate step instruction files**
   - Create `.deepwork/jobs/[job_name]/steps/[step_id].md` for each step
   - Use templates in `.deepwork/jobs/deepwork_jobs/templates/` as reference
   - Each file must include: Objective, Task, Process, Output Format, Quality Criteria

4. **Sync skills**
   ```bash
   deepwork sync
   ```

5. **Consider rules for the new job**
   - Think about whether rules would help maintain quality
   - If relevant, explain and offer to run `/deepwork_rules.define`

### Instruction File Guidelines

- **Be specific** - tailor to each step's purpose, not generic advice
- **Provide examples** - show what good output looks like
- **Include quality criteria** - how to verify the step is complete
- **Use "ask structured questions"** - for steps that gather user input
- **Align with hooks** - if step has hooks, match the validation criteria

### Templates Available

- `job.yml.template` - Job specification structure
- `step_instruction.md.template` - Step instruction file structure
- `agents.md.template` - AGENTS.md file structure
- Examples: `job.yml.example`, `step_instruction.md.example`

## Completion Checklist

- [ ] All step instruction files created (not stubs)
- [ ] Instructions are specific and actionable
- [ ] Output examples provided
- [ ] Quality criteria defined
- [ ] `deepwork sync` executed successfully
- [ ] Rules considered (suggest if genuinely helpful)

## Output

Complete instruction files in `.deepwork/jobs/[job_name]/steps/` and synced skills in `.claude/skills/`.
