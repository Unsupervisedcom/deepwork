# Job Management

This folder and its subfolders are managed using the `deepwork_jobs` slash commands.

## Recommended Commands

- `/deepwork_jobs.define` - Create or modify the job.yml specification
- `/deepwork_jobs.implement` - Generate step instruction files from the specification
- `/deepwork_jobs.learn` - Improve instructions based on execution learnings

## Directory Structure

```
.
├── AGENTS.md          # This file - project context and guidance
├── job.yml            # Job specification (created by /deepwork_jobs.define)
├── steps/             # Step instruction files (created by /deepwork_jobs.implement)
│   └── *.md           # One file per step
├── hooks/             # Custom validation scripts and prompts
│   └── *.md|*.sh      # Hook files referenced in job.yml
└── templates/         # Example file formats and templates
    └── *.md|*.yml     # Templates referenced in step instructions
```

## Editing Guidelines

1. **Use slash commands** for structural changes (adding steps, modifying job.yml)
2. **Direct edits** are fine for minor instruction tweaks
3. **Run `/deepwork_jobs.learn`** after executing job steps to capture improvements
4. **Run `deepwork sync`** after any changes to regenerate commands
