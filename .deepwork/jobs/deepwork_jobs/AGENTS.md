# Project Context for deepwork_jobs

This is the source of truth for the `deepwork_jobs` standard job.

## Codebase Structure

- Source location: `src/deepwork/standard_jobs/deepwork_jobs/`
- Working copy: `.deepwork/jobs/deepwork_jobs/`
- Templates: `templates/` directory within each location

## Dual Location Maintenance

**Important**: This job exists in two locations that must be kept in sync:

1. **Source of truth**: `src/deepwork/standard_jobs/deepwork_jobs/`
   - This is where changes should be made first
   - Tracked in version control

2. **Working copy**: `.deepwork/jobs/deepwork_jobs/`
   - Must be updated after changes to source
   - Used by `deepwork sync` to generate commands

After making changes to the source, copy files to the working copy:
```bash
cp src/deepwork/standard_jobs/deepwork_jobs/job.yml .deepwork/jobs/deepwork_jobs/
cp src/deepwork/standard_jobs/deepwork_jobs/steps/*.md .deepwork/jobs/deepwork_jobs/steps/
cp -r src/deepwork/standard_jobs/deepwork_jobs/templates/* .deepwork/jobs/deepwork_jobs/templates/
```

## File Organization

```
deepwork_jobs/
├── AGENTS.md              # This file
├── job.yml                # Job definition
├── make_new_job.sh        # Script to create new job structure
├── steps/
│   ├── define.md          # Define step instructions
│   ├── implement.md       # Implement step instructions
│   ├── learn.md           # Learn step instructions
│   └── supplemental_file_references.md  # Reference documentation
└── templates/
    ├── job.yml.template              # Job spec structure
    ├── step_instruction.md.template  # Step instruction structure
    ├── implementation_summary.md.template
    ├── learning_summary.md.template
    ├── agents.md.template
    ├── example_job.yml               # Complete example
    └── example_step_instruction.md   # Complete example
```

## Version Management

- Version is tracked in `job.yml`
- Bump patch version (0.0.x) for instruction improvements
- Bump minor version (0.x.0) for new features or structural changes
- Always update changelog when bumping version

## Last Updated

- Date: 2026-01-15
- From conversation about: Adding make_new_job.sh script and templates directory
