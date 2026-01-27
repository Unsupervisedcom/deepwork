---
name: deepwork_jobs.tools
description: "Verifies required techniques are available and documents how to use them. Use after job spec review to ensure implementation can succeed."user-invocable: false---

# deepwork_jobs.tools

**Step 3/4** in **new_job** workflow

> Create a new DeepWork job from scratch through definition, review, tools verification, and implementation

> Creates and manages multi-step AI workflows. Use when defining, implementing, or improving DeepWork jobs.

## Prerequisites (Verify First)

Before proceeding, confirm these steps are complete:
- `/deepwork_jobs.review_job_spec`

## Instructions

**Goal**: Verifies required techniques are available and documents how to use them. Use after job spec review to ensure implementation can succeed.

# Verify and Document Techniques

## Objective

Verify that all external tools and capabilities required by the job are available and working, find alternatives if needed, and create reusable **techniques** for future reference.

## Task

Analyze the job specification to determine what techniques are needed, then spawn parallel sub-agents to test, configure, and document each technique.

### Step 1: Analyze the Job for Required Techniques

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

**For each step, create a requirements list:**
- What the step needs to accomplish
- What external tools or capabilities might be required
- What the expected input/output formats are

### Step 2: Spawn Parallel Sub-Agents for Each Technique

For each technique you identified, spawn a sub-agent **in parallel** to handle testing and documentation. This allows all techniques to be verified concurrently.

**Sub-agent prompt template (customize for each technique):**

```
You are verifying and documenting a technique for the "[TECHNIQUE_NAME]" process in a DeepWork job.

## Technique Requirement

[Describe what this specific technique needs to accomplish]

## Your Tasks

1. **Test if a tool exists** - Check if a tool is available that can accomplish this technique
2. **Verify it works** - Run a simple test to confirm functionality
3. **Find alternatives if needed** - If the tool is missing or broken, research and test alternatives until you have a working solution
4. **Create the technique** - Create a folder in `.deepwork/techniques/[technique_name]/` with:
   - `SKILL.md` - The main technique skill file following the Claude Skills format:
     ```markdown
     ---
     name: technique_name
     description: "Brief description of what this technique accomplishes"
     ---

     # Technique Name

     ## Purpose
     What this technique accomplishes and when to use it.

     ## Tool
     - **Name**: Tool name (e.g., pandoc, playwright)
     - **Type**: CLI tool / MCP server / Browser extension / API
     - **Version**: Known working version

     ## Installation

     ### macOS
     ```bash
     brew install tool-name
     ```

     ### Ubuntu/Debian
     ```bash
     apt-get install tool-name
     ```

     ### pip/npm (if applicable)
     ```bash
     pip install tool-name
     ```

     ## Verification
     ```bash
     tool-name --version
     ```

     ## Usage

     ### Basic Example
     ```bash
     tool-name input.md -o output.pdf
     ```

     ### Common Options
     - `-o, --output`: Output file path
     - Other relevant options...

     ## Troubleshooting
     Common issues and solutions.

     ## Alternatives Considered
     - Alternative 1: Why not chosen
     - Alternative 2: Why not chosen
     ```
   - Any helper scripts or assets the technique needs (e.g., `convert.py`, `template.html`)

## Output Location

Create the technique in: `.deepwork/techniques/[technique_name]/`

Use descriptive, process-focused names like `making_pdfs`, `accessing_websites`, `creating_charts` (NOT tool names like `pandoc`, `playwright`).

## Success Criteria

- The technique has a working tool
- Created `.deepwork/techniques/[technique_name]/SKILL.md`
- Included any necessary helper scripts or assets in the same folder
```

**Example:** If you identified 3 techniques (making PDFs, accessing websites, creating charts), spawn 3 sub-agents in parallel:
- Sub-agent 1: "making_pdfs" technique
- Sub-agent 2: "accessing_websites" technique
- Sub-agent 3: "creating_charts" technique

### Step 3: Review Sub-Agent Outputs

After all sub-agents complete:

1. **Verify all techniques are covered** - Check that each identified need has a technique folder
2. **Spot-check the documentation** - Ensure the SKILL.md files are complete and accurate
3. **Verify tools work together** - If techniques depend on each other, confirm compatibility

### Step 4: Run Sync

After all techniques are created, run `deepwork sync` to copy them to the platform skill directories (`.claude/skills/`, `.gemini/skills/`) with the `dwt_` prefix.

