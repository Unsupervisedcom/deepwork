# DeepWork

> **Note**: DeepWork is in active development. We welcome feedback and contributions!

> Framework for enabling AI agents to perform complex, multi-step work tasks

DeepWork is a tool for defining and executing multi-step workflows with AI coding assistants like Claude Code, Google Gemini, and GitHub Copilot. It enables you to decompose complex tasks into manageable steps, with clear inputs, outputs, and dependencies.

## Supported Platforms

| Platform | Status | Command Format | Hooks Support |
|----------|--------|----------------|---------------|
| **Claude Code** | Full Support | Markdown | Yes (stop_hooks, pre/post) |
| **Gemini CLI** | Full Support | TOML | No (global only) |
| OpenCode | Planned | Markdown | No |
| GitHub Copilot CLI | Planned | Markdown | No (tool permissions only) |

> **Tip:** New to DeepWork? Claude Code has the most complete feature support, including quality validation hooks and automated rules. For browser automation, Claude in Chrome (Anthropic's browser extension) works well with DeepWork workflows.

## Easy Installation
In your Agent CLI (ex. `claude`), ask:

```
Please fully install https://pypi.org/project/deepwork/ and make sure you see the new commands.
```

## Installation Details


**Agents**: - be sure to perform all the steps, not just the package install.

### Prerequisites

- Python 3.11 or higher
- Git repository
- One of: Claude Code or Gemini CLI

### Install DeepWork

```bash
# Using Homebrew (macOS/Linux)
brew tap unsupervisedcom/deepwork
brew install deepwork

# Using pipx (isolated environment)
pipx install deepwork

# Or using uv
uv tool install deepwork

# Or using pip
pip install deepwork
```

### Install in Your Project
```bash
cd your-project/
deepwork install --platform claude

# Or Gemini CLI, etc.
deepwork install --platform gemini
```

This will:
- Create `.deepwork/` directory structure
- Generate core DeepWork jobs
- Install DeepWork jobs for your AI assistant
- Configure hooks for your AI assistant to enable rules

## Quick Start

### 1. Define a Job
Jobs are multi-step workflows where each Step has clear input and output artifacts, making them easier to manage effectively.

The process of defining a job itself is actually a DeepWork job. You can see it at `.deepwork/jobs/deepwork_jobs/`.

To start the process, just run the first Step in the job:

```
/deepwork_jobs.define
```

Follow the interactive prompts to:
- Name your job
- Define steps with inputs/outputs
- Specify dependencies between steps

It will also prompt you to go on the the next Step in the job.

### 2. Execute Steps

Run individual steps of your job:

```
/your_job_name.step_1
```

The AI will:
- Create a work branch
- Execute the step's instructions
- Generate required outputs
- Guide you to the next step

### 3. Manage Workflows

Use the refine skill to update existing jobs:

```
/deepwork_jobs.refine
```

## Example: Competitive Research Workflow

Here's a sample 4-step workflow for competitive analysis:

**job.yml**:
```yaml
name: competitive_research
version: "1.0.0"
summary: "Systematic competitive analysis workflow"
description: |
  A comprehensive workflow for analyzing competitors in your market segment.
  Helps product teams understand the competitive landscape by identifying
  competitors, researching their offerings, and developing positioning strategies.

changelog:
  - version: "1.0.0"
    changes: "Initial job creation"

steps:
  - id: identify_competitors
    name: "Identify Competitors"
    description: "Research and list competitors"
    inputs:
      - name: market_segment
        description: "Market segment to analyze"
      - name: product_category
        description: "Product category"
    outputs:
      - competitors.md
    dependencies: []

  - id: primary_research
    name: "Primary Research"
    description: "Analyze competitors' self-presentation"
    inputs:
      - file: competitors.md
        from_step: identify_competitors
    outputs:
      - primary_research.md
      - competitor_profiles/
    dependencies:
      - identify_competitors

  # ... additional steps
```

Usage:
```
/competitive_research.identify_competitors
# AI creates work branch and asks for market_segment, product_category
# Generates competitors.md

/competitive_research.primary_research
# AI reads competitors.md
# Generates primary_research.md and competitor_profiles/
```

## Architecture

DeepWork follows a **Git-native, installation-only** design:

- **No runtime daemon**: DeepWork is purely a CLI tool
- **Git-based workflow**: All work happens on dedicated branches
- **Skills as interface**: AI agents interact via generated skill files
- **Platform-agnostic**: Works with any AI coding assistant that supports skills

### Directory Structure

```
your-project/
├── .deepwork/
│   ├── config.yml          # Platform configuration
│   ├── rules/              # Rule definitions (v2 format)
│   │   └── rule-name.md    # Individual rule files
│   ├── tmp/                # Temporary state (gitignored)
│   │   └── rules/queue/    # Rule evaluation queue
│   └── jobs/               # Job definitions
│       └── job_name/
│           ├── job.yml     # Job metadata
│           └── steps/      # Step instructions
├── .claude/                # Claude Code skills (auto-generated)
│   └── skills/
│       ├── deepwork_jobs.define.md
│       └── job_name.step_name.md
└── .gemini/                # Gemini CLI skills (auto-generated)
    └── skills/
        └── job_name/
            └── step_name.toml
```

**Note**: Work outputs are created on dedicated Git branches (e.g., `deepwork/job_name-instance-date`), not in a separate directory.

## Documentation

- **[Architecture](doc/architecture.md)**: Complete design specification
- **[Doc Specs](doc/doc-specs.md)**: Document specification format for output quality criteria
- **[Contributing](CONTRIBUTING.md)**: Setup development environment and contribute
- **[Nix Flakes Guide](doc/nix-flake.md)**: Comprehensive guide for using DeepWork with Nix flakes

## Development with Nix

DeepWork is available as a Nix flake for reproducible development environments:

```bash
# Using Nix flakes
nix develop

# Or with direnv (automatic activation - recommended)
echo "use flake" > .envrc
direnv allow
```

The Nix environment provides all dependencies including Python 3.11, uv, pytest, ruff, and mypy.

### Installing DeepWork from Flake

You can also install deepwork directly from the flake:

```bash
# Install deepwork from this flake
nix profile install github:Unsupervisedcom/deepwork

# Or run it without installing
nix run github:Unsupervisedcom/deepwork -- --help

# Or build the package
nix build github:Unsupervisedcom/deepwork
```

## Project Structure

```
deepwork/
├── src/deepwork/
│   ├── cli/              # Command-line interface
│   ├── core/             # Core functionality
│   │   ├── parser.py     # Job definition parsing
│   │   ├── detector.py   # Platform detection
│   │   ├── generator.py  # Skill file generation
│   │   ├── rules_parser.py     # Rule parsing
│   │   ├── pattern_matcher.py  # Variable pattern matching
│   │   ├── rules_queue.py      # Rule state queue
│   │   └── command_executor.py # Command action execution
│   ├── hooks/            # Cross-platform hook wrappers
│   │   ├── wrapper.py    # Input/output normalization
│   │   ├── rules_check.py    # Rule evaluation hook
│   │   ├── claude_hook.sh    # Claude Code adapter
│   │   └── gemini_hook.sh    # Gemini CLI adapter
│   ├── templates/        # Jinja2 templates
│   │   ├── claude/       # Claude Code templates
│   │   └── gemini/       # Gemini CLI templates
│   ├── schemas/          # JSON schemas
│   └── utils/            # Utilities (fs, yaml, git, validation)
├── tests/
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   └── fixtures/         # Test fixtures
└── doc/                  # Documentation
```

## Features

### Job Definition
Define structured, multi-step workflows where each step has clear requirements and produces specific results.
- **Dependency Management**: Explicitly link steps with automatic sequence handling and cycle detection.
- **Artifact Passing**: Seamlessly use file outputs from one step as inputs for future steps.
- **Dynamic Inputs**: Support for both fixed file references and interactive user parameters.
- **Human-Readable YAML**: Simple, declarative job definitions that are easy to version and maintain.
- **Doc Specs**: Reference doc specs to enforce quality criteria on document outputs (see [doc specs documentation](doc/doc-specs.md)).

### Git-Native Workflow
Maintain a clean repository with automatic branch management and isolation.
- **Automatic Branching**: Every job execution happens on a dedicated work branch (e.g., `deepwork/my-job-2024`).
- **Namespace Isolation**: Run multiple concurrent jobs or instances without versioning conflicts.
- **Full Traceability**: All AI-generated changes, logs, and artifacts are tracked natively in your Git history.

### Automated Rules
Enforce project standards and best practices without manual oversight. Rules monitor file changes and automatically prompt your AI assistant to follow specific guidelines when relevant code is modified.
- **Automatic Triggers**: Detect when specific files or directories are changed to fire relevant rules.
- **File Correspondence**: Define bidirectional (set) or directional (pair) relationships between files.
- **Command Actions**: Run idempotent commands (formatters, linters) automatically when files change.
- **Contextual Guidance**: Instructions are injected directly into the AI's workflow at the right moment.

**Example Rule** (`.deepwork/rules/source-test-pairing.md`):
```markdown
---
name: Source/Test Pairing
set:
  - src/{path}.py
  - tests/{path}_test.py
compare_to: base
---
When source files change, corresponding test files should also change.
Please create or update tests for the modified source files.
```

**Example Command Rule** (`.deepwork/rules/format-python.md`):
```markdown
---
name: Format Python
trigger: "**/*.py"
action:
  command: "ruff format {file}"
  run_for: each_match
compare_to: prompt
---
```

### Multi-Platform Support
Generate native commands and skills tailored for your AI coding assistant.
- **Native Integration**: Works directly with the skill/command formats of supported agents.
- **Context-Aware**: Skills include all necessary context (instructions, inputs, and dependencies) for the AI.
- **Expanding Ecosystem**: Currently supports **Claude Code** and **Gemini CLI**, with more platforms planned.

## Contributing

DeepWork is currently in MVP phase. Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for the full development guide.

## License

DeepWork is licensed under the Business Source License 1.1 (BSL 1.1). See [LICENSE.md](LICENSE.md) for details.

### Key Points

- **Free for non-competing use**: You can use DeepWork freely for internal workflow automation, education, research, and development
- **Change Date**: On January 14, 2030, the license will automatically convert to Apache License 2.0
- **Prohibited Uses**: You cannot use DeepWork to build products that compete with DeepWork or Unsupervised.com, Inc. in workflow automation or data analysis
- **Contributing**: Contributors must sign our [Contributor License Agreement (CLA)](CLA/version_1/CLA.md)

For commercial use or questions about licensing, please contact legal@unsupervised.com

## Credits

- Inspired by [GitHub's spec-kit](https://github.com/github/spec-kit)

