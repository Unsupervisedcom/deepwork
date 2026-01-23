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

            1. **Tasks Analyzed**: Were all job steps reviewed to identify required tools and capabilities (CLI tools, MCP servers, browser extensions, etc.)?
            2. **Tools Tested**: Was each identified tool or capability tested to verify it works?
            3. **Had Working Process**: Does each required process have a working solution (original tool or alternative)?
            4. **Process Documentation**: Was a markdown document created for each process (e.g., making_pdfs.md, not pandoc.md)?
            5. **Installation Documented**: Is there a separate install_[tool].md file for each tool that requires installation?
            6. **Invocation Documented**: Does each process document show how to use the tool with examples?

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

            1. **Tasks Analyzed**: Were all job steps reviewed to identify required tools and capabilities (CLI tools, MCP servers, browser extensions, etc.)?
            2. **Tools Tested**: Was each identified tool or capability tested to verify it works?
            3. **Had Working Process**: Does each required process have a working solution (original tool or alternative)?
            4. **Process Documentation**: Was a markdown document created for each process (e.g., making_pdfs.md, not pandoc.md)?
            5. **Installation Documented**: Is there a separate install_[tool].md file for each tool that requires installation?
            6. **Invocation Documented**: Does each process document show how to use the tool with examples?

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

Verify that all external tools and capabilities required by the job are available and working, find alternatives if needed, and create process-focused documentation for future reference.

## Task

Review the job specification to identify what external tools or capabilities are needed, test them, and document how each process works.

### Step 1: Analyze the Job for Required Tools and Capabilities

Read the `job.yml` file and examine each step to identify tasks that require external tools or capabilities beyond the agent's built-in abilities.

**Look for steps that involve:**
- File format conversion (PDF, DOCX, HTML, etc.)
- Data processing (CSV, JSON, XML transformations)
- Media manipulation (images, audio, video)
- Web browsing or site access (via browser extensions like Chrome MCP)
- External API calls or web requests
- Build processes (compilers, bundlers)
- Testing frameworks
- Database operations
- Container or virtualization tools

**Types of tools and capabilities to consider:**
- **CLI tools**: Command-line programs (pandoc, ffmpeg, imagemagick, etc.)
- **MCP servers**: Model Context Protocol servers that extend agent capabilities (browser control, database access, etc.)
- **Browser extensions**: Chrome extensions or similar for web interaction
- **Language runtimes**: Python, Node.js, Ruby, etc. with specific packages
- **External services**: APIs that require authentication or setup

**For each step, note:**
- What the step needs to accomplish
- What external tools or capabilities might be required
- What the expected input/output formats are

### Step 2: Test Each Required Tool or Capability

For each tool or capability you've identified, verify it's available and working:

1. **Check availability** - Confirm the tool is installed or the capability is accessible
2. **Verify functionality** - Run a simple test to confirm it works as expected
3. **Note the version** - Record what version is installed for reproducibility

**Document what you find:**
- Tool/capability name and version
- Whether it works or not
- Any errors encountered

### Step 3: Ensure Working Processes

If a tool is missing or doesn't work:

1. **Research alternatives:**
   - Search for equivalent tools that accomplish the same task
   - Consider multiple options (CLI tools, MCP servers, browser extensions, libraries, online services)

2. **Test the alternatives:**
   - Install and try each alternative
   - Verify it can accomplish the required task
   - Compare quality, speed, and ease of use

3. **Select the best option:**
   - Choose the tool that works best for this job's needs
   - Consider factors like: availability, ease of installation, reliability

The goal is to have a **working process** for each required capability, not necessarily the originally planned tool.

### Step 4: Create Installation Documentation

For each tool that requires installation, create a separate installation document at `.deepwork/jobs/[job_name]/tools/install_[tool_name].md`.

**Installation document template:**

```markdown
# Installing [Tool Name]

## Overview
Brief description of what this tool does.

## How it was installed on this machine
[Document the actual installation method used]

## Alternative installation methods

### macOS
[instructions]

### Ubuntu/Debian
[instructions]

### Windows
[instructions]

### Via package manager (pip/npm/etc.)
[instructions]

## Verification
How to verify the installation worked.

## Troubleshooting
Common installation issues and solutions.
```

