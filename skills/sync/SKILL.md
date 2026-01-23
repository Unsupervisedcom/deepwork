---
name: sync
description: Sync DeepWork job definitions to platform-specific skills. Use after modifying job definitions, adding new jobs, or changing platform configurations.
---

# DeepWork Sync (Agent Skill)

This agent skill automatically detects when job definitions need to be synced to platform skills.

## Automatic Invocation

Claude will invoke this skill automatically when:
- Job definitions are modified in `.deepwork/jobs/`
- New jobs are created with `/deepwork_jobs.implement`
- Platform configuration changes are detected
- Step instructions or hooks are updated

## What This Skill Does

When invoked, this skill:
1. Detects changes to job definitions
2. Identifies which platforms need skill regeneration
3. Provides guidance on running `deepwork sync` or `/deepwork:sync`
4. Explains what will be updated (skills, hooks, platform settings)

## Manual Command

Users can also explicitly run the sync command:
```
/deepwork:sync
```

## Related

- **Command**: `/deepwork:sync` - User-invocable command for syncing
- **CLI**: `deepwork sync` - Direct CLI tool invocation

To sync all jobs for all configured platforms:

```bash
deepwork sync
```

This will:
1. Read configuration from `.deepwork/config.yml`
2. Scan all jobs in `.deepwork/jobs/`
3. Generate skills for each configured platform
4. Update hooks in platform settings

### Custom Path

To sync a project in a specific directory:

```bash
deepwork sync --path /path/to/project
```

## When to Use Sync

Run `deepwork sync` when you:

- **Created a new job** with `/deepwork_jobs.define` and `/deepwork_jobs.implement`
- **Modified a job definition** (`job.yml` or step instructions)
- **Updated job hooks** (quality criteria, validation scripts)
- **Changed platform configuration** in `.deepwork/config.yml`
- **Added a new platform** to the project
- **Updated DeepWork** to a newer version

## What Gets Synced

The sync command processes:

### Job Definitions
- Reads all `job.yml` files from `.deepwork/jobs/*/job.yml`
- Parses step metadata (inputs, outputs, dependencies)
- Reads step instruction files
- Extracts quality criteria and hooks

### Platform Skills
For each platform, generates:

**Claude Code** (`.claude/skills/*.md`):
- Step skills: `/job_name.step_name`
- Meta skills: `/deepwork_jobs.*`, `/deepwork_rules.*`
- Frontmatter with hooks configuration
- Quality validation prompts

**Gemini CLI** (`.gemini/skills/*/tool.toml`):
- Step commands in TOML format
- Job metadata and instructions
- Input/output specifications

### Hooks
Updates platform settings with:
- Stop hooks for quality validation
- Pre/Post hooks for rules checking
- Command hooks for automated actions

## Generated Structure

After sync, you'll have updated:

```
.claude/
├── settings.json          # Updated with hooks
└── skills/
    ├── job_name.step_1.md
    ├── job_name.step_2.md
    └── ...

.gemini/
└── skills/
    └── job_name/
        ├── step_1.toml
        └── step_2.toml
```

## Verify Sync

After running sync:

1. **Check skill files exist**: Look in `.claude/skills/` or `.gemini/skills/`
2. **Try invoking a skill**: e.g., `/deepwork_jobs.define`
3. **Check hooks**: View `.claude/settings.json` for hook configurations

## Troubleshooting

**"No jobs found" warning**:
- Ensure `.deepwork/jobs/` directory exists
- Check that job directories contain `job.yml` files
- Verify job YAML is valid

**Skills not appearing**:
- Restart your AI agent CLI after sync
- Check `.deepwork/config.yml` has correct platform names
- Verify platform directories exist (`.claude/`, `.gemini/`)

**Invalid job definition errors**:
- Review job.yml syntax against schema
- Check step IDs are unique
- Ensure all dependencies reference valid step IDs
- Validate YAML with: `python -c "import yaml; yaml.safe_load(open('.deepwork/jobs/my_job/job.yml'))"`

**Hooks not working**:
- Confirm hooks are defined in `job.yml` or step instructions
- Check `.claude/settings.json` was updated
- Restart Claude Code to reload settings

## Advanced Usage

### Sync Specific Job
While the sync command processes all jobs, you can:
1. Temporarily move other jobs out of `.deepwork/jobs/`
2. Run sync
3. Move them back

### Add Custom Skills
Standard jobs (like deepwork_jobs) are auto-synced. For custom skills:
1. Create `.deepwork/jobs/my_job/`
2. Add `job.yml` and step instructions
3. Run `deepwork sync`

## Related Commands

- `/deepwork:install` - Initial DeepWork setup
- `/deepwork_jobs.implement` - Generate job after defining it
- `/deepwork_rules.define` - Create automated rules
