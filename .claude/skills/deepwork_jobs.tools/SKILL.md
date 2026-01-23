---
name: deepwork_jobs.tools
description: "Verifies required external tools are available and documents how to use them. Use after job spec review to ensure implementation can succeed."
user-invocable: false
hooks:
  Stop:
    - hooks:
        - type: prompt
          prompt: |
            You must evaluate whether Claude has met all the below quality criteria for the request.

            ## Quality Criteria

            1. **Tasks Analyzed**: Were all job steps reviewed to identify required external tools?
            2. **Tools Tested**: Was each identified tool tested to verify it works?
            3. **Alternatives Found**: If a tool was missing or broken, were alternatives discovered and tested?
            4. **Process Documentation**: Was a markdown document created for each process (e.g., making_pdfs.md, not pandoc.md)?
            5. **Installation Documented**: Does each process document explain how the tool was/can be installed?
            6. **Invocation Documented**: Does each process document show how to invoke the tool with examples?

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

            1. **Tasks Analyzed**: Were all job steps reviewed to identify required external tools?
            2. **Tools Tested**: Was each identified tool tested to verify it works?
            3. **Alternatives Found**: If a tool was missing or broken, were alternatives discovered and tested?
            4. **Process Documentation**: Was a markdown document created for each process (e.g., making_pdfs.md, not pandoc.md)?
            5. **Installation Documented**: Does each process document explain how the tool was/can be installed?
            6. **Invocation Documented**: Does each process document show how to invoke the tool with examples?

            ## Instructions

            Review the conversation and determine if ALL quality criteria above have been satisfied.
            Look for evidence that each criterion has been addressed.

            If the agent has included `<promise>✓ Quality Criteria Met</promise>` in their response OR
            all criteria appear to be met, respond with: {"ok": true}

            If criteria are NOT met AND the promise tag is missing, respond with:
            {"ok": false, "reason": "**AGENT: TAKE ACTION** - [which criteria failed and why]"}
---

# deepwork_jobs.tools

**Step 3/5** in **deepwork_jobs** workflow

> Creates and manages multi-step AI workflows. Use when defining, implementing, or improving DeepWork jobs.

## Prerequisites (Verify First)

Before proceeding, confirm these steps are complete:
- `/deepwork_jobs.review_job_spec`

## Instructions

**Goal**: Verifies required external tools are available and documents how to use them. Use after job spec review to ensure implementation can succeed.

# Verify and Document Tools

## Objective

Verify that all external tools required by the job are available and working, find alternatives if needed, and create process-focused documentation for future reference.

## Task

Review the job specification to identify what external tools are needed, test them, and document how each process works.

### Step 1: Analyze the Job for Required Tools

Read the `job.yml` file and examine each step to identify tasks that require external tools.

**Look for steps that involve:**
- File format conversion (PDF, DOCX, HTML, etc.)
- Data processing (CSV, JSON, XML transformations)
- Media manipulation (images, audio, video)
- External API calls or web requests
- Build processes (compilers, bundlers)
- Testing frameworks
- Documentation generation
- Database operations
- Container or virtualization tools

**For each step, note:**
- What the step needs to accomplish
- What external tools might be required
- What the expected input/output formats are

### Step 2: Test Each Required Tool

For each tool you've identified:

1. **Check if the tool is installed:**
   ```bash
   which [tool_name] || echo "Not found"
   ```

2. **Verify the version:**
   ```bash
   [tool_name] --version
   ```

3. **Test basic functionality:**
   - Run a simple test command to confirm it works
   - Create a minimal test case if needed
   - Verify the output is as expected

**Document what you find:**
- Tool name and version
- Whether it works or not
- Any errors encountered

### Step 3: Find Alternatives for Missing/Broken Tools

If a tool is missing or doesn't work:

1. **Research alternatives:**
   - Search for equivalent tools that accomplish the same task
   - Consider multiple options (CLI tools, libraries, online services)

2. **Test the alternatives:**
   - Install and try each alternative
   - Verify it can accomplish the required task
   - Compare quality, speed, and ease of use

3. **Select the best option:**
   - Choose the tool that works best for this job's needs
   - Consider factors like: availability, ease of installation, reliability

### Step 4: Create Process Documentation

