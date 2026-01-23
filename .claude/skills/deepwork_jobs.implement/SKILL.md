---
name: deepwork_jobs.implement
description: "Generates step instruction files and syncs slash commands from the job.yml specification. Use after tools verification passes."
user-invocable: false
hooks:
  Stop:
    - hooks:
        - type: prompt
          prompt: |
            You must evaluate whether Claude has met all the below quality criteria for the request.

            ## Quality Criteria

            1. **Directory Structure**: Is `.deepwork/jobs/[job_name]/` created correctly?
            2. **Complete Instructions**: Are ALL step instruction files complete (not stubs or placeholders)?
            3. **Specific & Actionable**: Are instructions tailored to each step's purpose, not generic?
            4. **Output Examples**: Does each instruction file show what good output looks like?
            5. **Quality Criteria**: Does each instruction file define quality criteria for its outputs?
            6. **Ask Structured Questions**: Do step instructions that gather user input explicitly use the phrase "ask structured questions"?
            7. **Techniques Referenced**: Do steps requiring external tools reference the appropriate techniques from `.deepwork/techniques/`?
            8. **Sync Complete**: Has `deepwork sync` been run successfully?
            9. **Commands Available**: Are the slash-commands generated in `.claude/commands/`?
            10. **Rules Considered**: Has the agent thought about whether rules would benefit this job? If relevant rules were identified, did they explain them and offer to run `/deepwork_rules.define`? Not every job needs rules - only suggest when genuinely helpful.

            ## Instructions

            Review the conversation and determine if ALL quality criteria above have been satisfied.
            Look for evidence that each criterion has been addressed.

            If the agent has included `<promise>✓ Quality Criteria Met</promise>` in their response OR
            all criteria appear to be met, respond with: {"ok": true}

            If criteria are NOT met AND the promise tag is missing, respond with:
            {"ok": false, "reason": "**AGENT: TAKE ACTION** - [which criteria failed and why]"}
  SubagentStop:
    - hooks:
        - type: prompt
          prompt: |
            You must evaluate whether Claude has met all the below quality criteria for the request.

            ## Quality Criteria

            1. **Directory Structure**: Is `.deepwork/jobs/[job_name]/` created correctly?
            2. **Complete Instructions**: Are ALL step instruction files complete (not stubs or placeholders)?
            3. **Specific & Actionable**: Are instructions tailored to each step's purpose, not generic?
            4. **Output Examples**: Does each instruction file show what good output looks like?
            5. **Quality Criteria**: Does each instruction file define quality criteria for its outputs?
            6. **Ask Structured Questions**: Do step instructions that gather user input explicitly use the phrase "ask structured questions"?
            7. **Techniques Referenced**: Do steps requiring external tools reference the appropriate techniques from `.deepwork/techniques/`?
            8. **Sync Complete**: Has `deepwork sync` been run successfully?
            9. **Commands Available**: Are the slash-commands generated in `.claude/commands/`?
            10. **Rules Considered**: Has the agent thought about whether rules would benefit this job? If relevant rules were identified, did they explain them and offer to run `/deepwork_rules.define`? Not every job needs rules - only suggest when genuinely helpful.

            ## Instructions

            Review the conversation and determine if ALL quality criteria above have been satisfied.
            Look for evidence that each criterion has been addressed.

            If the agent has included `<promise>✓ Quality Criteria Met</promise>` in their response OR
            all criteria appear to be met, respond with: {"ok": true}

            If criteria are NOT met AND the promise tag is missing, respond with:
            {"ok": false, "reason": "**AGENT: TAKE ACTION** - [which criteria failed and why]"}
---

# deepwork_jobs.implement

**Step 4/5** in **deepwork_jobs** workflow

> Creates and manages multi-step AI workflows. Use when defining, implementing, or improving DeepWork jobs.

## Prerequisites (Verify First)

Before proceeding, confirm these steps are complete:
- `/deepwork_jobs.review_job_spec`
- `/deepwork_jobs.tools`

## Instructions

**Goal**: Generates step instruction files and syncs slash commands from the job.yml specification. Use after tools verification passes.

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
8. **Reference techniques** - When a step requires external tools, include a reference to the relevant technique created in the `tools` step. See the section below on "Incorporating Techniques"

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

### Incorporating Techniques

The `tools` step (which runs before `implement`) creates reusable techniques in `.deepwork/techniques/`. When generating step instructions, **reference these techniques** for any step that requires external tools.

