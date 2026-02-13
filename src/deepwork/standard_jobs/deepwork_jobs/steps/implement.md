# Implement Job Steps

## Objective

Generate step instruction files for each step based on the `job.yml` specification from the define step.

## Task

Read the `job.yml` specification file created by the define step and generate comprehensive instruction files for each step. The define step has already created the job directory structure.

### Step 1: Read and Validate the Specification

1. **Locate the job.yml file**
   - Read `.deepwork/jobs/[job_name]/job.yml` from the define step
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

**Template reference**: See `<job_dir>/templates/step_instruction.md.template` for the standard structure.

**Complete example**: See `<job_dir>/templates/step_instruction.md.example` for a fully worked example.

**Available templates in `<job_dir>/templates/`** (replace `<job_dir>` with the `job_dir` path from the workflow response):
- `job.yml.template` - Job specification structure
- `step_instruction.md.template` - Step instruction file structure
- `agents.md.template` - AGENTS.md file structure
- `job.yml.example` - Complete job specification example
- `step_instruction.md.example` - Complete step instruction example

**Guidelines for generating instructions:**

1. **Use the job description** - The detailed description from job.yml provides crucial context
2. **Be specific** - Don't write generic instructions; tailor them to the step's purpose
3. **Provide output format examples** - Include a markdown code block in an "Output Format" section showing the expected file structure. A template with `[bracket placeholders]` is acceptable. For complex outputs, also include a concrete filled-in example showing realistic data — this is especially valuable for the first step in a workflow where there's no prior output to reference.
4. **Explain the "why"** - Help the user understand the step's role in the workflow
5. **Quality over quantity** - Detailed, actionable instructions are better than vague ones
6. **Align with reviews** - If the step has `reviews` defined, ensure the quality criteria in the instruction file match the review criteria
7. **Ask structured questions (when applicable)** - When a step has user-provided inputs (name/description inputs in job.yml), the instructions MUST explicitly tell the agent to "ask structured questions" using the AskUserQuestion tool. Steps that only have file inputs from prior steps do NOT need this phrase — they process data without user interaction.
8. **Handle edge cases** - If inputs might be missing, ambiguous, or incomplete, tell the agent to ask structured questions to clarify how to proceed rather than guessing

### Handling Reviews

If a step in the job.yml has `reviews` defined, the generated instruction file should:

1. **Mirror the quality criteria** - The "Quality Criteria" section should match what the reviews will validate
2. **Be explicit about success** - Help the agent understand when the step is truly complete
3. **Explain what's reviewed** - If reviews target specific outputs (via `run_each`), mention which outputs will be reviewed

**Example: If the job.yml has:**
```yaml
- id: research_competitors
  name: "Research Competitors"
  reviews:
    - run_each: research_notes.md
      quality_criteria:
        "Sufficient Data": "Does each competitor have at least 3 data points?"
        "Sources Cited": "Are sources cited for key claims?"
        "Current Information": "Is the information current (within last year)?"
```

**The instruction file should include:**
```markdown
## Quality Criteria

- Each competitor has at least 3 distinct data points
- All information is sourced with citations
- Data is current (from within the last year)
```

This alignment ensures the AI agent knows exactly what will be validated and can self-check before completing.

### Using Supplementary Reference Files

Step instructions can include additional `.md` files in the `steps/` directory for detailed examples, templates, or reference material. Reference them using the full path from the project root.

See `<job_dir>/steps/supplemental_file_references.md` for detailed documentation and examples.

### Step 3: Verify Files

Verify that all files are in their correct locations:
- `job.yml` at `.deepwork/jobs/[job_name]/job.yml` (created by define step)
- Step instruction files at `.deepwork/jobs/[job_name]/steps/[step_id].md`

## Example Implementation

For a complete worked example showing a job.yml and corresponding step instruction file, see:
- **Job specification**: `<job_dir>/templates/job.yml.example`
- **Step instruction**: `<job_dir>/templates/step_instruction.md.example`

## Important Guidelines

1. **Read the spec carefully** - Understand the job's intent from the description
2. **Generate complete instructions** - Don't create placeholder or stub files
3. **Maintain consistency** - Use the same structure for all step instruction files
4. **Provide examples** - Show what good output looks like
5. **Use context** - The job description provides valuable context for each step
6. **Be specific** - Tailor instructions to the specific step, not generic advice

## Completion Checklist

Before marking this step complete, ensure:
- [ ] job.yml validated and in job directory
- [ ] All step instruction files created
- [ ] Each instruction file is complete and actionable

## Note: Workflow Availability

Once the job.yml and step instruction files are created, the workflow is immediately available through the DeepWork MCP server. The MCP server reads job definitions directly from `.deepwork/jobs/` - no separate sync or installation step is required.