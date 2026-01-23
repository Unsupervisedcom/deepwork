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
