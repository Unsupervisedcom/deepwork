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

**Tool Selection Principle:**
When no tool is currently available for a technique, **prefer open source and free tools** by default. Only suggest paid or proprietary tools if the user explicitly requests them or if no viable free alternative exists.

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
3. **Find alternatives if needed** - If the tool is missing or broken, research and test alternatives until you have a working solution. **Prefer open source and free tools** by default; only suggest paid/proprietary tools if explicitly requested or no viable free alternative exists.
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
- Open source/free tools were preferred when no existing capability was available
- Techniques are organized by PROCESS name, not by tool name
- Each technique folder contains a SKILL.md following the Claude Skills format
- Helper scripts and assets are stored alongside SKILL.md in the technique folder
- All techniques have been verified to work together
- `deepwork sync` was run to sync techniques to platform skill directories
- When all criteria are met, include `<promise>✓ Quality Criteria Met</promise>` in your response
