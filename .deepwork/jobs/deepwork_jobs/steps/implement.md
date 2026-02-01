# Implement Job Steps

## Objective

Generate the DeepWork job directory structure and instruction files for each step based on the validated `job.yml` specification.

## Task

Read the `job.yml` specification and create all necessary files to make the job functional.

### Step 1: Create Directory Structure

Run the setup script:
```bash
.deepwork/jobs/deepwork_jobs/make_new_job.sh [job_name]
```

This creates:
- `.deepwork/jobs/[job_name]/steps/` - Step instruction files
- `.deepwork/jobs/[job_name]/hooks/` - Validation scripts
- `.deepwork/jobs/[job_name]/templates/` - Example file formats
- `.deepwork/jobs/[job_name]/AGENTS.md` - Job management guidance

**Note**: If directory already exists from define step, create missing subdirectories manually.

### Step 2: Read and Validate the Specification

1. Read `.deepwork/jobs/[job_name]/job.yml`
2. Validate structure (name, version, summary, description, steps)
3. Check dependencies are valid and non-circular
4. Extract step details for instruction generation

### Step 3: Generate Step Instruction Files

Create `.deepwork/jobs/[job_name]/steps/[step_id].md` for each step.

**Templates**:
- `.deepwork/jobs/deepwork_jobs/templates/step_instruction.md.template` - Structure
- `.deepwork/jobs/deepwork_jobs/templates/step_instruction.md.example` - Complete example

**Guidelines**:

1. **Use the job description** - It provides crucial context
2. **Be specific** - Tailor instructions to each step's purpose
3. **Provide examples** - Show what good output looks like
4. **Explain the "why"** - Help understand the step's role in the workflow
5. **Ask structured questions** - When a step has user inputs, MUST use this phrase
6. **Align with hooks** - If step has `hooks` defined, match quality criteria

**Handling Hooks**:

If a step has hooks defined, the instruction file should:
- Mirror the quality criteria that hooks will validate
- Be explicit about what success looks like
- Mention the `<promise>Quality Criteria Met</promise>` pattern when criteria are met

### Step 4: Verify job.yml Location

Confirm `job.yml` exists at `.deepwork/jobs/[job_name]/job.yml`.

### Step 5: Sync Skills

Run:
```bash
deepwork sync
```

This generates skills for each step in `.claude/skills/` (or platform-specific directory).

### Step 6: Consider Rules

After implementing, consider whether **rules** would help enforce quality.

**What are rules?**
Automated guardrails in `.deepwork/rules/` that trigger when files change.

**When to suggest rules**:
- Job produces outputs that other files depend on
- Documentation should stay in sync with outputs
- Quality checks should happen when certain files change

**Examples**:
| Job Type | Potential Rule |
|----------|----------------|
| API Design | Update docs when endpoints change |
| Database Schema | Review migrations when schema changes |
| Competitive Research | Update strategy when analysis changes |

If a rule would help, explain what it would do and offer to run `/deepwork_rules.define`.

## Completion Checklist

Before marking complete:
- [ ] job.yml validated and in place
- [ ] All step instruction files created (complete, not stubs)
- [ ] Instructions are specific and actionable
- [ ] Output examples provided
- [ ] Quality criteria defined for each step
- [ ] User input steps use "ask structured questions"
- [ ] `deepwork sync` executed successfully
- [ ] Skills available in platform directory
- [ ] Considered relevant rules for job domain

## Output

Complete step instruction files at `.deepwork/jobs/[job_name]/steps/` and synced skills.