## Example

For a job that creates research reports from web sources:

**Step 1 output (your analysis):**
```
Required techniques:
1. Accessing websites - Need to browse and extract data from web pages
2. Creating charts - Need to generate visualizations from data
3. Making PDFs - Need to convert markdown reports to PDF format
```

**Step 2:** Spawn 3 parallel sub-agents, one for each technique

**Step 3:** Verify all sub-agents created their techniques:
```
.deepwork/techniques/
├── accessing_websites/
│   └── SKILL.md
├── creating_charts/
│   ├── SKILL.md
│   └── chart_helper.py
└── making_pdfs/
    └── SKILL.md
```

**Step 4:** Run `deepwork sync` to sync techniques to platforms

## Output

After completing this step, you should have:

1. **techniques/ directory** with technique folders:
   ```
   .deepwork/techniques/
   ├── [technique_1]/
   │   ├── SKILL.md
   │   └── [optional assets]
   ├── [technique_2]/
   │   ├── SKILL.md
   │   └── [optional assets]
   └── ...
   ```

2. **Synced skills** in platform directories (after running `deepwork sync`):
   ```
   .claude/skills/
   ├── dwt_[technique_1]/
   │   └── SKILL.md
   └── dwt_[technique_2]/
       └── SKILL.md
   ```

3. **Confidence that all techniques work** and the job can be implemented successfully

## Quality Criteria

- All job steps have been analyzed for technique requirements
- Parallel sub-agents were spawned for each technique requiring tooling
- Every required tool has been tested and verified working
- Each required technique has a working solution (original tool or alternative)
- Techniques are organized by PROCESS name, not by tool name
- Each technique folder contains a SKILL.md following the Claude Skills format
- Helper scripts and assets are stored alongside SKILL.md in the technique folder
- All techniques have been verified to work together
- `deepwork sync` was run to sync techniques to platform skill directories
- When all criteria are met, include `<promise>✓ Quality Criteria Met</promise>` in your response


### Job Context

Core commands for managing DeepWork jobs. These commands help you define new multi-step
workflows and learn from running them.

The `new_job` workflow guides you through defining and implementing a new job by
asking structured questions about your workflow, understanding each step's inputs and outputs,
reviewing the specification, verifying required techniques, and generating all necessary files.

The `learn` skill reflects on conversations where DeepWork jobs were run, identifies
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
- `.deepwork/techniques/` (directory)

## Guardrails

- Do NOT skip prerequisite verification if this step has dependencies
- Do NOT produce partial outputs; complete all required outputs before finishing
- Do NOT proceed without required inputs; ask the user if any are missing
- Do NOT modify files outside the scope of this step's defined outputs

## Quality Validation

**Before completing this step, you MUST have your work reviewed against the quality criteria below.**

Use a sub-agent (Haiku model) to review your work against these criteria:

**Criteria (all must be satisfied)**:
1. **Tasks Analyzed**: Were all job steps reviewed to identify required techniques (CLI tools, MCP servers, browser extensions, etc.)?
2. **Parallel Sub-Agents**: Were parallel sub-agents spawned for each technique requiring tooling?
3. **Had Working Technique**: Does each required technique have a working solution (original tool or alternative)?
4. **Technique Created**: Was a technique folder created in `.deepwork/techniques/` for each technique (e.g., making_pdfs/, not pandoc/)?
5. **SKILL.md Format**: Does each technique folder contain a SKILL.md file following the Claude Skills format?
6. **Assets Included**: Are helper scripts and assets stored alongside SKILL.md in the technique folder?
7. **Sync Complete**: Was `deepwork sync` run to sync techniques to platform skill directories?
**Review Process**:
1. Once you believe your work is complete, spawn a sub-agent using Haiku to review your work against the quality criteria above
2. The sub-agent should examine your outputs and verify each criterion is met
3. If the sub-agent identifies valid issues, fix them
4. Have the sub-agent review again until all valid feedback has been addressed
5. Only mark the step complete when the sub-agent confirms all criteria are satisfied

## On Completion

1. Verify outputs are created
2. Inform user: "new_job step 3/4 complete, outputs: .deepwork/techniques/"
3. **Continue workflow**: Use Skill tool to invoke `/deepwork_jobs.implement`

---

**Reference files**: `.deepwork/jobs/deepwork_jobs/job.yml`, `.deepwork/jobs/deepwork_jobs/steps/tools.md`