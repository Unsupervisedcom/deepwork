# DeepWork Techniques

This folder contains reusable **techniques** - documented processes for accomplishing specific tasks using external tools. Techniques follow the Claude Skills format and are automatically synced to AI agent configuration directories (`.claude/skills/`, `.gemini/skills/`) with a `dwt_` prefix.

## Purpose

Techniques capture knowledge about how to accomplish processes that require external tools, MCP servers, or specific workflows. They are:

- **Reusable**: Once created, a technique can be used across multiple jobs
- **Documented**: Each technique includes installation and usage instructions
- **Portable**: Techniques are synced to all configured AI platforms

## Format

Each technique is a folder containing skill files that follow the Claude Skills format:

```
techniques/
├── AGENTS.md                    # This file
├── making_pdfs/
│   └── SKILL.md                 # Main technique skill
├── accessing_websites/
│   └── SKILL.md
└── [technique_name]/
    └── SKILL.md
```

### SKILL.md Format (Claude Skills)

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

How to install the required tool:

### macOS
\`\`\`bash
brew install tool-name
\`\`\`

### Ubuntu/Debian
\`\`\`bash
apt-get install tool-name
\`\`\`

### pip/npm
\`\`\`bash
pip install tool-name
# or
npm install -g tool-name
\`\`\`

## Verification

How to verify the tool is installed correctly:

\`\`\`bash
tool-name --version
\`\`\`

## Usage

### Basic Example

\`\`\`bash
tool-name input.md -o output.pdf
\`\`\`

### Common Options

- `-o, --output`: Output file path
- `-f, --format`: Output format

### Example Workflow

1. Prepare input files
2. Run the tool
3. Verify output

## Troubleshooting

Common issues and solutions:

### Issue 1: Tool not found
- Ensure tool is in PATH
- Try reinstalling

## Assets

If this technique requires helper scripts or templates, they should be stored
alongside the SKILL.md file:

```
technique_name/
├── SKILL.md
├── convert.py          # Helper script
└── template.html       # Template file
```

Reference these assets using relative paths in the SKILL.md.

## Alternatives Considered

Other tools that could accomplish this process:
- Alternative 1: Brief note on why not chosen
- Alternative 2: Brief note on why not chosen
```

## Syncing

Techniques are automatically synced by `deepwork sync`:

1. Techniques from `.deepwork/techniques/` are copied to platform skill directories
2. Folder names are prefixed with `dwt_` (e.g., `making_pdfs` becomes `dwt_making_pdfs`)
3. Stale `dwt_` prefixed folders (no longer in techniques) are removed
4. This ensures platform skills stay in sync with the techniques folder

## Creating Techniques

Techniques are created by the `deepwork_jobs` workflow:

- **`/deepwork_jobs.tools`** step creates techniques when verifying tools for a job
- **`/deepwork_jobs.learn`** step can refine existing techniques based on execution learnings

You can also create techniques manually by adding a new folder with a `SKILL.md` file.

## Invocation

Once synced, techniques can be invoked as skills:

- **Claude Code**: `/dwt_making_pdfs`
- **Gemini CLI**: `/dwt_making_pdfs`

The `dwt_` prefix indicates these are DeepWork-managed techniques.
