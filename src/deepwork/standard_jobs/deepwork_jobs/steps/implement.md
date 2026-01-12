# Implement Job Steps

## Objective

Generate the DeepWork job directory structure and instruction files for each step based on the `job.yml` specification created in the previous step.

## Task

Read the `job.yml` specification file and create all the necessary files to make the job functional, including directory structure and step instruction files. Then sync the commands to make them available.

### Step 1: Read and Validate the Specification

1. **Locate the job.yml file**
   - Read `.deepwork/jobs/[job_name]/job.yml` from the define step (Where `[job_name]` is the name of the new job that was created in the define step)
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

### Step 2: Create Directory Structure

Create the job directory in `.deepwork/jobs/[job_name]/`:

```bash
mkdir -p .deepwork/jobs/[job_name]/steps
```

Files to create:
- `.deepwork/jobs/[job_name]/job.yml`
- `.deepwork/jobs/[job_name]/steps/[step_id].md` - One for each step

### Step 3: Generate Step Instruction Files

For each step in the job.yml, create a comprehensive instruction file at `.deepwork/jobs/[job_name]/steps/[step_id].md`.

Each instruction file should follow this structure:

```markdown
# [Step Name]

## Objective

[Clear statement of what this step accomplishes, derived from the step's description]

## Task

[Detailed instructions for completing this step, based on:
- The step's purpose
- Expected inputs and outputs
- The job's overall context
]

### Process

[Break down the step into substeps. Use the information gathered during define about:
- What needs to be done
- What makes a good output
- Any quality criteria
]

1. [Substep 1]
2. [Substep 2]
3. [Substep 3]

[If this step has user inputs, explain how to gather them]
[If this step has file inputs, explain how to use them]

## Output Format

### [output_filename_1]

[Description of what should be in this output file]

**Structure**:
```[file format]
[Example or template of what the output should look like]
```

[Repeat for each output file]

## Quality Criteria

[List what makes this step's output high quality:
- Completeness checks
- Format requirements
- Content requirements
]

- [Quality criterion 1]
- [Quality criterion 2]
- [Quality criterion 3]

## Context

[Provide context from the job's overall description to help understand why this step matters and how it fits into the bigger picture]
```

**Guidelines for generating instructions:**

1. **Use the job description** - The detailed description from job.yml provides crucial context
2. **Be specific** - Don't write generic instructions; tailor them to the step's purpose
3. **Provide examples** - Show what good output looks like
4. **Explain the "why"** - Help the user understand the step's role in the workflow
5. **Quality over quantity** - Detailed, actionable instructions are better than vague ones
6. **Align with stop hooks** - If the step has `stop_hooks` defined, ensure the quality criteria in the instruction file match the validation criteria in the hooks

### Handling Stop Hooks

If a step in the job.yml has `stop_hooks` defined, the generated instruction file should:

1. **Mirror the quality criteria** - The "Quality Criteria" section should match what the stop hooks will validate
2. **Be explicit about success** - Help the agent understand when the step is truly complete
3. **Include the promise pattern** - Mention that `<promise>QUALITY_COMPLETE</promise>` should be included when criteria are met

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
- When all criteria are met, include `<promise>QUALITY_COMPLETE</promise>` in your response
```

This alignment ensures the AI agent knows exactly what will be validated and can self-check before completing.

### Step 4: Verify job.yml Location

Verify that `job.yml` is in the correct location at `.deepwork/jobs/[job_name]/job.yml`. The define step should have created it there. If for some reason it's not there, you may need to create or move it.

### Step 5: Sync Commands

Run `deepwork sync` to generate the slash-commands for this job:

```bash
deepwork sync
```

This will:
- Parse the job definition
- Generate slash-commands for each step
- Make the commands available in `.claude/commands/` (or appropriate platform directory)

### Step 6: Reload Commands

Instruct the user to reload commands in their current session:
- Run `/reload` command (if available)
- Or restart the Claude session

### Step 7: Consider Policies for the New Job

After implementing the job, consider whether there are **policies** that would help enforce quality or consistency when working with this job's domain.

**What are policies?**

Policies are automated guardrails defined in `.deepwork.policy.yml` that trigger when certain files change during an AI session. They help ensure:
- Documentation stays in sync with code
- Team guidelines are followed
- Architectural decisions are respected
- Quality standards are maintained

**When to suggest policies:**

Think about the job you just implemented and ask:
- Does this job produce outputs that other files depend on?
- Are there documentation files that should be updated when this job's outputs change?
- Are there quality checks or reviews that should happen when certain files in this domain change?
- Could changes to the job's output files impact other parts of the project?

**Examples of policies that might make sense:**

| Job Type | Potential Policy |
|----------|------------------|
| API Design | "Update API docs when endpoint definitions change" |
| Database Schema | "Review migrations when schema files change" |
| Competitive Research | "Update strategy docs when competitor analysis changes" |
| Feature Development | "Update changelog when feature files change" |
| Configuration Management | "Update install guide when config files change" |

**How to offer policy creation:**

If you identify one or more policies that would benefit the user, explain:
1. **What the policy would do** - What triggers it and what action it prompts
2. **Why it would help** - How it prevents common mistakes or keeps things in sync
3. **What files it would watch** - The trigger patterns

Then ask the user:

> "Would you like me to create this policy for you? I can run `/deepwork_policy.define` to set it up."

If the user agrees, invoke the `/deepwork_policy.define` command to guide them through creating the policy.

**Example dialogue:**

```
Based on the competitive_research job you just created, I noticed that when
competitor analysis files change, it would be helpful to remind you to update
your strategy documentation.

