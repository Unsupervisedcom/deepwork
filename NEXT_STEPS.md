# Next Steps - Quick Reference

## 🎯 Current Status
- **8/13 steps complete** (61%)
- **120 unit tests passing**
- Core functionality implemented and tested
- Ready for template design phase

---

## ⚠️ BLOCKED: Template Design Review Required

**Before proceeding with Step 10 implementation, templates must be designed and reviewed.**

### What Needs Review:

**Three templates need to be created and approved:**

1. **`skill-deepwork.define.md.jinja`** - Job definition wizard
2. **`skill-deepwork.refine.md.jinja`** - Job refinement tool
3. **`skill-job-step.md.jinja`** - Individual step skill (MOST CRITICAL)

### Review Requirements:

For each template, provide:
- Complete Jinja2 template code
- 2-3 rendered examples showing:
  - Simple job (1 step with user inputs)
  - Complex job (4 steps with dependencies and file inputs)
  - Edge cases

### Why This Matters:

Templates are the core interface between DeepWork and AI agents. They must:
- Follow Claude Code skill format correctly
- Provide clear instructions AI agents can follow
- Handle context passing between steps properly
- Guide users through the workflow smoothly

**Getting this wrong means the entire system won't work.**

---

## 🚀 After Template Approval

Once templates are approved, implement in order:

### Step 9: Platform Detector (~2 hours)
- Detect Claude/Gemini/Copilot availability
- Simple directory checking
- Low risk, straightforward

### Step 10: Template Renderer (~4 hours)
- Implement Jinja2 rendering
- Load approved templates
- Generate skills from job definitions
- Test with all fixtures

### Step 11: CLI Install Command (~3 hours)
- Click-based CLI framework
- Install command with platform options
- Ties all components together
- End-to-end testing

### Step 12: Integration Tests (~2 hours)
- Full workflow tests
- Git integration tests
- CLI tests

### Step 13: Documentation & Polish (~2 hours)
- README with examples
- CHANGELOG
- CI/CD setup
- Final verification

---

## 🏁 MVP Complete

After Steps 9-11, you'll have:
- ✅ Fully working CLI
- ✅ Install DeepWork in projects
- ✅ Parse and validate jobs
- ✅ Generate skills automatically
- ✅ Ready for real usage

Steps 12-13 add polish but aren't required for MVP.

---

## 📝 Template Design Questions

Before designing templates, clarify:

1. **Claude Code skill format conventions?**
   - Required sections?
   - Markdown structure preferences?
   - Example skills to reference?

2. **Work branch naming?**
   - User-specified vs auto-generated?
   - Timestamp format preference?
   - Work directory structure?

3. **Instruction style?**
   - Imperative ("Create file X")?
   - Descriptive ("This step creates file X")?
   - Conversational?

4. **Error handling?**
   - What should AI do if step fails?
   - Retry logic?
   - User notification approach?

5. **Context passing?**
   - How verbose should file input instructions be?
   - Should skills validate previous outputs?
   - Dependency checking approach?

---

## 🔄 How to Resume

```bash
# 1. Navigate to project
cd /Users/noah/deep-work

# 2. Enter dev environment
nix-shell

# 3. Verify current state
uv run pytest tests/unit/ -v
# Should show: 120 passed in ~1s

# 4. Review STATUS.md for full context
cat STATUS.md

# 5. Design templates (with user)
# Create templates in: src/deepwork/templates/claude/
# Get user approval before implementing

# 6. Implement Steps 9-11
# Follow plan in STATUS.md

# 7. Test end-to-end
# Create test project and verify install works
```

---

## 📁 Key Files Reference

**Documentation:**
- `STATUS.md` - Complete implementation status (this session)
- `NEXT_STEPS.md` - This file (quick reference)
- `doc/architecture.md` - Original architecture spec
- `claude.md` - Project context for Claude

**Core Modules (Complete):**
- `src/deepwork/core/parser.py` - Job parsing (243 lines, 23 tests)
- `src/deepwork/core/registry.py` - Job registry (210 lines, 19 tests)
- `src/deepwork/schemas/job_schema.py` - JSON Schema (137 lines, 10 tests)
- `src/deepwork/utils/fs.py` - Filesystem (134 lines, 23 tests)
- `src/deepwork/utils/git.py` - Git ops (157 lines, 25 tests)
- `src/deepwork/utils/yaml_utils.py` - YAML (82 lines, 20 tests)
- `src/deepwork/utils/validation.py` - Validation (31 lines, included in schema tests)

**Test Fixtures:**
- `tests/fixtures/jobs/simple_job/` - 1-step job
- `tests/fixtures/jobs/complex_job/` - 4-step competitive research job
- `tests/fixtures/jobs/invalid_job/` - Invalid for error testing

