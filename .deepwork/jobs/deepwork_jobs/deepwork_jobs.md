# DeepWork Jobs Reference

This document contains reference information for the `deepwork_jobs` job - the core commands for defining, implementing, and learning from DeepWork jobs.

## Job Structure

A DeepWork job consists of:

```
.deepwork/jobs/[job_name]/
├── job.yml              # Job definition (name, steps, inputs/outputs, hooks)
├── steps/               # Step instruction files
│   └── [step_id].md
├── hooks/               # Custom validation scripts
├── templates/           # Example file formats
└── AGENTS.md
```

## job.yml Schema

```yaml
name: job_name                    # lowercase, underscores
version: "1.0.0"                  # semantic versioning
summary: "Brief description"      # max 200 chars
description: |                    # detailed multi-line
  Full description of the job...

changelog:
  - version: "1.0.0"
    changes: "Initial creation"

steps:
  - id: step_id                   # lowercase, underscores
    name: "Step Name"
    description: "What this step does"
    instructions_file: steps/step_id.md
    inputs:
      - name: param_name          # User-provided parameter
        description: "What to provide"
      - file: filename.md         # File from previous step
        from_step: previous_step_id
    outputs:
      - output_file.md            # Files this step creates
    dependencies:                 # Steps that must complete first
      - previous_step_id
    hooks:                        # Quality validation
      after_agent:
        - prompt: "Validation criteria..."
        - prompt_file: hooks/check.md
        - script: hooks/validate.sh
```

## Stop Hooks (Quality Validation)

Stop hooks allow iterative refinement until quality criteria are met.

**Types:**
1. **Inline Prompt** (`prompt`) - Simple quality criteria
2. **Prompt File** (`prompt_file`) - Detailed/reusable criteria
3. **Script** (`script`) - Programmatic validation (tests, linting)

**Usage:**
```yaml
hooks:
  after_agent:
    - prompt: |
        Verify output meets criteria:
        1. [Criterion 1]
        2. [Criterion 2]
        If ALL met, include `<promise>✓ Quality Criteria Met</promise>`.
```

## Step Instruction File Structure

Each step needs an instruction file at `steps/[step_id].md`:

```markdown
# [Step Name]

## Objective
[Clear statement of what this step accomplishes]

## Task
[Detailed instructions with substeps]

### Process
1. [Substep 1]
2. [Substep 2]

## Output Format
### [output_filename]
[Description and example of output format]

## Quality Criteria
- [Criterion 1]
- [Criterion 2]
- When all criteria are met, include `<promise>✓ Quality Criteria Met</promise>`
```

## Templates

Templates are available in `.deepwork/jobs/deepwork_jobs/templates/`:

| Template | Purpose |
|----------|---------|
| `job.yml.template` | Job specification structure |
| `job.yml.example` | Complete worked example |
| `step_instruction.md.template` | Step instruction structure |
| `step_instruction.md.example` | Complete worked example |
| `agents.md.template` | AGENTS.md structure |

## Directory Setup Script

Create a new job directory structure:

```bash
.deepwork/jobs/deepwork_jobs/make_new_job.sh [job_name]
```

Creates: job directory, steps/, hooks/, templates/, and AGENTS.md.

## Validation Rules

Before creating job.yml:
- Job name: lowercase, underscores, no spaces
- Version: semantic versioning (1.0.0)
- Summary: concise, under 200 characters
- Step IDs: unique, lowercase with underscores
- Dependencies: must reference existing step IDs
- File inputs: `from_step` must be in dependencies
- At least one output per step
- No circular dependencies

## Syncing Commands

After creating/modifying jobs:

```bash
deepwork sync
```

This generates slash-commands in `.claude/commands/` (or platform equivalent).

**Reload commands after sync:**
- **Claude Code**: Type `exit` then run `claude --resume`
- **Gemini CLI**: Run `/memory refresh`

## Using Supplementary Reference Files

Step instructions can reference additional `.md` files for detailed examples or schemas.

See `.deepwork/jobs/deepwork_jobs/steps/supplemental_file_references.md` for documentation.
