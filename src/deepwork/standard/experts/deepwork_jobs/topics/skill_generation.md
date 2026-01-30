---
name: Skill Generation
keywords:
  - sync
  - templates
  - jinja
  - skills
  - commands
last_updated: 2025-01-30
---

# Skill Generation

How DeepWork generates platform-specific skills from job definitions.

## The Sync Process

Running `deepwork sync`:

1. Loads `config.yml` to get configured platforms
2. Discovers all job directories in `.deepwork/jobs/`
3. Parses each `job.yml` into `JobDefinition` dataclass
4. For each job and platform, generates skills using Jinja2 templates
5. Writes skill files to platform-specific directories
6. Syncs hooks and permissions to platform settings

## Generated Skill Types

### Meta-Skill (Job Entry Point)
- One per job
- Routes user intent to appropriate step
- Lists available workflows and standalone skills
- Claude: `.claude/skills/[job_name]/SKILL.md`
- Gemini: `.gemini/skills/[job_name]/index.toml`

### Step Skills
- One per step
- Contains full instructions, inputs, outputs
- Includes workflow position and navigation
- Claude: `.claude/skills/[job_name].[step_id]/SKILL.md`
- Gemini: `.gemini/skills/[job_name]/[step_id].toml`

## Template Variables

Templates receive rich context including:

**Job Context**:
- `job_name`, `job_version`, `job_summary`, `job_description`
- `total_steps`, `has_workflows`, `workflows`, `standalone_steps`

**Step Context**:
- `step_id`, `step_name`, `step_description`, `step_number`
- `instructions_content` (full markdown from instructions file)
- `user_inputs`, `file_inputs`, `outputs`, `dependencies`
- `is_standalone`, `exposed`, `agent`

**Workflow Context** (when step is in workflow):
- `workflow_name`, `workflow_summary`
- `workflow_step_number`, `workflow_total_steps`
- `workflow_next_step`, `workflow_prev_step`

**Quality & Hooks**:
- `quality_criteria` (array of strings)
- `hooks` (dict by platform event name)
- `stop_hooks` (backward compat: after_agent hooks)

## Template Location

Templates live in `src/deepwork/templates/[platform]/`:

```
templates/
├── claude/
│   ├── skill-job-meta.md.jinja
│   ├── skill-job-step.md.jinja
│   └── settings.json
└── gemini/
    ├── skill-job-meta.toml.jinja
    └── skill-job-step.toml.jinja
```

## Platform Differences

**Claude Code**:
- Markdown format with YAML frontmatter
- Uses `---` delimited frontmatter for metadata
- Hook events: `Stop`, `SubagentStop`, `PreToolUse`, `UserPromptSubmit`
- Skills directory: `.claude/skills/`

**Gemini CLI**:
- TOML format
- Uses namespace separators via directories
- No skill-level hooks (global only)
- Skills directory: `.gemini/skills/`

## The Generator Class

`SkillGenerator` in `core/generator.py`:

```python
generator = SkillGenerator()

# Generate all skills for a job
paths = generator.generate_all_skills(
    job=job_definition,
    adapter=claude_adapter,
    output_dir=project_path,
    project_root=project_path
)

# Generate single step skill
path = generator.generate_step_skill(
    job=job_def,
    step=step,
    adapter=adapter,
    output_dir=output_dir
)
```

## Doc Spec Integration

When outputs reference doc specs, the generator:

1. Loads doc spec file using `DocSpecParser`
2. Extracts quality criteria, target audience, example document
3. Includes this context in template variables
4. Generated skill displays doc spec requirements inline

## Skill Frontmatter

Claude skills have YAML frontmatter:

```yaml
---
name: job_name.step_id
description: "Step description"
user-invocable: false  # when exposed: false
context: fork          # when agent is specified
agent: general-purpose
hooks:
  Stop:
    - hooks:
        - type: command
          command: ".deepwork/jobs/job_name/hooks/validate.sh"
---
```

## Permissions Syncing

After generating skills, adapters sync permissions:

- Base permissions (read `.deepwork/tmp/**`)
- Skill invocation permissions (`Skill(job_name)`, `Skill(job_name.step_id)`)

Permissions are added to `.claude/settings.json` in the `permissions.allow` array.
