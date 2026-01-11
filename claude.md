# DeepWork - Project Context for Claude Code

## Project Overview

DeepWork is a framework for enabling AI agents to perform complex, multi-step work tasks across any domain. It is inspired by GitHub's spec-kit but generalized for any job type - from competitive research to ad campaign design to monthly reporting.

**Key Insight**: DeepWork is an *installation tool* that sets up job-based workflows in your project. After installation, all work is done through your chosen AI agent CLI (like Claude Code) using slash commands. The DeepWork CLI itself is only used for initial setup.

## Core Concepts

### Jobs
Jobs are complex, multi-step tasks defined once and executed many times by AI agents. Examples:
- Feature Development
- Competitive Research
- Ad Campaign Design
- Monthly Sales Reporting
- Data-Driven Research

### Steps
Each job consists of reviewable steps with clear inputs and outputs. For example:
- Competitive Research steps: `identify_competitors` → `primary_research` → `secondary_research` → `report` → `position`
- Each step becomes a slash command: `/competitive_research.identify_competitors`

## Architecture Principles

1. **Job-Agnostic**: Supports any multi-step workflow, not just software development
2. **Git-Native**: All work products are versioned for collaboration and context accumulation
3. **Step-Driven**: Jobs decomposed into reviewable steps with clear inputs/outputs
4. **Template-Based**: Job definitions are reusable and shareable via Git
5. **AI-Neutral**: Supports multiple AI platforms (Claude Code, Gemini, Copilot, etc.)
6. **Stateless Execution**: All state stored in filesystem artifacts for transparency
7. **Installation-Only CLI**: DeepWork installs skills/commands then gets out of the way

## Project Structure

```
deepwork/
├── src/deepwork/
│   ├── cli/              # CLI commands (install, etc.)
│   ├── core/             # Core logic (project init, detection, generation)
│   ├── templates/        # Skill templates per AI platform
│   │   ├── claude/
│   │   ├── gemini/
│   │   └── copilot/
│   ├── schemas/          # Job definition schemas
│   └── utils/            # Utilities (git, yaml, validation)
├── tests/                # Test suite
├── docs/                 # Documentation
└── doc/architecture.md   # Detailed architecture document
```

## Technology Stack

- **Language**: Python 3.11+
- **Dependencies**: Jinja2 (templates), PyYAML (config), GitPython (git ops)
- **Distribution**: uv/pipx for modern Python package management
- **Testing**: pytest with pytest-mock
- **Linting**: ruff
- **Type Checking**: mypy

## Development Environment

This project uses Nix for reproducible development environments:

```bash
# Enter development environment
nix-shell

# Inside nix-shell, use uv for package management
uv sync                  # Install dependencies
uv run pytest           # Run tests
```

## How DeepWork Works

### 1. Installation
Users install DeepWork globally, then run it in a Git project:
```bash
cd my-project/
deepwork install --claude
```

This installs core skills into `.claude/`:
- `deepwork.define` - Interactive job definition wizard
- `deepwork.refine` - Refine existing job definitions

### 2. Job Definition
Users define jobs via Claude Code:
```
/deepwork.define
```

The agent guides you through defining:
- Job name and description
- Steps with inputs/outputs
- Dependencies between steps
- Instructions for each step

Job definitions are stored in `.deepwork/jobs/[job-name]/` and tracked in Git.

### 3. Job Execution
Execute jobs via slash commands in Claude Code:
```
/competitive_research.identify_competitors
```

Each step:
- Creates/uses a work branch (`work/[job-name]-[instance]`)
- Reads inputs from previous steps
- Generates outputs for review
- Suggests next step

### 4. Work Completion
- Review outputs in `work/[branch-name]/`
- Commit artifacts as you progress
- Create PR for team review
- Merge to preserve work products for future context

## Target Project Structure (After Installation)

```
my-project/
├── .git/
├── .claude/                    # Claude Code skills
│   ├── skill-deepwork.define.md
│   ├── skill-deepwork.refine.md
│   └── skill-[job].[step].md
├── .deepwork/                  # DeepWork configuration
│   ├── config.yml
│   └── jobs/
│       └── [job-name]/
│           ├── job.yml
│           └── steps/
│               └── [step].md
└── work/                       # Work products (on branches)
    └── [job-name]-[instance]/
        └── [outputs].md
```

## Implementation Phases

### Phase 1: Core Runtime (Current)
- [ ] Project structure and build system
- [ ] Job definition parser
- [ ] Registry implementation
- [ ] Basic Git integration
- [ ] Template renderer
- [ ] Unit tests for core components

### Phase 2: CLI and Installation
- [ ] CLI command framework
- [ ] `install` command with platform detection
- [ ] `define` command with interactive wizard
- [ ] Integration tests

### Phase 3: Runtime Engine
- [ ] Step execution engine
- [ ] Context preparation and injection
- [ ] Output validation system
- [ ] State management

### Phase 4: AI Platform Integration
- [ ] Claude Code skill generation
- [ ] Gemini command generation
- [ ] Platform-specific templates

### Phase 5: Job Ecosystem
- [ ] Reference job definitions
- [ ] Job validation tools
- [ ] Documentation and examples

## Key Files to Reference

- `doc/architecture.md` - Comprehensive architecture documentation
- `readme.md` - High-level project overview
- `shell.nix` - Development environment setup

## Development Guidelines

1. **Read Before Modifying**: Always read existing code before suggesting changes
2. **Security**: Avoid XSS, SQL injection, command injection, and OWASP top 10 vulnerabilities
3. **Simplicity**: Don't over-engineer; make only requested changes
4. **Testing**: Write tests for new functionality
5. **Type Safety**: Use type hints for better code quality
6. **No Auto-Commit**: DO NOT automatically commit changes to git. Let the user review and commit changes themselves.

## Current Status

The project is in early development (Phase 1). The architecture is defined, and we're building the core runtime components.

## Success Metrics

1. **Usability**: Users can define and execute new jobs in <30 minutes
2. **Reliability**: 99%+ of steps execute successfully on first try
3. **Performance**: Job import completes in <10 seconds
4. **Extensibility**: New AI platforms can be added in <2 days
5. **Quality**: 90%+ test coverage, zero critical bugs

## Questions or Issues?

- See `doc/architecture.md` for detailed design documentation
- Check `readme.md` for high-level concepts
- Reference implementation phases for current work focus