### Step 5: Create Process Documentation

**IMPORTANT:** Create documentation organized by **process** (what you're trying to accomplish), NOT by tool name.

**Correct naming:**
- `making_pdfs.md` - How to create PDF documents
- `resizing_images.md` - How to resize/optimize images
- `accessing_websites.md` - How to browse and extract data from websites
- `converting_data_formats.md` - How to transform data between formats

**Incorrect naming:**
- `pandoc.md` - This is tool-centric, not process-centric
- `imagemagick.md` - Same issue

Create documentation files in `.deepwork/jobs/[job_name]/tools/`:

**Each process document should include:**

```markdown
# [Process Name]

## Purpose
What this process accomplishes and when you would use it.

## Selected Tool
- **Tool**: [tool name]
- **Type**: [CLI tool / MCP server / Browser extension / etc.]
- **Version**: [version tested]
- **Why chosen**: [brief rationale]

## Installation
See [install_[tool_name].md](./install_[tool_name].md) for installation instructions.

## Usage

### Basic invocation
[Show basic usage example]

### Common options
| Option | Description |
|--------|-------------|
| ... | ... |

### Examples

**Example 1: [Basic use case]**
[example]

**Example 2: [More complex use case]**
[example]

## Alternatives Considered
- **[Alternative tool]**: [Why not chosen / when it might be preferred]
```

### Step 6: Verify All Tools Work Together

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

For a job that creates research reports from web sources:

1. **Analyze job**: Steps need to browse websites, gather data, create visualizations, and generate PDF reports
2. **Identify tools needed**: Web browsing (Chrome MCP or browser extension), chart generation (matplotlib), PDF creation (pandoc)
3. **Test tools**: Found Chrome MCP working, pandoc installed, matplotlib not installed
4. **Ensure working processes**: Installed matplotlib via pip, tested successfully
5. **Document installation**:
   - `tools/install_matplotlib.md` - Python package installation
   - `tools/install_pandoc.md` - System package installation
6. **Document processes**:
   - `tools/accessing_websites.md` - Using Chrome MCP for web browsing
   - `tools/creating_charts.md` - Using matplotlib for visualizations
   - `tools/making_pdfs.md` - Using pandoc with custom templates

## Output

After completing this step, you should have:

1. **tools/ directory** with process and installation documentation:
   ```
   .deepwork/jobs/[job_name]/tools/
   ├── [process_1].md
   ├── [process_2].md
   ├── install_[tool_1].md
   ├── install_[tool_2].md
   └── ...
   ```

2. **Confidence that all processes work** and the job can be implemented successfully

## Quality Criteria

- All job steps have been analyzed for tool/capability requirements
- Every required tool has been tested and verified working
- Each required process has a working solution (original tool or alternative)
- Documentation is organized by PROCESS, not by tool name
- Installation instructions are in separate `install_[tool].md` files
- Each process document references its installation doc
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
1. **Tasks Analyzed**: Were all job steps reviewed to identify required tools and capabilities (CLI tools, MCP servers, browser extensions, etc.)?
2. **Tools Tested**: Was each identified tool or capability tested to verify it works?
3. **Had Working Process**: Does each required process have a working solution (original tool or alternative)?
4. **Process Documentation**: Was a markdown document created for each process (e.g., making_pdfs.md, not pandoc.md)?
5. **Installation Documented**: Is there a separate install_[tool].md file for each tool that requires installation?
6. **Invocation Documented**: Does each process document show how to use the tool with examples?


**To complete**: Include `<promise>✓ Quality Criteria Met</promise>` in your final response only after verifying ALL criteria are satisfied.

## On Completion

1. Verify outputs are created
2. Inform user: "Step 3/5 complete, outputs: tools/"
3. **Continue workflow**: Use Skill tool to invoke `/deepwork_jobs.implement`

---

**Reference files**: `.deepwork/jobs/deepwork_jobs/job.yml`, `.deepwork/jobs/deepwork_jobs/steps/tools.md`