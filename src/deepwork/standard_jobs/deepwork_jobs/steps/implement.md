# Implement Job Steps

## Objective

Generate step instruction files for each step based on the validated `job.yml` specification from the review_job_spec step.

## Task

Read the `job.yml` specification file and create all the necessary step instruction files to make the job functional. Then sync the commands to make them available.

**Note:** The `define` step already creates the directory structure using `make_new_job.sh`, so you don't need to create directories here.

### Step 1: Read and Validate the Specification

1. **Locate the job.yml file**
   - Read `.deepwork/jobs/[job_name]/job.yml` from the review_job_spec step
   - Parse the YAML content

2. **Validate the specification**
   - Ensure it follows the schema (name, version, summary, description, steps)
   - Check that all dependencies reference existing steps
   - Verify no circular dependencies
   - Confirm file inputs match dependencies

3. **Extract key information**
   - Job name, version, summary, description
   - List of all steps with their details
   - Understand the workflow structure

### Step 2: Generate Step Instruction Files

For each step in the job.yml, create a comprehensive instruction file at `.deepwork/jobs/[job_name]/steps/[step_id].md`.

**Template reference**: See `.deepwork/jobs/deepwork_jobs/templates/step_instruction.md.template` for the standard structure.

**Complete example**: See `.deepwork/jobs/deepwork_jobs/templates/step_instruction.md.example` for a fully worked example.

**Available templates in `.deepwork/jobs/deepwork_jobs/templates/`:**
- `job.yml.template` - Job specification structure
- `step_instruction.md.template` - Step instruction file structure
- `agents.md.template` - AGENTS.md file structure
- `job.yml.example` - Complete job specification example
- `step_instruction.md.example` - Complete step instruction example

**Guidelines for generating instructions:**

1. **Use the job description** - The detailed description from job.yml provides crucial context
2. **Be specific** - Don't write generic instructions; tailor them to the step's purpose
3. **Provide examples** - Show what good output looks like
4. **Explain the "why"** - Help the user understand the step's role in the workflow
5. **Quality over quantity** - Detailed, actionable instructions are better than vague ones
6. **Align with stop hooks** - If the step has `stop_hooks` defined, ensure the quality criteria in the instruction file match the validation criteria in the hooks
7. **Ask structured questions** - When a step has user inputs, the instructions MUST explicitly tell the agent to "ask structured questions" using the AskUserQuestion tool to gather that information. Never use generic phrasing like "ask the user" - always use "ask structured questions"
8. **Reference tool documentation** - When a step requires external tools, include a reference to the relevant tool documentation created in the `tools` step. See the section below on "Incorporating Tool Documentation"

### Handling Stop Hooks

If a step in the job.yml has `stop_hooks` defined, the generated instruction file should:

1. **Mirror the quality criteria** - The "Quality Criteria" section should match what the stop hooks will validate
2. **Be explicit about success** - Help the agent understand when the step is truly complete
3. **Include the promise pattern** - Mention that `<promise>✓ Quality Criteria Met</promise>` should be included when criteria are met

**Example: If the job.yml has:**
```yaml
- id: research_competitors
  name: "Research Competitors"
  stop_hooks:
    - prompt: |
        Verify the research meets criteria:
        1. Each competitor has at least 3 data points
        2. Sources are cited
        3. Information is current (within last year)
```

**The instruction file should include:**
```markdown
## Quality Criteria

- Each competitor has at least 3 distinct data points
- All information is sourced with citations
- Data is current (from within the last year)
- When all criteria are met, include `<promise>✓ Quality Criteria Met</promise>` in your response
```

This alignment ensures the AI agent knows exactly what will be validated and can self-check before completing.

### Using Supplementary Reference Files

Step instructions can include additional `.md` files in the `steps/` directory for detailed examples, templates, or reference material. Reference them using the full path from the project root.

See `.deepwork/jobs/deepwork_jobs/steps/supplemental_file_references.md` for detailed documentation and examples.

### Incorporating Tool Documentation

The `tools` step (which runs before `implement`) creates process-focused documentation in `.deepwork/jobs/[job_name]/tools/`. When generating step instructions, **reference these tool documents** for any step that requires external tools.

**How to incorporate tool documentation:**

1. **Check what tools/ documents exist:**
   ```bash
   ls .deepwork/jobs/[job_name]/tools/
   ```

2. **Reference relevant documents in step instructions:**
   When a step uses an external tool (e.g., PDF generation, image processing), add a reference like:

   ```markdown
   ## Required Tools

   This step requires external tools. See the following documentation for usage:
   - [Creating PDFs](../tools/making_pdfs.md) - How to generate PDF output
   - [Processing Images](../tools/resizing_images.md) - How to resize and optimize images
   ```

3. **Include key commands inline when helpful:**
   For frequently-used commands, you can quote the essential invocation from the tool docs:

   ```markdown
   To convert markdown to PDF, use:
   ```bash
   pandoc input.md -o output.pdf --pdf-engine=xelatex
   ```
   See [Making PDFs](../tools/making_pdfs.md) for full documentation and troubleshooting.
   ```

