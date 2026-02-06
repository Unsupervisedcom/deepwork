# Implement Job Steps

## Objective

Generate the DeepWork job directory structure and instruction files for each step based on the validated `job.yml` specification.

## Task

Read the `job.yml` specification and create all necessary files to make the job functional, then sync the commands.

### Step 1: Create Directory Structure

Run the `make_new_job.sh` script:

```bash
.deepwork/jobs/deepwork_jobs/make_new_job.sh [job_name]
```

This creates:
- `.deepwork/jobs/[job_name]/` - Main job directory
- `.deepwork/jobs/[job_name]/steps/` - Step instruction files
- `.deepwork/jobs/[job_name]/hooks/` - Custom validation scripts
- `.deepwork/jobs/[job_name]/templates/` - Example file formats
- `.deepwork/jobs/[job_name]/AGENTS.md` - Job management guidance

**Note**: If directory exists from define step, skip or just create missing subdirectories.

### Step 2: Read and Validate the Specification

1. Read `.deepwork/jobs/[job_name]/job.yml`
2. Validate: name, version, summary, description, steps are present
3. Check dependencies reference existing steps, no circular dependencies
4. Verify file inputs match dependencies

### Step 3: Generate Step Instruction Files

For each step in job.yml, create `.deepwork/jobs/[job_name]/steps/[step_id].md`.

**Reference**: See `.deepwork/jobs/deepwork_jobs/templates/step_instruction.md.template` for structure.

**Guidelines**:

1. **Use the job description** - It provides crucial context
2. **Be specific** - Tailor instructions to the step's purpose, not generic
3. **Provide examples** - Show what good output looks like
4. **Explain the "why"** - Help understand the step's role in the workflow
5. **Ask structured questions** - Steps with user inputs MUST explicitly tell the agent to "ask structured questions"
6. **Align with hooks** - If step has `stop_hooks`, ensure quality criteria match the hooks

Each instruction file should include:
- **Objective** - What this step accomplishes
- **Task** - Detailed process
- **Output Format** - Examples of expected outputs
- **Quality Criteria** - How to verify completion

### Step 4: Verify job.yml Location

Ensure `job.yml` is at `.deepwork/jobs/[job_name]/job.yml`.

### Step 5: Sync Skills

Run:

```bash
deepwork sync
```

This generates skills in `.claude/skills/` (or appropriate platform directory).

### Step 6: Consider Rules

After implementing, consider whether **rules** would help this job's domain.

**What are rules?** Automated guardrails that trigger when certain files change, ensuring:
- Documentation stays in sync
- Team guidelines are followed
- Quality standards are maintained

**When to suggest rules:**
- Does this job produce outputs that other files depend on?
- Are there docs that should update when outputs change?
- Could changes impact other parts of the project?

**Examples**:
| Job Type | Potential Rule |
|----------|----------------|
| API Design | "Update API docs when endpoint definitions change" |
| Competitive Research | "Update strategy docs when competitor analysis changes" |
| Feature Development | "Update changelog when feature files change" |

If you identify helpful rules, explain what they would do and offer: "Would you like me to create this rule? I can run `/deepwork_rules.define` to set it up."

**Note**: Not every job needs rules. Only suggest when genuinely helpful.

## Completion Checklist

- [ ] job.yml in correct location
- [ ] All step instruction files created (not stubs)
- [ ] Instructions are specific and actionable
- [ ] Output examples provided
- [ ] Quality criteria defined for each step
- [ ] `deepwork sync` executed successfully
- [ ] Considered relevant rules for this job
