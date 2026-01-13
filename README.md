# DeepWork

> Framework for enabling AI agents to perform complex, multi-step work tasks

DeepWork is a tool for defining and executing multi-step workflows with AI coding assistants like Claude Code, Google Gemini, and GitHub Copilot. It enables you to decompose complex tasks into manageable steps, with clear inputs, outputs, and dependencies.

## Supported Platforms

| Platform | Status | Command Format | Hooks Support |
|----------|--------|----------------|---------------|
| **Claude Code** | Full Support | Markdown | Yes (stop_hooks, pre/post) |
| **Gemini CLI** | Full Support | TOML | No (global only) |
| OpenCode | Planned | Markdown | No |
| GitHub Copilot CLI | Planned | Markdown | No (tool permissions only) |

## Installation

### Prerequisites

- Python 3.11 or higher
- Git repository
- One of: Claude Code or Gemini CLI

### Install DeepWork

```bash
# Using uv (recommended)
uv pip install -e .

# Or using pip
pip install -e .
```

### Install in Your Project

#### Claude Code

```bash
cd your-project/
deepwork install --platform claude
```

#### Gemini CLI

```bash
cd your-project/
deepwork install --platform gemini
```

**Gemini CLI Notes**:
- Commands are generated as TOML files in `.gemini/commands/`
- Commands use colon (`:`) namespacing: `/job_name:step_id`
- Gemini CLI does not support command-level hooks; quality validation is embedded in prompts
- See [Gemini CLI documentation](https://geminicli.com/docs/) for more details

This will:
- Create `.deepwork/` directory structure
- Generate core DeepWork jobs
- Install DeepWork jobs for your AI assistant
- Configure hooks for your AI assistant to enable policies

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
- **Skills as interface**: AI agents interact via generated markdown skill files
- **Platform-agnostic**: Works with any AI coding assistant that supports skills

### Directory Structure

```
your-project/
├── .deepwork/
│   ├── config.yml          # Platform configuration
│   └── jobs/               # Job definitions
│       └── job_name/
│           ├── job.yml     # Job metadata
│           └── steps/      # Step instructions
├── .claude/                # Claude Code commands (auto-generated)
│   └── commands/
│       ├── deepwork_jobs.define.md
│       └── job_name.step_name.md
└── .gemini/                # Gemini CLI commands (auto-generated)
    └── commands/
        └── job_name/
            └── step_name.toml
```

**Note**: Work outputs are created on dedicated Git branches (e.g., `deepwork/job_name-instance-date`), not in a separate directory.

## Development

### Setup Development Environment

```bash
# Using Nix (recommended)
nix-shell

# Or manually
uv sync
```

### Run Tests

```bash
# All tests
uv run pytest tests/ -v

# Unit tests only
uv run pytest tests/unit/ -v

# Integration tests only
uv run pytest tests/integration/ -v

# With coverage
uv run pytest tests/ --cov=deepwork --cov-report=html
```

### Code Quality

```bash
# Linting
ruff check src/

# Type checking
mypy src/

# Format code
ruff format src/
```

## Documentation

- **[Architecture](doc/architecture.md)**: Complete design specification

## Project Structure

```
deepwork/
├── src/deepwork/
│   ├── cli/              # Command-line interface
│   ├── core/             # Core functionality
│   │   ├── parser.py     # Job definition parsing
│   │   ├── detector.py   # Platform detection
│   │   └── generator.py  # Skill file generation
│   ├── templates/        # Jinja2 templates
│   │   ├── claude/       # Claude Code templates
│   │   └── gemini/       # Gemini CLI templates
│   ├── schemas/          # JSON schemas
│   └── utils/            # Utilities (fs, yaml, git, validation)
├── tests/
│   ├── unit/             # Unit tests (147 tests)
│   ├── integration/      # Integration tests (19 tests)
│   └── fixtures/         # Test fixtures
└── doc/                  # Documentation
```

## Features

### Job Definition

- **Declarative YAML**: Define workflows in simple, readable YAML
- **JSON Schema Validation**: Automatic validation of job structure
- **Dependency Management**: Explicit dependencies with cycle detection
- **File & User Inputs**: Support for both user parameters and file outputs from previous steps

### Skill Generation

- **Template-Based**: Jinja2 templates for consistent skill generation
- **Context-Aware**: Skills include all necessary context (instructions, inputs, dependencies)
- **Multi-Platform**: Generate skills for different AI platforms

### Git Integration

- **Work Branches**: Automatic work branch creation and management
- **Namespace Isolation**: Multiple concurrent job instances supported
- **Version Control**: All outputs tracked in Git

### Policies

Policies automatically enforce team guidelines when files change:

```yaml
# .deepwork.policy.yml
- name: "Update docs on config changes"
  trigger: "app/config/**/*"
  safety: "docs/install_guide.md"
  instructions: |
    Configuration files changed. Please update docs/install_guide.md
    if installation instructions need to change.
```

**How it works**:
1. When you start a Claude Code session, the baseline git state is captured
2. When the agent finishes, changed files are compared against policy triggers
3. If policies fire (trigger matches, no safety match), Claude is prompted to address them
4. Use `<promise policy="Policy Name">addressed</promise>` to mark policies as handled

**Use cases**:
- Keep documentation in sync with code changes
- Require security review for auth code modifications
- Enforce changelog updates for API changes

Define policies interactively:
```
/deepwork_policy.define
```

## Roadmap

### Phase 2: Runtime Enhancements (Planned)

- Job execution tracking
- Automatic skill invocation
- Progress visualization
- Error recovery

### Phase 3: Advanced Features (Planned)

- Job templates and marketplace
- Parallel step execution
- External tool integration
- Web UI for job management

## Contributing

DeepWork is currently in MVP phase. Contributions welcome!

## License

MIT License - see LICENSE file for details

## Credits

- Inspired by [GitHub's spec-kit](https://github.com/github/spec-kit)
- Built for [Claude Code](https://claude.com/claude-code)

---

**Built with Claude Code** 🤖