**Why this matters:**
- Step instructions stay focused on workflow logic
- Tool details are documented once and referenced everywhere
- If tools change, only the tools/ docs need updating
- New users can refer to tool docs for installation help

### Step 3: Verify job.yml Location

Verify that `job.yml` is in the correct location at `.deepwork/jobs/[job_name]/job.yml`. The define and review_job_spec steps should have created and validated it. If for some reason it's not there, you may need to create or move it.

### Step 4: Sync Skills

Run `deepwork sync` to generate the skills for this job:

```bash
deepwork sync
```

This will:
- Parse the job definition
- Generate skills for each step
- Make the skills available in `.claude/skills/` (or appropriate platform directory)

### Step 5: Relay Reload Instructions

After running `deepwork sync`, look at the "To use the new skills" section in the output. **Relay these exact reload instructions to the user** so they know how to pick up the new skills. Don't just reference the sync output - tell them directly what they need to do (e.g., "Type 'exit' then run 'claude --resume'" for Claude Code, or "Run '/memory refresh'" for Gemini CLI).

### Step 6: Consider Rules for the New Job

After implementing the job, consider whether there are **rules** that would help enforce quality or consistency when working with this job's domain.

**What are rules?**

Rules are automated guardrails stored as markdown files in `.deepwork/rules/` that trigger when certain files change during an AI session. They help ensure:
- Documentation stays in sync with code
- Team guidelines are followed
- Architectural decisions are respected
- Quality standards are maintained

**When to suggest rules:**

Think about the job you just implemented and ask:
- Does this job produce outputs that other files depend on?
- Are there documentation files that should be updated when this job's outputs change?
- Are there quality checks or reviews that should happen when certain files in this domain change?
- Could changes to the job's output files impact other parts of the project?

**Examples of rules that might make sense:**

| Job Type | Potential Rule |
|----------|----------------|
| API Design | "Update API docs when endpoint definitions change" |
| Database Schema | "Review migrations when schema files change" |
| Competitive Research | "Update strategy docs when competitor analysis changes" |
| Feature Development | "Update changelog when feature files change" |
| Configuration Management | "Update install guide when config files change" |

**How to offer rule creation:**

If you identify one or more rules that would benefit the user, explain:
1. **What the rule would do** - What triggers it and what action it prompts
2. **Why it would help** - How it prevents common mistakes or keeps things in sync
3. **What files it would watch** - The trigger patterns

Then ask the user:

> "Would you like me to create this rule for you? I can run `/deepwork_rules.define` to set it up."

If the user agrees, invoke the `/deepwork_rules.define` command to guide them through creating the rule.

**Example dialogue:**

```
Based on the competitive_research job you just created, I noticed that when
competitor analysis files change, it would be helpful to remind you to update
your strategy documentation.

I'd suggest a rule like:
- **Name**: "Update strategy when competitor analysis changes"
- **Trigger**: `**/positioning_report.md`
- **Action**: Prompt to review and update `docs/strategy.md`

Would you like me to create this rule? I can run `/deepwork_rules.define` to set it up.
```

**Note:** Not every job needs rules. Only suggest them when they would genuinely help maintain consistency or quality. Don't force rules where they don't make sense.

## Example Implementation

For a complete worked example showing a job.yml and corresponding step instruction file, see:
- **Job specification**: `.deepwork/jobs/deepwork_jobs/templates/job.yml.example`
- **Step instruction**: `.deepwork/jobs/deepwork_jobs/templates/step_instruction.md.example`

## Important Guidelines

1. **Read the spec carefully** - Understand the job's intent from the description
2. **Generate complete instructions** - Don't create placeholder or stub files
3. **Maintain consistency** - Use the same structure for all step instruction files
4. **Provide examples** - Show what good output looks like
5. **Use context** - The job description provides valuable context for each step
6. **Be specific** - Tailor instructions to the specific step, not generic advice

## Validation Before Sync

Before running `deepwork sync`, verify:
- All directories exist
- `job.yml` is in place
- All step instruction files exist (one per step)
- No file system errors

## Completion Checklist

Before marking this step complete, ensure:
- [ ] job.yml validated and copied to job directory
- [ ] All step instruction files created
- [ ] Each instruction file is complete and actionable
- [ ] Steps requiring external tools reference tools/ documentation
- [ ] `deepwork sync` executed successfully
- [ ] Skills generated in platform directory
- [ ] User informed to follow reload instructions from `deepwork sync`
- [ ] Considered whether rules would benefit this job (Step 6)
- [ ] If rules suggested, offered to run `/deepwork_rules.define`

## Quality Criteria

- Job directory structure is correct
- All instruction files are complete (not stubs)
- Instructions are specific and actionable
- Output examples are provided in each instruction file
- Quality criteria defined for each step
- Steps with user inputs explicitly use "ask structured questions" phrasing
- Steps requiring external tools reference the appropriate tools/ documentation
- Sync completed successfully
- Skills available for use
- Thoughtfully considered relevant rules for the job domain