Techniques are synced to platform skill directories with a `dw_` prefix (e.g., `making_pdfs` becomes `/dwt_making_pdfs`), so agents can invoke them directly.

**How to incorporate techniques:**

1. **Check what techniques exist:**
   ```bash
   ls .deepwork/techniques/
   ```

2. **Reference relevant techniques in step instructions:**
   When a step uses an external tool (e.g., PDF generation, image processing), add a reference like:

   ```markdown
   ## Required Techniques

   This step requires external tools. Use the following techniques:
   - `/dwt_making_pdfs` - How to generate PDF output
   - `/dwt_resizing_images` - How to resize and optimize images

   See `.deepwork/techniques/[technique_name]/SKILL.md` for detailed usage instructions.
   ```

3. **Include key commands inline when helpful:**
   For frequently-used commands, you can quote the essential invocation from the technique:

   ```markdown
   To convert markdown to PDF, use:
   ```bash
   pandoc input.md -o output.pdf --pdf-engine=xelatex
   ```
   See `/dwt_making_pdfs` (or `.deepwork/techniques/making_pdfs/SKILL.md`) for full documentation and troubleshooting.
   ```

**Why this matters:**
- Step instructions stay focused on workflow logic
- Techniques are documented once and synced to all platforms
- Agents can invoke techniques directly as skills (e.g., `/dwt_making_pdfs`)
- If techniques change, only the `.deepwork/techniques/` folder needs updating
- New users can refer to technique SKILL.md files for installation help

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
- [ ] Steps requiring external tools reference techniques from `.deepwork/techniques/`
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
- Steps requiring external tools reference the appropriate techniques from `.deepwork/techniques/`
- Sync completed successfully
- Skills available for use
- Thoughtfully considered relevant rules for the job domain


### Job Context

Core commands for managing DeepWork jobs. These commands help you define new multi-step
workflows and learn from running them.

The `define` command guides you through an interactive process to create a new job by
asking structured questions about your workflow, understanding each step's inputs and outputs,
and generating all necessary files.

The `learn` command reflects on conversations where DeepWork jobs were run, identifies
confusion or inefficiencies, and improves job instructions. It also captures bespoke
learnings specific to the current run into AGENTS.md files in the working folder.


## Required Inputs


**Files from Previous Steps** - Read these first:
- `job.yml` (from `review_job_spec`)

## Work Branch

Use branch format: `deepwork/deepwork_jobs-[instance]-YYYYMMDD`

- If on a matching work branch: continue using it
- If on main/master: create new branch with `git checkout -b deepwork/deepwork_jobs-[instance]-$(date +%Y%m%d)`

## Outputs

**Required outputs**:
- `steps/` (directory)

## Guardrails

- Do NOT skip prerequisite verification if this step has dependencies
- Do NOT produce partial outputs; complete all required outputs before finishing
- Do NOT proceed without required inputs; ask the user if any are missing
- Do NOT modify files outside the scope of this step's defined outputs

## Quality Validation

Stop hooks will automatically validate your work. The loop continues until all criteria pass.

**Criteria (all must be satisfied)**:
1. **Directory Structure**: Is `.deepwork/jobs/[job_name]/` created correctly?
2. **Complete Instructions**: Are ALL step instruction files complete (not stubs or placeholders)?
3. **Specific & Actionable**: Are instructions tailored to each step's purpose, not generic?
4. **Output Examples**: Does each instruction file show what good output looks like?
5. **Quality Criteria**: Does each instruction file define quality criteria for its outputs?
6. **Ask Structured Questions**: Do step instructions that gather user input explicitly use the phrase "ask structured questions"?
7. **Techniques Referenced**: Do steps requiring external tools reference the appropriate techniques from `.deepwork/techniques/`?
8. **Sync Complete**: Has `deepwork sync` been run successfully?
9. **Commands Available**: Are the slash-commands generated in `.claude/commands/`?
10. **Rules Considered**: Has the agent thought about whether rules would benefit this job? If relevant rules were identified, did they explain them and offer to run `/deepwork_rules.define`? Not every job needs rules - only suggest when genuinely helpful.


**To complete**: Include `<promise>✓ Quality Criteria Met</promise>` in your final response only after verifying ALL criteria are satisfied.

## On Completion

1. Verify outputs are created
2. Inform user: "Step 4/5 complete, outputs: steps/"
3. **Continue workflow**: Use Skill tool to invoke `/deepwork_jobs.learn`

---

**Reference files**: `.deepwork/jobs/deepwork_jobs/job.yml`, `.deepwork/jobs/deepwork_jobs/steps/implement.md`