I'd suggest a policy like:
- **Name**: "Update strategy when competitor analysis changes"
- **Trigger**: `**/positioning_report.md`
- **Action**: Prompt to review and update `docs/strategy.md`

Would you like me to create this policy? I can run `/deepwork_policy.define` to set it up.
```

**Note:** Not every job needs policies. Only suggest them when they would genuinely help maintain consistency or quality. Don't force policies where they don't make sense.

## Example Implementation

**Given this job.yml:**
```yaml
name: competitive_research
version: "1.0.0"
summary: "Systematic competitive analysis workflow"
description: |
  A comprehensive workflow for analyzing competitors in your market segment.
  Helps product teams understand the competitive landscape through systematic
  identification, research, comparison, and positioning recommendations.

steps:
  - id: identify_competitors
    name: "Identify Competitors"
    description: "Identify 5-7 key competitors in the target market"
    instructions_file: steps/identify_competitors.md
    inputs:
      - name: market_segment
        description: "The market segment to analyze"
      - name: product_category
        description: "The product category"
    outputs:
      - competitors_list.md
    dependencies: []
```

**Generate this instruction file** (`.deepwork/jobs/competitive_research/steps/identify_competitors.md`):

```markdown
# Identify Competitors

## Objective

Identify 5-7 key competitors in the target market segment to analyze for competitive positioning.

## Task

Research and identify the most relevant competitors in the specified market segment and product category. Focus on companies that directly compete for the same customer base and solve similar problems.

### Process

1. **Understand the market context**
   - Review the market segment provided by the user
   - Understand the product category boundaries
   - Consider direct and indirect competitors

2. **Research competitors**
   - Search for companies in this space
   - Look for market leaders and emerging players
   - Consider different competitive dimensions (features, price, target market)

3. **Select 5-7 key competitors**
   - Prioritize direct competitors
   - Include at least one market leader
   - Include 1-2 emerging/innovative players
   - Ensure diversity in the competitive set

4. **Document each competitor**
   - Company name
   - Brief description (2-3 sentences)
   - Why they're a relevant competitor
   - Primary competitive dimension

## Output Format

### competitors_list.md

A markdown document listing each competitor with context.

**Structure**:
```markdown
# Competitor Analysis: [Market Segment]

## Market Context
- **Segment**: [market segment]
- **Category**: [product category]
- **Analysis Date**: [current date]

## Identified Competitors

### 1. [Competitor Name]
**Description**: [2-3 sentence description of what they do]

**Why Relevant**: [Why they're a key competitor in this space]

**Competitive Dimension**: [What they compete on - e.g., price, features, market segment]

[Repeat for each competitor, 5-7 total]

## Selection Rationale

[Brief paragraph explaining why these specific competitors were chosen and what dimensions of competition they represent]
```

## Quality Criteria

- 5-7 competitors identified (not too few, not too many)
- Mix of established and emerging players
- All competitors are genuinely relevant to the market segment
- Each competitor has clear, specific description
- Selection rationale explains the competitive landscape
- Output is well-formatted and ready for use by next step

## Context

This is the foundation step for competitive analysis. The competitors identified here will be deeply researched in subsequent steps, so it's important to choose the right set. Focus on competitors that will provide strategic insights for positioning decisions.
```

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

## Output Format

### implementation_summary.md

After successful implementation, create a summary:

```markdown
# Job Implementation Complete: [job_name]

## Overview

Successfully implemented the **[job_name]** workflow with [N] steps.

**Summary**: [job summary]

**Version**: [version]

## Files Created

### Job Definition
- `.deepwork/jobs/[job_name]/job.yml`

### Step Instructions
- `.deepwork/jobs/[job_name]/steps/[step1_id].md`
- `.deepwork/jobs/[job_name]/steps/[step2_id].md`
[... list all step files ...]


## Generated Commands

After running `deepwork sync`, the following slash-commands are now available:

- `/[job_name].[step1_id]` - [step description]
- `/[job_name].[step2_id]` - [step description]
[... list all commands ...]

## Next Steps

1. **Reload commands**: Run `/reload` or restart your Claude session
2. **Start the workflow**: Run `/[job_name].[first_step_id]` to begin
3. **Test the job**: Try executing the first step to ensure everything works

## Job Structure

[Show the workflow diagram with step names and dependencies]

Step 1: [step_name]
  ↓
Step 2: [step_name]
  ↓
Step 3: [step_name]
  ↓
[Final output]

The job is now ready for use!
```

## Completion Checklist

Before marking this step complete, ensure:
- [ ] job.yml validated and copied to job directory
- [ ] All step instruction files created
- [ ] Each instruction file is complete and actionable
- [ ] `deepwork sync` executed successfully
- [ ] Commands generated in platform directory
- [ ] User informed of next steps (reload commands)
- [ ] implementation_summary.md created
- [ ] Considered whether policies would benefit this job (Step 7)
- [ ] If policies suggested, offered to run `/deepwork_policy.define`

## Quality Criteria

- Job directory structure is correct
- All instruction files are complete (not stubs)
- Instructions are specific and actionable
- Output examples are provided in each instruction file
- Quality criteria defined for each step
- Sync completed successfully
- Commands available for use
- Thoughtfully considered relevant policies for the job domain
