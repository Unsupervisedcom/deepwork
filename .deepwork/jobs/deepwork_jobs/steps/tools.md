# Verify and Document Tools

## Objective

Verify that all external tools and capabilities required by the job are available and working, find alternatives if needed, and create process-focused documentation for future reference.

## Task

Analyze the job specification to determine what tools are needed, then spawn parallel sub-agents to test, configure, and document each process.

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

**For each step, create a requirements list:**
- What the step needs to accomplish
- What external tools or capabilities might be required
- What the expected input/output formats are

### Step 2: Spawn Parallel Sub-Agents for Each Process

For each process you identified, spawn a sub-agent **in parallel** to handle testing and documentation. This allows all processes to be verified concurrently.

**Sub-agent prompt template (customize for each process):**

```
You are verifying and documenting a tool for the "[PROCESS_NAME]" process in a DeepWork job.

## Process Requirement

[Describe what this specific process needs to accomplish]

## Your Tasks

1. **Test if a tool exists** - Check if a tool is available that can accomplish this process
2. **Verify it works** - Run a simple test to confirm functionality
3. **Find alternatives if needed** - If the tool is missing or broken, research and test alternatives until you have a working solution
4. **Create installation documentation** - Write `install_[tool_name].md` with:
   - How it was installed on this machine
   - Alternative installation methods (macOS, Ubuntu, Windows, pip/npm)
   - Verification steps
   - Troubleshooting tips
5. **Create process documentation** - Write `[process_name].md` (e.g., `making_pdfs.md`, NOT `pandoc.md`) with:
   - Purpose of this process
   - Selected tool, type, and version
   - Reference to installation doc
   - Usage examples
   - Alternatives considered

## Output Location

Create documentation in: `.deepwork/jobs/[job_name]/tools/`

## Success Criteria

- The process has a working tool
- Created `[process_name].md` document
- Created `install_[tool_name].md` document
```

**Example:** If you identified 3 processes (making PDFs, accessing websites, creating charts), spawn 3 sub-agents in parallel:
- Sub-agent 1: "making_pdfs" process
- Sub-agent 2: "accessing_websites" process
- Sub-agent 3: "creating_charts" process

### Step 3: Review Sub-Agent Outputs

After all sub-agents complete:

1. **Verify all processes are covered** - Check that each identified need has documentation
2. **Spot-check the documentation** - Ensure the docs are complete and accurate
3. **Verify tools work together** - If processes depend on each other, confirm compatibility

## Example

For a job that creates research reports from web sources:

**Step 1 output (your analysis):**
```
Required processes:
1. Accessing websites - Need to browse and extract data from web pages
2. Creating charts - Need to generate visualizations from data
3. Making PDFs - Need to convert markdown reports to PDF format
```

**Step 2:** Spawn 3 parallel sub-agents, one for each process

**Step 3:** Verify all sub-agents created their docs:
- `tools/accessing_websites.md` + `tools/install_chrome_mcp.md`
- `tools/creating_charts.md` + `tools/install_matplotlib.md`
- `tools/making_pdfs.md` + `tools/install_pandoc.md`

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
- Parallel sub-agents were spawned for each process requiring tooling
- Every required tool has been tested and verified working
- Each required process has a working solution (original tool or alternative)
- Documentation is organized by PROCESS, not by tool name
- Installation instructions are in separate `install_[tool].md` files
- Each process document references its installation doc
- All tools have been verified to work together
- When all criteria are met, include `<promise>✓ Quality Criteria Met</promise>` in your response
