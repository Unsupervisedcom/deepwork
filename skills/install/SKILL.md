---
name: install
description: Install DeepWork in a project. Adds AI platform support and syncs commands for configured platforms. Use when setting up DeepWork in a new or existing project.
---

# DeepWork Install

Install DeepWork in a project with support for AI platforms like Claude Code or Gemini CLI.

## Usage

This skill can be invoked with `/deepwork:install` or Claude may invoke it automatically when detecting a need for DeepWork setup.

### Basic Installation

To install DeepWork with auto-detection:

```bash
deepwork install
```

This will:
1. Check for Git repository
2. Auto-detect available AI platforms (Claude Code, Gemini CLI, etc.)
3. Create `.deepwork/` directory structure
4. Install core job definitions (deepwork_jobs, deepwork_rules)
5. Generate platform-specific skills
6. Configure hooks for rules enforcement

### Specify Platform

To install for a specific platform:

```bash
# For Claude Code
deepwork install --platform claude

# For Gemini CLI
deepwork install --platform gemini
```

### Custom Path

To install in a specific directory:

```bash
deepwork install --path /path/to/project
```

## What Gets Installed

After installation, your project will have:

```
your-project/
├── .deepwork/
│   ├── config.yml          # Platform configuration
│   ├── .gitignore          # Ignores runtime artifacts
│   ├── tmp/                # Temporary state (gitignored)
│   │   └── .gitkeep
│   ├── rules/              # Rule definitions
│   │   └── README.md       # Rules documentation
│   ├── doc_specs/          # Document specifications
│   └── jobs/               # Job definitions
│       ├── deepwork_jobs/  # Core job management
│       └── deepwork_rules/ # Rules management
├── .claude/                # Claude Code skills (if detected)
│   ├── settings.json       # Hooks configuration
│   └── skills/
│       ├── deepwork_jobs.define.md
│       ├── deepwork_jobs.implement.md
│       └── ...
└── .gemini/                # Gemini CLI skills (if detected)
    └── skills/
        └── ...
```

## Next Steps

After installation:

1. Start your AI agent CLI (e.g., `claude` or `gemini`)
2. Define your first job with `/deepwork_jobs.define`
3. Implement the job with `/deepwork_jobs.implement`
4. Run job steps with `/your_job_name.step_name`

## Requirements

- Python 3.11 or higher
- Git repository
- One of: Claude Code, Gemini CLI, or other supported platform

## Troubleshooting

**"Not a Git repository" error**:
- Run `git init` in your project directory first

**Platform not detected**:
- Ensure `.claude/` or `.gemini/` directory exists
- Or specify the platform explicitly: `--platform claude`

**Permission errors**:
- Ensure you have write access to the project directory
- Check that Python/pipx/uv installation is in your PATH

## Related Commands

- `/deepwork:sync` - Sync job definitions to platform skills
- `/deepwork_jobs.define` - Define a new multi-step job
- `/deepwork_rules.define` - Define automated rules
