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
    ├── agents.md.template            # AGENTS.md structure
    ├── job.yml.example               # Complete job example
    └── step_instruction.md.example   # Complete step example
```

## Version Management

- Version is tracked in `job.yml`
- Bump patch version (0.0.x) for instruction improvements
- Bump minor version (0.x.0) for new features or structural changes
- Always update changelog when bumping version

## Learnings

### AskUserQuestion Tool Does Not Exist (2026-02-01)

**Issue**: The step instructions and expert documentation referenced a tool called
`AskUserQuestion` that does not exist in Claude Code's toolset.

**Symptom**: When running the define step, the agent would output all questions as
a plain text list instead of asking them interactively one at a time.

**Root Cause**: The phrase "ask structured questions" was documented as triggering
the `AskUserQuestion` tool, but this was aspirational - the tool was never
implemented in Claude Code.

**Fix Applied**:
- Removed all references to `AskUserQuestion` tool
- Updated instructions to say "ask questions one at a time"
- Clarified that questions should be presented individually with waits for responses

**Files Changed**:
- `src/deepwork/standard_jobs/deepwork_jobs/steps/define.md`
- `src/deepwork/standard_jobs/deepwork_rules/steps/define.md`
- `src/deepwork/standard/experts/deepwork_jobs/topics/step_instructions.md`
- `library/jobs/spec_driven_development/steps/*.md` (multiple files)

**Lesson**: Do not reference tools in instructions unless they actually exist.
When specifying interactive behavior, be explicit about the expected pattern
(one question at a time, wait for response) rather than referencing hypothetical
tooling.

## Last Updated

- Date: 2026-02-01
- From conversation about: Learning why define step output questions as plain text
