---
name: Skill Generation
keywords:
  - sync
  - templates
  - jinja
  - skills
  - commands
last_updated: 2025-02-01
---

# Skill Generation

How DeepWork generates platform-specific skills from expert definitions.

## The Sync Process

Running `deepwork sync`:

1. Loads `config.yml` to get configured platforms
2. Discovers all expert directories in `.deepwork/experts/`
3. For each expert, discovers workflows in `workflows/` subdirectory
4. Parses each `workflow.yml` into dataclasses
5. For each workflow and platform, generates skills using Jinja2 templates
6. Writes skill files to platform-specific directories
7. Syncs hooks and permissions to platform settings

## Generated Skill Types

### Workflow Meta-Skill
- One per workflow
- Routes user intent to appropriate step
- Lists available steps in the workflow
- Claude: `.claude/skills/[expert-name].[workflow-name]/SKILL.md`

### Step Skills
- One per step
- Contains full instructions, inputs, outputs
- Includes workflow position and navigation
- Claude: `.claude/skills/[expert-name].[step-id]/SKILL.md`

## Skill Naming Convention

Skills use 2-part naming: `{expert-name}.{step-id}`

Examples:
- `experts.define` - The define step in the experts expert
- `experts.implement` - The implement step
- `deepwork-rules.define` - The define step in deepwork-rules expert

## Template Variables

Templates receive rich context including:

**Expert Context**:
- `expert_name` - The expert identifier (hyphenated)

**Workflow Context**:
- `workflow_name`, `workflow_version`, `workflow_summary`, `workflow_description`
- `total_steps`, `execution_entries`

**Step Context**:
- `step_id`, `step_name`, `step_description`
- `instructions_content` (full markdown from instructions file)
- `user_inputs`, `file_inputs`, `outputs`, `dependencies`
- `exposed`, `agent`
- `workflow_step_number`, `workflow_total_steps`
- `next_step`, `prev_step`

**Quality & Hooks**:
- `quality_criteria` (array of strings)
- `hooks` (dict by platform event name)

## Template Location

Templates live in `src/deepwork/templates/[platform]/`:

```
templates/
├── claude/
│   ├── skill-workflow-meta.md.jinja
│   ├── skill-workflow-step.md.jinja
│   └── agent-expert.md.jinja
└── gemini/
    ├── skill-workflow-meta.toml.jinja
    └── skill-workflow-step.toml.jinja
```

## Platform Differences

**Claude Code**:
- Markdown format with YAML frontmatter
- Uses `---` delimited frontmatter for metadata
- Hook events: `Stop`, `SubagentStop`, `PreToolUse`, `UserPromptSubmit`
- Skills directory: `.claude/skills/`
- Agents directory: `.claude/agents/`

**Gemini CLI**:
- TOML format
- No skill-level hooks (global only)
- Skills directory: `.gemini/skills/`

## The Generator Class

`ExpertGenerator` in `core/experts_generator.py`:

```python
generator = ExpertGenerator()

# Generate all skills for an expert
paths = generator.generate_all_expert_skills(
    expert=expert_definition,
    adapter=claude_adapter,
    output_dir=project_path,
    project_root=project_path
)

# Generate single step skill
path = generator.generate_workflow_step_skill(
    expert=expert_def,
    workflow=workflow,
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
name: experts.define
description: "Step description"
user-invocable: false  # when exposed: false
context: fork          # when agent is specified
agent: experts
hooks:
  Stop:
    - hooks:
        - type: command
          command: ".deepwork/experts/experts/workflows/new_workflow/hooks/validate.sh"
---
```

## Permissions Syncing

After generating skills, adapters sync permissions:

- Base permissions (read `.deepwork/tmp/**`)
- Skill invocation permissions (`Skill(expert.step_id)`)

Permissions are added to `.claude/settings.json` in the `permissions.allow` array.