**Configuration:**
- `pyproject.toml` - Complete with all dependencies
- `shell.nix` - Nix dev environment
- `.gitignore` - Python/test exclusions

---

## ✅ What's Working

Everything implemented so far works perfectly:

```python
# Parse a job definition
from deepwork.core.parser import parse_job_definition

job = parse_job_definition("tests/fixtures/jobs/complex_job")
print(f"{job.name} v{job.version}: {len(job.steps)} steps")
# Output: competitive_research v1.0.0: 4 steps

# Register a job
from deepwork.core.registry import JobRegistry

registry = JobRegistry(".deepwork")
entry = registry.register_job(
    job.name, job.version, job.description, "jobs/competitive_research"
)
print(f"Registered: {entry.name} at {entry.installed_at}")

# List all jobs
for job in registry.list_jobs():
    print(f"  - {job.name} v{job.version}")

# Git operations
from deepwork.utils.git import is_git_repo, create_branch

if is_git_repo("."):
    create_branch(".", "work/test-job-001", checkout=True)
    print("Created and checked out work branch")

# YAML operations
from deepwork.utils.yaml_utils import load_yaml, save_yaml

data = load_yaml("tests/fixtures/jobs/simple_job/job.yml")
print(f"Job name: {data['name']}")

save_yaml("/tmp/test.yml", {"key": "value"})

# Filesystem operations
from deepwork.utils.fs import safe_write, safe_read, find_files

safe_write("/tmp/test/nested/file.txt", "content")
content = safe_read("/tmp/test/nested/file.txt")
files = find_files("tests/fixtures/jobs", "**/*.yml")
print(f"Found {len(files)} YAML files")
```

All of this works with full test coverage!

---

## 🎨 Template Design Starting Point

### Recommended Approach:

1. **Study existing Claude Code skills** to understand format
2. **Start with `skill-job-step.md.jinja`** (most important)
3. **Create example context data** from `complex_job` fixture
4. **Render a few examples** to see how they look
5. **Get user feedback** before implementing generator

### Template Context Example:

```python
# What will be passed to skill-job-step.md.jinja:
context = {
    "job_name": "competitive_research",
    "job_version": "1.0.0",
    "job_description": "Systematic competitive analysis workflow",

    "step_id": "primary_research",
    "step_name": "Primary Research",
    "step_description": "Analyze competitors' self-presentation",
    "step_number": 2,
    "total_steps": 4,

    "instructions_file": "steps/primary_research.md",
    "instructions_content": "# Primary Research\n\n## Objective\n...",

    "user_inputs": [],  # No user inputs for this step
    "file_inputs": [
        {"file": "competitors.md", "from_step": "identify_competitors"}
    ],
    "outputs": ["primary_research.md", "competitor_profiles/"],
    "dependencies": ["identify_competitors"],

    "next_step": "secondary_research",
    "prev_step": "identify_competitors"
}
```

Use this to design the template!

---

## 💭 Design Considerations

### For `skill-job-step.md.jinja`:

**Must Include:**
- Clear step identification (Name: job.step)
- Step context (number/total)
- Prerequisites section (if dependencies exist)
- Input gathering (user params and/or files)
- Instructions from the step's .md file
- Work branch management
- Output requirements
- Next step guidance

**Should Handle:**
- Steps with no inputs
- Steps with only user inputs
- Steps with only file inputs
- Steps with both input types
- First step (no prev_step)
- Last step (no next_step)
- Multiple outputs
- Directory outputs (ending with /)

**Example Sections:**

```markdown
Name: {{job_name}}.{{step_id}}
Description: {{step_description}}

## Overview
Step {{step_number}} of {{total_steps}} in the {{job_name}} workflow.

{% if dependencies %}
## Prerequisites
This step requires completion of:
{% for dep in dependencies %}
- Step: {{dep}}
{% endfor %}
{% endif %}

{% if user_inputs %}
## Input Parameters
Please provide the following information:
{% for input in user_inputs %}
**{{input.name}}**: {{input.description}}
{% endfor %}
{% endif %}

{% if file_inputs %}
## Required Files
This step requires these files from previous steps:
{% for input in file_inputs %}
- `{{input.file}}` (from step {{input.from_step}})
{% endfor %}
{% endif %}

## Instructions
{{instructions_content}}

## Work Branch
Ensure you're on a work branch for this job instance.
...

## Outputs
Create the following in the work directory:
{% for output in outputs %}
- `work/[branch]/{{output}}`
{% endfor %}

{% if next_step %}
## Next Step
After completing this step, run:
`/{{job_name}}.{{next_step}}`
{% endif %}
```

---

**Ready to start template design whenever you are!**

See STATUS.md for complete context.
