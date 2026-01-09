# DeepWork Architecture

## Overview

DeepWork is a framework for enabling AI agents to perform complex, multi-step work tasks across any domain. Inspired by spec-kit's approach to software development, DeepWork generalizes the pattern to support any job type—from competitive research to ad campaign design to monthly reporting.

**Key Insight**: DeepWork is an *installation tool* that sets up job-based workflows in your project. After installation, all work is done through your chosen AI agent CLI (like Claude Code, Gemini, etc.) using slash commands. The DeepWork CLI itself is only used for the initial setup.

## Core Design Principles

1. **Job-Agnostic**: The framework supports any multi-step workflow, not just software development
2. **Git-Native**: All work products are versioned in Git for collaboration, review, and context accumulation
3. **Step-Driven**: Jobs are decomposed into reviewable steps with clear inputs and outputs
4. **Template-Based**: Job definitions are reusable and shareable via Git repositories
5. **AI-Neutral**: Support for multiple AI platforms (Claude Code, Gemini, Copilot, etc.)
6. **Stateless Execution**: All state is stored in filesystem artifacts, enabling resumability and transparency
7. **Installation-Only CLI**: The deepwork CLI installs skills/commands into projects, then gets out of the way

## Architecture Overview

This document is organized into three major sections:

1. **[DeepWork Tool Architecture](#part-1-deepwork-tool-architecture)** - The DeepWork repository/codebase itself and how it works
2. **[Target Project Architecture](#part-2-target-project-architecture)** - What a project looks like after DeepWork is installed
3. **[Runtime Execution Model](#part-3-runtime-execution-model)** - How AI agents execute jobs using the installed skills

---

# Part 1: DeepWork Tool Architecture

This section describes the DeepWork repository itself - the tool that users install globally and use to set up projects.

## DeepWork Repository Structure

```
deepwork/                       # DeepWork tool repository
├── src/
│   └── deepwork/
│       ├── cli/
│       │   ├── __init__.py
│       │   ├── install.py      # Main install command
│       │   └── commands.py     # Other CLI commands
│       ├── core/
│       │   ├── project.py      # Project initialization
│       │   ├── detector.py     # AI platform detection
│       │   └── generator.py    # Skill file generation
│       ├── templates/          # Skill templates for each platform
│       │   ├── claude/
│       │   │   ├── skill-deepwork.define.md
│       │   │   ├── skill-deepwork.refine.md
│       │   │   └── skill-job-step.md.jinja
│       │   ├── gemini/
│       │   └── copilot/
│       ├── schemas/            # Job definition schemas
│       │   └── job.schema.json
│       └── utils/
│           ├── git.py
│           ├── yaml.py
│           └── validation.py
├── tests/                      # DeepWork tool tests
├── docs/                       # Documentation
├── pyproject.toml
└── README.md
```

## DeepWork CLI Components

### 1. Installation Command (`install.py`)

The only command that runs regularly. When user executes `deepwork install --claude`:

**Responsibilities**:
1. Detect if current directory is a Git repository
2. Detect if specified AI platform is available (check for `.claude/`, `.gemini/`, etc.)
3. Create `.deepwork/` directory structure in the project
4. Copy core skill templates to appropriate AI platform directory
5. Create initial configuration files

**Pseudocode**:
```python
def install(platform: str):
    # Validate environment
    if not is_git_repo():
        raise Error("Must be run in a Git repository")

    # Detect platform
    platform_config = detect_platform(platform)
    if not platform_config.is_available():
        raise Error(f"{platform} not found in this project")

    # Create DeepWork structure
    create_directory(".deepwork/")
    create_directory(".deepwork/jobs/")

    # Install core skills
    skills_to_install = [
        "deepwork.define",   # Interactive job definition
        "deepwork.refine",   # Refine existing job
    ]

    for skill in skills_to_install:
        template = load_template(f"templates/{platform}/skill-{skill}.md")
        write_file(f"{platform_config.skill_dir}/skill-{skill}.md", template)

    # Create config
    config = {
        "platform": platform,
        "version": DEEPWORK_VERSION,
        "installed": datetime.now()
    }
    write_yaml(".deepwork/config.yml", config)

    print(f"✓ DeepWork installed for {platform}")
    print(f"  Run /{skills_to_install[0]} to create your first job")
```

### 2. Platform Detector (`detector.py`)

Identifies which AI platforms are available in the project.

**Detection Logic**:
```python
PLATFORM_SIGNATURES = {
    "claude": {
        "check": lambda: Path(".claude").exists(),
        "skill_dir": ".claude",
        "skill_extension": ".md",
        "skill_prefix": "skill-"
    },
    "gemini": {
        "check": lambda: Path(".gemini").exists(),  # Hypothetical
        "skill_dir": ".gemini",
        "skill_extension": ".md",
        "skill_prefix": "skill-"
    },
    "copilot": {
        "check": lambda: Path(".github/copilot-instructions.md").exists(),
        "skill_dir": ".github",
        "skill_extension": ".md",
        "skill_prefix": "copilot-"
    }
}
```

### 3. Skill Generator (`generator.py`)

Generates AI-platform-specific skill files from job definitions.

When a user defines a job via `/deepwork.define`, this component:
1. Reads the job definition from `.deepwork/jobs/[job-name]/job.yml`
2. Loads platform-specific templates
3. Generates skill files for each step in the job
4. Writes skills to the AI platform's directory

**Example Generation Flow**:
```python
def generate_skills_for_job(job_name: str, platform: str):
    # Load job definition
    job = load_yaml(f".deepwork/jobs/{job_name}/job.yml")

    # Get platform config
    platform_config = PLATFORM_SIGNATURES[platform]

    # Generate skill for each step
    for step in job['steps']:
        skill_name = f"{job_name}.{step['id']}"

        # Load template
        template = load_jinja_template(
            f"templates/{platform}/skill-job-step.md.jinja"
        )

        # Render with step data
        skill_content = template.render(
            job_name=job_name,
            step_id=step['id'],
            step_name=step['name'],
            description=step['description'],
            inputs=step['inputs'],
            outputs=step['outputs'],
            instructions=load_file(step['instructions_file'])
        )

        # Write to platform directory
        skill_path = f"{platform_config['skill_dir']}/skill-{skill_name}.md"
        write_file(skill_path, skill_content)
```

---

# Part 2: Target Project Architecture

This section describes what a project looks like AFTER `deepwork install --claude` has been run.

## Target Project Structure

```
my-project/                     # User's project (target)
├── .git/
├── .claude/                    # Claude Code directory
│   ├── skill-deepwork.define.md       # Core DeepWork skill
│   ├── skill-deepwork.refine.md       # Refine existing jobs
│   ├── skill-competitive_research.identify_competitors.md
│   ├── skill-competitive_research.primary_research.md
│   ├── skill-competitive_research.secondary_research.md
│   ├── skill-competitive_research.comparative_report.md
│   └── skill-competitive_research.positioning.md
├── .deepwork/                  # DeepWork configuration
│   ├── config.yml              # Platform config
│   └── jobs/                   # Job definitions
│       ├── competitive_research/
│       │   ├── job.yml         # Job metadata
│       │   ├── steps/
│       │   │   ├── identify_competitors.md
│       │   │   ├── primary_research.md
│       │   │   ├── secondary_research.md
│       │   │   ├── comparative_report.md
│       │   │   └── positioning.md
│       │   ├── templates/      # Output templates
│       │   └── examples/       # Example outputs
│       └── ad_campaign/
│           └── ...
├── work/                       # Work products (Git branches)
│   ├── competitive-research-acme-2026-01/
│   │   ├── competitors.md
│   │   ├── primary_research.md
│   │   ├── secondary_research.md
│   │   ├── comparison_matrix.md
│   │   └── positioning_strategy.md
│   └── ad-campaign-q1-2026/
│       └── ...
├── (rest of user's project files)
└── README.md
```

## Configuration Files

### `.deepwork/config.yml`

```yaml
platform: claude
version: "1.0.0"
installed: "2026-01-09T10:30:00Z"
```

### Job Definition Example

`.deepwork/jobs/competitive_research/job.yml`:

```yaml
name: competitive_research
version: "1.0.0"
description: "Systematic competitive analysis workflow"

steps:
  - id: identify_competitors
    name: "Identify Competitors"
    description: "Research and list direct and indirect competitors"
    instructions_file: steps/identify_competitors.md
    inputs:
      - name: market_segment
        description: "The market segment to analyze"
      - name: product_category
        description: "Product category"
    outputs:
      - competitors.md
    dependencies: []

  - id: primary_research
    name: "Primary Research"
    description: "Analyze competitors' self-presentation"
    instructions_file: steps/primary_research.md
    inputs:
      - file: competitors.md
        from_step: identify_competitors
    outputs:
      - primary_research.md
      - competitor_profiles/
    dependencies:
      - identify_competitors

  - id: secondary_research
    name: "Secondary Research"
    description: "Research third-party perspectives on competitors"
    instructions_file: steps/secondary_research.md
    inputs:
      - file: competitors.md
        from_step: identify_competitors
      - file: primary_research.md
        from_step: primary_research
    outputs:
      - secondary_research.md
    dependencies:
      - primary_research

  - id: comparative_report
    name: "Comparative Report"
    description: "Create detailed comparison matrix"
    instructions_file: steps/comparative_report.md
    inputs:
      - file: primary_research.md
        from_step: primary_research
      - file: secondary_research.md
        from_step: secondary_research
    outputs:
      - comparison_matrix.md
      - strengths_weaknesses.md
    dependencies:
      - primary_research
      - secondary_research

  - id: positioning
    name: "Market Positioning"
    description: "Define positioning strategy against competitors"
    instructions_file: steps/positioning.md
    inputs:
      - file: comparison_matrix.md
        from_step: comparative_report
    outputs:
      - positioning_strategy.md
    dependencies:
      - comparative_report
```

### Step Instructions Example

`.deepwork/jobs/competitive_research/steps/identify_competitors.md`:

```markdown
# Identify Competitors

## Objective
Research and create a comprehensive list of direct and indirect competitors in the specified market segment.

## Task Description
You will identify companies that compete with us in {{market_segment}} for {{product_category}}.

### Direct Competitors
Companies offering similar products/services to the same customer base:
- List 5-10 companies
- Include company name, website, and brief description
- Note their primary value proposition

### Indirect Competitors
Companies solving the same problem with different approaches:
- List 3-5 companies
- Explain how they're indirect competitors

## Output Format
Create `competitors.md` with this structure:

```markdown
# Competitor Analysis: {{market_segment}}

## Direct Competitors

### [Company Name]
- **Website**: [URL]
- **Description**: [Brief description]
- **Value Proposition**: [What they claim]
- **Target Market**: [Who they serve]

[Repeat for each direct competitor]

## Indirect Competitors

### [Company Name]
- **Website**: [URL]
- **Alternative Approach**: [How they differ]
- **Why Relevant**: [Why they compete with us]

[Repeat for each indirect competitor]
```

## Research Tips
1. Start with web searches for "[product category] companies"
2. Check industry analyst reports (Gartner, Forrester)
3. Look at review sites (G2, Capterra)
4. Check LinkedIn for similar companies
5. Use Crunchbase or similar databases

## Quality Checklist
- [ ] At least 5 direct competitors identified
- [ ] At least 3 indirect competitors identified
- [ ] Each competitor has website and description
- [ ] Value propositions are clearly stated
- [ ] No duplicate entries
```

## Generated Skill Files

When the job is defined, DeepWork generates skill files. Example for Claude Code:

`.claude/skill-competitive_research.identify_competitors.md`:

```markdown
Name: competitive_research.identify_competitors
Description: Research and identify direct and indirect competitors

## Overview
This is step 1 of 5 in the Competitive Research job.

## Instructions

You are performing the "Identify Competitors" step of competitive research.

### Prerequisites
Before starting, ensure you have:
- Market segment defined
- Product category specified

### Input Parameters
Ask the user for the following if not already provided:
1. **market_segment**: The market segment to analyze
2. **product_category**: Product category

### Your Task

[Content from .deepwork/jobs/competitive_research/steps/identify_competitors.md is embedded here]

### Work Branch Management
1. Check if we're on a work branch for this job
2. If not, create a new branch: `work/competitive-research-[timestamp]`
3. All outputs should be created in the `work/[branch-name]/` directory

### Output Requirements
Create the following file in the work directory:
- `work/[branch-name]/competitors.md`

### After Completion
1. Inform the user that step 1 is complete
2. Recommend they review the competitors.md file
3. Suggest running `/competitive_research.primary_research` to continue

---

## Context Files
- Job definition: `.deepwork/jobs/competitive_research/job.yml`
- Step instructions: `.deepwork/jobs/competitive_research/steps/identify_competitors.md`
```

---

# Part 3: Runtime Execution Model

This section describes how AI agents (like Claude Code) actually execute jobs using the installed skills.

## Execution Flow

### User Workflow

1. **Initial Setup** (one-time):
   ```bash
   # In terminal
   cd my-project/
   deepwork install --claude
   ```

2. **Define a Job** (once per job type):
   ```
   # In Claude Code
   User: /deepwork.define

   Claude: I'll help you define a new job. What type of work do you want to define?

   User: Competitive research

   [Interactive dialog to define all the steps]

   Claude: ✓ Job 'competitive_research' created with 5 steps
          Skills installed to .claude/
          Run /competitive_research.identify_competitors to start
   ```

3. **Execute a Job Instance** (each time you need to do the work):
   ```
   # In Claude Code
   User: /competitive_research.identify_competitors

   Claude: Starting competitive research job...
          Created branch: work/competitive-research-20260109-143022

          Please provide:
          - Market segment: ?
          - Product category: ?

   User: Market segment: Enterprise SaaS
         Product category: Project Management

   Claude: [Performs research using web tools, analysis, etc.]
          ✓ Created work/competitive-research-20260109-143022/competitors.md

          Found 8 direct competitors and 4 indirect competitors.
          Review the file and run /competitive_research.primary_research when ready.

   User: [Reviews competitors.md, maybe edits it]
         /competitive_research.primary_research

   Claude: Continuing competitive research (step 2/5)...
          [Reads competitors.md]
          [Performs primary research on each competitor]
          ✓ Created primary_research.md and competitor_profiles/

          Next: /competitive_research.secondary_research

   [Continue through all steps...]
   ```

4. **Complete and Merge**:
   ```
   User: Looks great! Create a PR for this work

   Claude: [Creates PR from work/competitive-research-20260109-143022 to main]
          PR created: https://github.com/user/project/pull/123
   ```

## How Claude Code Executes Skills

When user types `/competitive_research.identify_competitors`:

1. **Skill Discovery**:
   - Claude Code scans `.claude/` directory
   - Finds `skill-competitive_research.identify_competitors.md`
   - Loads the skill definition

2. **Context Loading**:
   - Skill file contains embedded instructions
   - References to job definition and step files
   - Claude reads these files to understand the full context

3. **Execution**:
   - Claude follows the instructions in the skill
   - Uses its tools (Read, Write, WebSearch, WebFetch, etc.)
   - Creates outputs in the specified format

4. **State Management** (via filesystem):
   - Work branch name encodes the job instance
   - Output files track progress
   - Git provides version control and resumability

5. **No DeepWork Runtime**:
   - DeepWork CLI is NOT running during execution
   - Everything happens through Claude Code's native execution
   - Skills are just markdown instruction files that Claude interprets

## Context Passing Between Steps

Since there's no DeepWork runtime process, context is passed through:

### 1. Filesystem (Primary Mechanism)

```
work/competitive-research-20260109-143022/
├── competitors.md              ← Step 1 output
├── primary_research.md          ← Step 2 output
├── competitor_profiles/         ← Step 2 output
│   ├── acme_corp.md
│   ├── widgets_inc.md
│   └── ...
├── secondary_research.md        ← Step 3 output
├── comparison_matrix.md         ← Step 4 output
└── positioning_strategy.md      ← Step 5 output
```

Each skill instructs Claude to:
- Read specific input files from previous steps
- Write specific output files for this step
- All within the same work directory

### 2. Skill Instructions

Each skill file explicitly states its dependencies:

```markdown
### Prerequisites
This step requires outputs from:
- Step 1 (identify_competitors): competitors.md
- Step 2 (primary_research): primary_research.md

### Your Task
1. Read `work/[branch]/competitors.md`
2. Read `work/[branch]/primary_research.md`
3. [Perform analysis]
4. Write `work/[branch]/secondary_research.md`
```

### 3. Git History

When working on similar jobs:
- User: "Do competitive research for Acme Corp, similar to our Widget Corp analysis"
- Claude can read `work/competitive-research-widget-corp/` from git history
- Uses it as a template for style, depth, format

### 4. No Environment Variables Needed

Unlike the original architecture, we don't need special environment variables because:
- The work branch name encodes the job instance
- File paths are explicit in skill instructions
- Git provides all the state management

## Branching Strategy

### Work Branches

Each job execution creates a new work branch:

```bash
work/competitive-research-20260109-143022   # Timestamp-based
work/ad-campaign-q1-2026                    # Name-based (user can specify)
work/monthly-report-2026-01                 # Date-based
```

**Branch Naming Convention**:
```
work/[job-name]-[instance-identifier]
```

Where `instance-identifier` can be:
- Timestamp (default): `20260109-143022`
- User-specified: `acme-corp`, `q1-2026`, etc.
- Logical: "ford" when doing competitive research on Ford Motor Company

### Skill Behavior

Skills should:
1. Check if we're already on a work branch for this job
2. If not, ask user for instance name or auto-generate from timestamp
3. Create branch: `git checkout -b work/[job-name]-[instance]`
4. Create work directory: `mkdir -p work/[job-name]-[instance]`
5. Perform work in that directory

### Completion and Merge

When all steps are done:
1. User reviews all outputs in `work/[branch-name]/`
2. Commits the work
3. Creates PR to main branch
4. After merge, the work products are in the repository
5. Future job instances can reference this work for context/templates

---

## Job Definition and Skill Generation

### The `/deepwork.define` Skill

When a user runs `/deepwork.define` in Claude Code:

**What Happens**:
1. Claude engages in interactive dialog to gather:
   - Job name
   - Job description
   - List of steps (name, description, inputs, outputs)
   - Dependencies between steps

2. Claude creates the job definition files:
   ```
   .deepwork/jobs/[job-name]/
   ├── job.yml                    # Job metadata
   └── steps/
       ├── step1.md               # Instructions for each step
       ├── step2.md
       └── ...
   ```

3. Claude generates skill files using the DeepWork skill template:
   ```
   For each step in job.yml:
     - Load template from embedded knowledge
     - Substitute job/step metadata
     - Write to .claude/skill-[job].[step].md
   ```

4. The `/deepwork.define` skill contains:
   - The job definition YAML schema
   - The skill file template (Jinja2-like)
   - Logic for generation

**How Templates are Embedded**:

The `skill-deepwork.define.md` file contains the template AS DATA:

```markdown
Name: deepwork.define
Description: Interactive job definition wizard

## Instructions

[Instructions for Claude on how to run the wizard...]

## Template for Generated Skills

When you generate skills, use this template:

````markdown
Name: {{job_name}}.{{step_id}}
Description: {{step_description}}

## Overview
This is step {{step_number}} of {{total_steps}} in the {{job_name}} job.

## Instructions

{{instructions_content}}

## Work Branch Management
[Branch creation instructions...]

## Output Requirements
Create these files:
{{#outputs}}
- `work/[branch]/{{this}}`
{{/outputs}}
````

## Job Definition Schema

When creating job.yml, use this structure:
[YAML schema embedded here...]
```

### The `/deepwork.refine` Skill

Allows updating existing job definitions:

```
User: /deepwork.refine competitive_research

Claude: Loading competitive_research job definition...
        What would you like to update?
        1. Add a new step
        2. Modify existing step
        3. Remove a step
        4. Update metadata

User: Add a new step between primary_research and secondary_research

Claude: [Interactive dialog...]
        ✓ Added step 'social_media_analysis'
        ✓ Updated dependencies
        ✓ Regenerated skill files
        New command available: /competitive_research.social_media_analysis
```

## Testing Framework and Strategy

### Test Architecture for DeepWork Tool

The DeepWork tool itself (the Python CLI) has a comprehensive test suite:

```
deepwork/tests/
├── unit/                        # Unit tests for CLI components
│   ├── test_detector.py         # Platform detection
│   ├── test_generator.py        # Skill generation
│   ├── test_yaml_parser.py      # Job definition parsing
│   └── test_validation.py       # Schema validation
├── integration/                 # Integration tests
│   ├── test_install.py          # Installation flow
│   └── test_define_workflow.py  # Job definition workflow
├── fixtures/                    # Test data
│   ├── sample_jobs/
│   │   ├── simple_job/
│   │   │   ├── job.yml
│   │   │   └── steps/
│   │   └── complex_job/
│   ├── expected_skills/         # Expected generated skill files
│   └── mock_projects/           # Mock project directories
└── conftest.py                  # Pytest configuration

```yaml
name: string                    # Unique identifier (snake_case)
version: semver                 # Semantic version
description: string             # Human-readable description
author: string                  # GitHub repo or author name
ai_platforms: string[]          # ["claude", "gemini", "copilot"]
min_deepwork_version: semver    # Minimum DeepWork version required

# Optional: Global configuration
config:
  branch_prefix: string         # Default: "work"
  auto_commit: boolean          # Auto-commit after each step
  require_validation: boolean   # Enforce validation before next step

# Required: Step definitions
steps:
  - id: string                  # Unique step identifier
    name: string                # Display name
    description: string         # What this step does
    inputs: string[]            # Required input artifacts/parameters
    outputs: string[]           # Expected output artifacts
    template: path              # Path to template file
    prompts:                    # Platform-specific prompts
      claude: path
      gemini: path
      copilot: path
    dependencies: string[]      # Step IDs that must complete first
    optional: boolean           # Can be skipped
    validation:                 # Step-specific validation rules
      - type: string
        ...

# Optional: Job-level validation
validation:
  - type: schema|completeness|custom
    file: path                  # File to validate
    schema: path                # For type=schema
    required_sections: string[] # For type=completeness
    script: path                # For type=custom

# Optional: Job-level hooks
hooks:
  on_start: path                # Script to run when job starts
  on_complete: path             # Script to run when job completes
  on_step_complete: path        # Script after each step
```

### Template System

Templates are Markdown files with variable interpolation:

```markdown
# {{STEP_NAME}}

## Objective
{{STEP_DESCRIPTION}}

## Context
You are working on: {{JOB_NAME}}
Current step: {{STEP_ID}} ({{STEP_NUMBER}}/{{TOTAL_STEPS}})

## Inputs
{% for input in INPUTS %}
- Read `{{input.file}}` for {{input.description}}
{% endfor %}

## Your Task
[Detailed instructions for the AI agent...]

## Output Format
Create the following files:
{% for output in OUTPUTS %}
### {{output.file}}
{{output.template}}
{% endfor %}

## Quality Checklist
- [ ] Criterion 1
- [ ] Criterion 2

## Examples
{{EXAMPLES}}
```

Variables populated by runtime:
- Job metadata: `{{JOB_NAME}}`, `{{JOB_DESCRIPTION}}`
- Step metadata: `{{STEP_ID}}`, `{{STEP_NAME}}`, `{{STEP_NUMBER}}`
- Context: `{{INPUTS}}`, `{{OUTPUTS}}`, `{{DEPENDENCIES}}`
- Examples: `{{EXAMPLES}}` (loaded from `examples/` directory if present)

---

## Testing Framework and Strategy

### Test Architecture

```
tests/
├── unit/                       # Unit tests for core components
│   ├── test_job_parser.py
│   ├── test_registry.py
│   ├── test_runtime_engine.py
│   └── test_template_renderer.py
├── integration/                # Integration tests
│   ├── test_job_import.py
│   ├── test_workflow_execution.py
│   └── test_git_integration.py
├── e2e/                        # End-to-end tests
│   ├── test_full_workflow.py
│   └── test_multi_platform.py
├── fixtures/                   # Test data
│   ├── jobs/
│   │   ├── simple_job/
│   │   └── complex_job/
│   ├── templates/
│   └── mock_responses/
└── mocks/                      # Mock AI agent responses
    ├── claude_mock.py
    └── gemini_mock.py
```

### Test Strategy

#### 1. Unit Tests

**Job Parser** (`test_job_parser.py`):
```python
def test_parse_valid_job_definition():
    """Verify parser correctly loads valid job.yml"""

def test_parse_rejects_invalid_schema():
    """Ensure invalid job definitions raise ValidationError"""

def test_parse_resolves_dependencies():
    """Check dependency graph construction"""

def test_parse_handles_optional_steps():
    """Verify optional steps are marked correctly"""
```

**Registry** (`test_registry.py`):
```python
def test_add_job_to_registry():
    """Test job registration"""

def test_detect_version_conflicts():
    """Ensure version conflicts are caught"""

def test_list_installed_jobs():
    """Verify registry query operations"""

def test_remove_job_from_registry():
    """Test job uninstallation"""
```

**Runtime Engine** (`test_runtime_engine.py`):
```python
def test_create_work_branch():
    """Verify branch creation with correct naming"""

def test_step_initialization():
    """Check step setup and context preparation"""

def test_validate_step_outputs():
    """Test output validation against schemas"""

def test_handle_missing_dependencies():
    """Ensure proper error when dependencies not met"""
```

**Template Renderer** (`test_template_renderer.py`):
```python
def test_render_basic_template():
    """Test simple variable substitution"""

def test_render_with_loops():
    """Verify loop constructs work correctly"""

def test_render_with_conditionals():
    """Check conditional rendering"""

def test_escape_special_characters():
    """Ensure proper escaping of Markdown"""
```

#### 2. Integration Tests

**Job Import** (`test_job_import.py`):
```python
def test_import_from_github():
    """Test importing job from GitHub repository"""
    # Mock git clone operation
    # Verify job files copied correctly
    # Check registry updated

def test_import_local_job():
    """Test importing from local directory"""

def test_import_with_dependencies():
    """Verify transitive job dependencies handled"""
```

**Workflow Execution** (`test_workflow_execution.py`):
```python
def test_single_step_execution():
    """Run a single step end-to-end"""
    # Create mock AI responses
    # Execute step
    # Verify outputs created

def test_multi_step_workflow():
    """Execute complete job workflow"""
    # Mock all steps
    # Verify context passes between steps
    # Check final outputs

def test_resume_after_interruption():
    """Test workflow can resume mid-execution"""
```

**Git Integration** (`test_git_integration.py`):
```python
def test_branch_management():
    """Verify branch creation, switching, cleanup"""

def test_commit_integration():
    """Test auto-commit functionality"""

def test_merge_detection():
    """Check detection of merged work"""
```

#### 3. End-to-End Tests

**Full Workflow** (`test_full_workflow.py`):
```python
@pytest.mark.e2e
def test_complete_competitive_research_job():
    """
    Full simulation of competitive research job:
    1. Install DeepWork
    2. Import job definition
    3. Start job
    4. Execute all steps with mocked AI responses
    5. Validate final outputs
    6. Verify Git state
    """
    # Setup test repository
    # Run: deepwork install --claude
    # Run: deepwork import github.com/deepwork-jobs/competitive-research
    # Run: /competitive_research.identify_competitors (mocked)
    # Validate outputs
    # Run: /competitive_research.primary_research (mocked)
    # Continue through all steps
    # Assert final state correct
```

**Multi-Platform** (`test_multi_platform.py`):
```python
@pytest.mark.e2e
def test_claude_and_gemini_compatibility():
    """Verify same job works on different platforms"""
    # Install for Claude
    # Execute job
    # Capture outputs
    # Reinstall for Gemini
    # Execute same job
    # Compare outputs (should be structurally similar)
```

#### 4. Mock AI Agents

Since testing requires AI agent interactions, create mock agents:

```python
# tests/mocks/claude_mock.py
class MockClaudeAgent:
    """Simulates Claude Code agent behavior"""

    def __init__(self, response_fixtures_dir):
        self.fixtures = load_fixtures(response_fixtures_dir)

    def execute_skill(self, skill_name, context):
        """
        Simulates skill execution by returning pre-recorded responses
        based on the skill name and context
        """
        fixture_key = self._get_fixture_key(skill_name, context)
        return self.fixtures[fixture_key]

    def _get_fixture_key(self, skill_name, context):
        # Match to appropriate fixture based on patterns
        # e.g., "competitive_research.identify_competitors" ->
        #       "competitive_research_identify_competitors_001.md"
        ...
```

Fixtures stored as markdown files with expected outputs:
```
tests/fixtures/mock_responses/
├── competitive_research_identify_competitors_001.md
├── competitive_research_primary_research_001.md
└── ...
```

#### 5. Validation Testing

**Schema Validation** (`test_validation.py`):
```python
def test_json_schema_validation():
    """Test validating outputs against JSON schemas"""

def test_completeness_validation():
    """Verify required sections are present"""

def test_custom_validation_scripts():
    """Run custom validation scripts"""
```

#### 6. Performance Testing

**Performance Tests** (`test_performance.py`):
```python
def test_large_job_parsing():
    """Ensure parser handles jobs with 50+ steps"""

def test_template_rendering_performance():
    """Benchmark template rendering with large datasets"""

def test_git_operations_at_scale():
    """Test with repositories containing 100+ work branches"""
```
**Benchmarks** (`benchmarks/`):
Note that these are not run on every change.

```python
def full_simple_cycle():
    """Run the full simple cycle - install the tool in Claude Code, runt he define command and make a simple 3 step job, execute that job and LLM-review the output."""


### CI/CD Integration

**GitHub Actions Workflow** (`.github/workflows/test.yml`):
```yaml
name: DeepWork Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: ["3.11", "3.12"]

    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: uv sync

      - name: Run unit tests
        run: uv run pytest tests/unit -v --cov=deepwork --cov-report=xml

      - name: Run integration tests
        run: uv run pytest tests/integration -v

      - name: Run E2E tests
        run: uv run pytest tests/e2e -v --timeout=300

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: uv tool install ruff
      - run: ruff check deepwork/
      - run: ruff format --check deepwork/

  type-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: uv tool install mypy
      - run: mypy deepwork/
```

### Test Coverage Goals

- **Unit Tests**: 90%+ coverage of core logic
- **Integration Tests**: All major workflows covered
- **E2E Tests**: At least 3 complete job types tested end-to-end
- **Platform Tests**: All supported AI platforms tested
- **Regression Tests**: Add test for each bug found in production

### Testing Best Practices

1. **Fixture Management**: Keep fixtures minimal and focused
2. **Isolation**: Each test should be independent and idempotent
3. **Speed**: Unit tests should run in <1s each; optimize slow tests
4. **Clarity**: Test names should clearly describe what they verify
5. **Mocking**: Mock external dependencies (Git, network, AI agents)
6. **Assertions**: Use specific assertions with clear failure messages
7. **Documentation**: Complex tests should have docstrings explaining setup

---

## Implementation Phases

### Phase 1: Core Runtime
- [ ] Project structure and build system
- [ ] Job definition parser
- [ ] Registry implementation
- [ ] Basic Git integration
- [ ] Template renderer
- [ ] Unit tests for core components

### Phase 2: CLI and Installation
- [ ] CLI command framework
- [ ] `install` command with platform detection
- [ ] `import` command with Git clone
- [ ] `define` command with interactive wizard
- [ ] `list` and `status` commands
- [ ] Integration tests

### Phase 3: Runtime Engine
- [ ] Step execution engine
- [ ] Context preparation and injection
- [ ] Output validation system
- [ ] State management and resumption
- [ ] Environment variable handling
- [ ] Integration tests for workflows

### Phase 4: AI Platform Integration
- [ ] Claude Code skill generation
- [ ] Gemini command generation
- [ ] Copilot instruction generation
- [ ] Platform-specific template variations
- [ ] Multi-platform testing

### Phase 5: Job Ecosystem
- [ ] Create reference jobs (competitive research, campaign design, etc.)
- [ ] Job validation tools
- [ ] Job sharing infrastructure
- [ ] Documentation and examples
- [ ] E2E tests with real job definitions
- [ ] Benchmarks

### Phase 6: Polish and Release
- [ ] Performance optimization
- [ ] Error handling improvements
- [ ] User documentation
- [ ] Tutorial videos
- [ ] Beta release

---

## Technical Decisions

### Language: Python 3.11+
- **Rationale**: Proven ecosystem for CLI tools (click, rich)
- **Alternatives**: TypeScript (more verbose), Go (less flexible for templates)
- **Dependencies**: Jinja2 (templates), PyYAML (config), GitPython (Git ops)

### Distribution: uv/pipx
- **Rationale**: Modern Python tooling, fast, isolated environments
- **Alternatives**: pip (global pollution), Docker (heavyweight for CLI)

### State Storage: Filesystem + Git
- **Rationale**: Transparent, auditable, reviewable, collaborative
- **Alternatives**: Database (opaque), JSON files (no versioning)

### Template Engine: Jinja2
- **Rationale**: Industry standard, powerful, well-documented
- **Alternatives**: Mustache (too simple), custom (NIH syndrome)

### Validation: JSON Schema + Custom Scripts
- **Rationale**: Flexible, extensible, supports both structure and semantics
- **Alternatives**: Only custom scripts (inconsistent), only schemas (limited)

### Testing: pytest + pytest-mock
- **Rationale**: De facto standard, excellent plugin ecosystem
- **Alternatives**: unittest (verbose), nose (unmaintained)

---

## Open Questions

1. **Job Versioning**: How do we handle breaking changes in job definitions?
   - Proposal: Semantic versioning + migration scripts

2. **Concurrent Jobs**: Should users be able to run multiple jobs simultaneously?
   - Proposal: Yes, using separate Git branches

3. **Job Composition**: Can jobs include other jobs as steps?
   - Proposal: Phase 2 feature - support nested jobs

4. **Private Jobs**: How do we support proprietary job definitions?
   - Proposal: Support private Git repos + local job directories

5. **AI Agent Abstraction**: Should we abstract AI platforms behind a common interface?
   - Proposal: No - embrace platform-specific strengths via custom templates

---

## Success Metrics

1. **Usability**: User can define and execute a new job type in <30 minutes
2. **Reliability**: 99%+ of steps execute successfully on first try (with valid inputs)
3. **Performance**: Job import completes in <10 seconds
4. **Extensibility**: New AI platforms can be added in <2 days
5. **Quality**: 90%+ test coverage, zero critical bugs in production
6. **Adoption**: 10+ community-contributed job definitions within 3 months

---

## References

- [Spec-Kit Repository](https://github.com/github/spec-kit)
- [Spec-Driven Development Methodology](https://github.com/github/spec-kit/blob/main/spec-driven.md)
- [Claude Code Documentation](https://claude.com/claude-code)
- [Git Workflows](https://www.atlassian.com/git/tutorials/comparing-workflows)
- [JSON Schema](https://json-schema.org/)
- [Jinja2 Documentation](https://jinja.palletsprojects.com/)