**IMPORTANT:** Create documentation organized by **process** (what you're trying to accomplish), NOT by tool name.

**Correct naming:**
- `making_pdfs.md` - How to create PDF documents
- `resizing_images.md` - How to resize/optimize images
- `converting_data_formats.md` - How to transform data between formats

**Incorrect naming:**
- `pandoc.md` - This is tool-centric, not process-centric
- `imagemagick.md` - Same issue

Create documentation files in `.deepwork/jobs/[job_name]/tools/`:

```bash
mkdir -p .deepwork/jobs/[job_name]/tools
```

**Each process document should include:**

```markdown
# [Process Name]

## Purpose
What this process accomplishes and when you would use it.

## Selected Tool
- **Tool**: [tool name]
- **Version**: [version tested]
- **Why chosen**: [brief rationale]

## Installation

### How it was installed on this machine
[Document the actual installation method used]

### Alternative installation methods
- **macOS**: `brew install [package]`
- **Ubuntu/Debian**: `apt install [package]`
- **Windows**: [instructions]
- **Using pip/npm/etc.**: [instructions]

## Usage

### Basic invocation
```bash
[basic command example]
```

### Common options
| Option | Description |
|--------|-------------|
| `-o` | Output file |
| ... | ... |

### Examples

**Example 1: [Basic use case]**
```bash
[command]
```

**Example 2: [More complex use case]**
```bash
[command]
```

## Troubleshooting

### Common issues
- **[Issue]**: [Solution]

## Alternatives Considered
- **[Alternative tool]**: [Why not chosen / when it might be preferred]
```

### Step 5: Verify All Tools Work Together

After documenting all tools:

1. **Run a dry-run test:**
   - Simulate the workflow with test inputs
   - Verify each tool can read the previous tool's output

2. **Check for compatibility:**
   - Ensure tools work with the same file formats
   - Verify version compatibility if tools interact

3. **Document any integration notes:**
   - Add notes about tool ordering or dependencies
   - Document any format conversion requirements between steps

## Example Workflow

For a job that creates research reports with charts:

1. **Analyze job**: Steps need to gather data, create visualizations, and generate PDF reports
2. **Identify tools needed**: Data fetching (curl/wget), chart generation (gnuplot/matplotlib), PDF creation (pandoc/weasyprint)
3. **Test tools**: Found pandoc v3.1 and gnuplot v5.4 installed, matplotlib not installed
4. **Find alternatives**: Installed matplotlib via pip, tested successfully
5. **Document processes**:
   - `tools/fetching_web_data.md` - Using curl for API requests
   - `tools/creating_charts.md` - Using matplotlib for visualizations
   - `tools/making_pdfs.md` - Using pandoc with custom templates

## Output

After completing this step, you should have:

1. **tools/ directory** with process documentation:
   ```
   .deepwork/jobs/[job_name]/tools/
   ├── [process_1].md
   ├── [process_2].md
   └── ...
   ```

2. **Confidence that all tools work** and the job can be implemented successfully

## Quality Criteria

- All job steps have been analyzed for tool requirements
- Every required tool has been tested and verified working
- Missing or broken tools have been replaced with working alternatives
- Documentation is organized by PROCESS, not by tool name
- Each process document includes installation and invocation instructions
- All tools have been verified to work together
- When all criteria are met, include `<promise>✓ Quality Criteria Met</promise>` in your response


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
- `tools/` (directory)

## Guardrails

- Do NOT skip prerequisite verification if this step has dependencies
- Do NOT produce partial outputs; complete all required outputs before finishing
- Do NOT proceed without required inputs; ask the user if any are missing
- Do NOT modify files outside the scope of this step's defined outputs

## Quality Validation

Stop hooks will automatically validate your work. The loop continues until all criteria pass.

**Criteria (all must be satisfied)**:
1. **Tasks Analyzed**: Were all job steps reviewed to identify required external tools?
2. **Tools Tested**: Was each identified tool tested to verify it works?
3. **Alternatives Found**: If a tool was missing or broken, were alternatives discovered and tested?
4. **Process Documentation**: Was a markdown document created for each process (e.g., making_pdfs.md, not pandoc.md)?
5. **Installation Documented**: Does each process document explain how the tool was/can be installed?
6. **Invocation Documented**: Does each process document show how to invoke the tool with examples?


**To complete**: Include `<promise>✓ Quality Criteria Met</promise>` in your final response only after verifying ALL criteria are satisfied.

## On Completion

1. Verify outputs are created
2. Inform user: "Step 3/5 complete, outputs: tools/"
3. **Continue workflow**: Use Skill tool to invoke `/deepwork_jobs.implement`

---

**Reference files**: `.deepwork/jobs/deepwork_jobs/job.yml`, `.deepwork/jobs/deepwork_jobs/steps/tools.md`