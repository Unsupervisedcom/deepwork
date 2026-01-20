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
│       │   ├── main.py         # CLI entry point
│       │   ├── install.py      # Install command
│       │   └── sync.py         # Sync command
│       ├── core/
│       │   ├── adapters.py     # Agent adapters for AI platforms
│       │   ├── detector.py     # AI platform detection
│       │   ├── generator.py    # Command file generation
│       │   ├── parser.py       # Job definition parsing
│       │   ├── doc_spec_parser.py   # Document Type Definition parsing
│       │   ├── rules_parser.py     # Rule definition parsing
│       │   ├── pattern_matcher.py  # Variable pattern matching for rules
│       │   ├── rules_queue.py      # Rule state queue system
│       │   ├── command_executor.py # Command action execution
│       │   └── hooks_syncer.py     # Hook syncing to platforms
│       ├── hooks/              # Hook system and cross-platform wrappers
│       │   ├── __init__.py
│       │   ├── wrapper.py           # Cross-platform input/output normalization
│       │   ├── claude_hook.sh       # Shell wrapper for Claude Code
│       │   ├── gemini_hook.sh       # Shell wrapper for Gemini CLI
│       │   └── rules_check.py       # Cross-platform rule evaluation hook
│       ├── templates/          # Skill templates for each platform
│       │   ├── claude/
│       │   │   └── skill-job-step.md.jinja
│       │   ├── gemini/
│       │   └── copilot/
│       ├── standard_jobs/      # Built-in job definitions
│       │   ├── deepwork_jobs/
│       │   │   ├── job.yml
│       │   │   ├── steps/
│       │   │   └── templates/
│       │   │       ├── doc_spec.md.template
│       │   │       └── doc_spec.md.example
│       │   └── deepwork_rules/   # Rule management job
│       │       ├── job.yml
│       │       ├── steps/
│       │       │   └── define.md
│       │       └── hooks/         # Hook scripts
│       │           ├── global_hooks.yml
│       │           ├── user_prompt_submit.sh
│       │           └── capture_prompt_work_tree.sh
│       ├── schemas/            # Definition schemas
│       │   ├── job_schema.py
│       │   ├── doc_spec_schema.py   # Doc spec schema definition
│       │   └── rules_schema.py
│       └── utils/
│           ├── fs.py
│           ├── git.py
│           ├── validation.py
│           └── yaml_utils.py
├── tests/                      # DeepWork tool tests
├── doc/                        # Documentation
├── pyproject.toml
└── readme.md
```

## DeepWork CLI Components

### 1. Installation Command (`install.py`)

The primary installation command. When user executes `deepwork install --claude`:

**Responsibilities**:
1. Detect if current directory is a Git repository
2. Detect if specified AI platform is available (check for `.claude/`, `.gemini/`, etc.)
3. Create `.deepwork/` directory structure in the project
4. Inject standard job definitions (deepwork_jobs)
5. Update or create configuration file
6. Run sync to generate commands for all platforms

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

    # Inject core job definitions
    inject_deepwork_jobs(".deepwork/jobs/")

    # Create rules directory with example templates (if not exists)
    if not exists(".deepwork/rules/"):
        create_directory(".deepwork/rules/")
        copy_example_rules(".deepwork/rules/")

    # Update config (supports multiple platforms)
    config = load_yaml(".deepwork/config.yml") or {}
    config["version"] = "1.0.0"
    config["platforms"] = config.get("platforms", [])

    if platform not in config["platforms"]:
        config["platforms"].append(platform)

    write_yaml(".deepwork/config.yml", config)

    # Run sync to generate skills
    sync_skills()

    print(f"✓ DeepWork installed for {platform}")
    print(f"  Run /deepwork_jobs.define to create your first job")
```

### 2. Agent Adapters (`adapters.py`)

Defines the modular adapter architecture for AI platforms. Each adapter encapsulates platform-specific configuration and behavior.

**Adapter Architecture**:
```python
class SkillLifecycleHook(str, Enum):
    """Generic lifecycle hook events supported by DeepWork."""
    AFTER_AGENT = "after_agent"    # After agent finishes (quality validation)
    BEFORE_TOOL = "before_tool"    # Before tool execution
    BEFORE_PROMPT = "before_prompt" # When user submits a prompt

class AgentAdapter(ABC):
    """Base class for AI agent platform adapters."""

    # Auto-registration via __init_subclass__
    _registry: ClassVar[dict[str, type[AgentAdapter]]] = {}

    # Platform configuration (subclasses define as class attributes)
    name: ClassVar[str]           # "claude"
    display_name: ClassVar[str]   # "Claude Code"
    config_dir: ClassVar[str]     # ".claude"
    skills_dir: ClassVar[str] = "skills"

    # Mapping from generic hook names to platform-specific names
    hook_name_mapping: ClassVar[dict[SkillLifecycleHook, str]] = {}

    def detect(self, project_root: Path) -> bool:
        """Check if this platform is available in the project."""

    def get_platform_hook_name(self, hook: SkillLifecycleHook) -> str | None:
        """Get platform-specific event name for a generic hook."""

    @abstractmethod
    def sync_hooks(self, project_path: Path, hooks: dict) -> int:
        """Sync hooks to platform settings."""

class ClaudeAdapter(AgentAdapter):
    name = "claude"
    display_name = "Claude Code"
    config_dir = ".claude"

    # Claude Code uses PascalCase event names
    hook_name_mapping = {
        SkillLifecycleHook.AFTER_AGENT: "Stop",
        SkillLifecycleHook.BEFORE_TOOL: "PreToolUse",
        SkillLifecycleHook.BEFORE_PROMPT: "UserPromptSubmit",
    }
```

### 3. Platform Detector (`detector.py`)

Uses adapters to identify which AI platforms are available in the project.

**Detection Logic**:
```python
class PlatformDetector:
    def detect_platform(self, platform_name: str) -> AgentAdapter | None:
        """Check if a specific platform is available."""
        adapter_class = AgentAdapter.get(platform_name)
        adapter = adapter_class(self.project_root)
        if adapter.detect():
            return adapter
        return None

    def detect_all_platforms(self) -> list[AgentAdapter]:
        """Detect all available platforms."""
        return [
            adapter_class(self.project_root)
            for adapter_class in AgentAdapter.get_all().values()
            if adapter_class(self.project_root).detect()
        ]
```

### 4. Skill Generator (`generator.py`)

Generates AI-platform-specific skill files from job definitions.

This component is called by the `sync` command to regenerate all skills:
1. Reads the job definition from `.deepwork/jobs/[job-name]/job.yml`
2. Loads platform-specific templates
3. Generates skill files for each step in the job
4. Writes skills to the AI platform's skills directory

**Example Generation Flow**:
```python
class SkillGenerator:
    def generate_all_skills(self, job: JobDefinition,
                            platform: PlatformConfig,
                            output_dir: Path) -> list[Path]:
        """Generate skill files for all steps in a job."""
        skill_paths = []

        for step_index, step in enumerate(job.steps):
            # Load step instructions
            instructions = read_file(job.job_dir / step.instructions_file)

            # Build template context
            context = {
                "job_name": job.name,
                "step_id": step.id,
                "step_name": step.name,
                "step_number": step_index + 1,
                "total_steps": len(job.steps),
                "instructions_content": instructions,
                "user_inputs": [inp for inp in step.inputs if inp.is_user_input()],
                "file_inputs": [inp for inp in step.inputs if inp.is_file_input()],
                "outputs": step.outputs,
                "dependencies": step.dependencies,
                "exposed": step.exposed,
            }

            # Render template
            template = env.get_template("skill-job-step.md.jinja")
            rendered = template.render(**context)

            # Write to platform's skills directory
            skill_path = output_dir / platform.config_dir / platform.skills_dir / f"{job.name}.{step.id}.md"
            write_file(skill_path, rendered)
            skill_paths.append(skill_path)

        return skill_paths
```

---

# Part 2: Target Project Architecture

This section describes what a project looks like AFTER `deepwork install --claude` has been run.

## Target Project Structure

```
my-project/                     # User's project (target)
├── .git/
├── .claude/                    # Claude Code directory
│   ├── settings.json           # Includes installed hooks
│   └── skills/                 # Skill files
│       ├── deepwork_jobs.define.md         # Core DeepWork skills
│       ├── deepwork_jobs.implement.md
│       ├── deepwork_jobs.refine.md
│       ├── deepwork_rules.define.md        # Rule management
│       ├── competitive_research.identify_competitors.md
│       └── ...
├── .deepwork/                  # DeepWork configuration
│   ├── config.yml              # Platform config
│   ├── .gitignore              # Ignores tmp/ directory
│   ├── doc_specs/                   # Document Type Definitions
│   │   └── monthly_aws_report.md
│   ├── rules/                  # Rule definitions (v2 format)
│   │   ├── source-test-pairing.md
│   │   ├── format-python.md
│   │   └── api-docs.md
│   ├── tmp/                    # Temporary state (gitignored)
│   │   └── rules/queue/        # Rule evaluation queue
│   └── jobs/                   # Job definitions
│       ├── deepwork_jobs/      # Core job for managing jobs
│       │   ├── job.yml
│       │   └── steps/
│       ├── deepwork_rules/     # Rule management job
│       │   ├── job.yml
│       │   ├── steps/
│       │   │   └── define.md
│       │   └── hooks/          # Hook scripts (installed from standard_jobs)
│       │       ├── global_hooks.yml
│       │       ├── user_prompt_submit.sh
│       │       └── capture_prompt_work_tree.sh
│       ├── competitive_research/
│       │   ├── job.yml         # Job metadata
│       │   └── steps/
│       └── ad_campaign/
│           └── ...
├── (rest of user's project files)
└── README.md
```

**Note**: Work outputs are created directly in the project on dedicated Git branches (e.g., `deepwork/competitive_research-acme-2026-01-11`). The branch naming convention is `deepwork/[job_name]-[instance]-[date]`.

## Configuration Files

### `.deepwork/config.yml`

```yaml
version: 1.0.0
platforms:
  - claude
```

**Note**: The config supports multiple platforms. You can add additional platforms by running `deepwork install --platform gemini` etc.

### Job Definition Example

`.deepwork/jobs/competitive_research/job.yml`:

```yaml
name: competitive_research
version: "1.0.0"
summary: "Systematic competitive analysis workflow"
description: |
  A comprehensive workflow for analyzing competitors in your market segment. This job
  helps product teams understand the competitive landscape by systematically identifying
  competitors, researching their offerings, creating comparison matrices, and developing
  strategic positioning recommendations.

  The workflow produces:
  - A vetted list of key competitors
  - Detailed research notes on each competitor (primary and secondary sources)
  - A comparison matrix highlighting key differentiators
  - Strategic positioning recommendations

  Designed for product teams conducting quarterly competitive analysis.

changelog:
  - version: "1.0.0"
    changes: "Initial job creation"

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

### Lifecycle Hooks in Job Definitions

Steps can define lifecycle hooks that trigger at specific points during execution. Hooks are defined using generic event names that are mapped to platform-specific names by adapters:

```yaml
steps:
  - id: build_report
    name: "Build Report"
    description: "Generate the final report"
    instructions_file: steps/build_report.md
    outputs:
      - report.md
    hooks:
      after_agent:  # Triggers after agent finishes (Claude: "Stop")
        - prompt: |
            Verify the report includes all required sections:
            - Executive summary
            - Data analysis
            - Recommendations
        - script: hooks/validate_report.sh
      before_tool:  # Triggers before tool use (Claude: "PreToolUse")
        - prompt: "Confirm tool execution is appropriate"
```

**Supported Lifecycle Events**:
- `after_agent` - Triggered after the agent finishes responding (quality validation)
- `before_tool` - Triggered before the agent uses a tool
- `before_prompt` - Triggered when user submits a new prompt

**Hook Action Types**:
- `prompt` - Inline prompt text
- `prompt_file` - Path to a file containing the prompt
- `script` - Path to a shell script

**Note**: The deprecated `stop_hooks` field is still supported for backward compatibility but maps to `hooks.after_agent`.

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

## Generated Command Files

When the job is defined and `sync` is run, DeepWork generates command files. Example for Claude Code:

`.deepwork/jobs/competitive_research` a step called `identify_competitors` will generate a skill file at `.claude/skills/competitive_research.identify_competitors.md`:


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
   User: /deepwork_jobs.define

   Claude: I'll help you define a new job. What type of work do you want to define?

   User: Competitive research

   [Interactive dialog to define all the steps]

   Claude: ✓ Job 'competitive_research' created with 5 steps
          Run /deepwork_jobs.implement to generate skill files
          Then run 'deepwork sync' to install skills

   User: /deepwork_jobs.implement

   Claude: [Generates step instruction files]
          [Runs deepwork sync]
          ✓ Skills installed to .claude/skills/
          Run /competitive_research.identify_competitors to start
   ```

3. **Execute a Job Instance** (each time you need to do the work):
   ```
   # In Claude Code
   User: /competitive_research.identify_competitors

   Claude: Starting competitive research job...
          Created branch: deepwork/competitive_research-acme-2026-01-11

          Please provide:
          - Market segment: ?
          - Product category: ?

   User: Market segment: Enterprise SaaS
         Product category: Project Management

   Claude: [Performs research using web tools, analysis, etc.]
          ✓ Created competitors.md

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

   Claude: [Creates PR from deepwork/competitive_research-acme-2026-01-11 to main]
          PR created: https://github.com/user/project/pull/123
   ```

## How Claude Code Executes Skills

When user types `/competitive_research.identify_competitors`:

1. **Skill Discovery**:
   - Claude Code scans `.claude/skills/` directory
   - Finds `competitive_research.identify_competitors.md`
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

On a work branch like `deepwork/competitive_research-acme-2026-01-11`, outputs are created in the project:

```
(project root on work branch)
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

Each command instructs Claude to:
- Read specific input files from previous steps
- Write specific output files for this step
- All on the same work branch

### 2. Skill Instructions

Each skill file explicitly states its dependencies:

```markdown
### Prerequisites
This step requires outputs from:
- Step 1 (identify_competitors): competitors.md
- Step 2 (primary_research): primary_research.md

### Your Task
Conduct web research on secondary sources for each competitor identified in competitors.md.
```

### 3. Git History

When working on similar jobs:
- User: "Do competitive research for Acme Corp, similar to our Widget Corp analysis"
- Claude can read old existing branches like `deepwork/competitive_research-widget-corp-2024-01-05` from git history
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
deepwork/competitive_research-acme-2026-01-11      # Name-based with date
deepwork/ad_campaign-q1-2026-01-11                 # Quarter-based with date
deepwork/monthly_report-2026-01-11                 # Date-based
```

**Branch Naming Convention**:
```
deepwork/[job_name]-[instance-identifier]-[date]
```

Where `instance-identifier` can be:
- User-specified: `acme`, `q1`, etc.
- Auto-generated from timestamp if not specified
- Logical: "ford" when doing competitive research on Ford Motor Company

**Date format**: `YYYY-MM-DD`

### Skill Behavior

Skills should:
1. Check if we're already on a branch for this job
2. If not, ask user for instance name or auto-generate from timestamp
3. Create branch: `git checkout -b deepwork/[job_name]-[instance]-[date]`
4. Perform the work on that branch

### Completion and Merge

When all steps are done, remind the user they should:
1. Review all outputs
2. Commit the work
3. Create PR to main branch
4. After merge, the work products are in the repository
5. Future job instances can reference this work for context/templates

---

## Job Definition and Command Generation

### Standard Job: `deepwork_jobs`

DeepWork includes a built-in job called `deepwork_jobs` with three commands for managing jobs:

1. **`/deepwork_jobs.define`** - Interactive job definition wizard
2. **`/deepwork_jobs.implement`** - Generates step instruction files from job.yml
3. **`/deepwork_jobs.refine`** - Modifies existing job definitions

These commands are installed automatically when you run `deepwork install`.

### The `/deepwork_jobs.define` Command

When a user runs `/deepwork_jobs.define` in Claude Code:

**What Happens**:
1. Claude engages in interactive dialog to gather:
   - Job name
   - Job description
   - List of steps (name, description, inputs, outputs)
   - Dependencies between steps

2. Claude creates the job definition file:
   ```
   .deepwork/jobs/[job-name]/
   └── job.yml                    # Job metadata only
   ```

3. User then runs `/deepwork_jobs.implement` to:
   - Generate step instruction files (steps/*.md)
   - Run `deepwork sync` to generate command files
   - Install commands to `.claude/commands/`

4. The workflow is now:
   ```
   /deepwork_jobs.define     → Creates job.yml
   /deepwork_jobs.implement  → Creates steps/*.md and syncs commands
   ```

5. The `/deepwork_jobs.define` command contains:
   - The job definition YAML schema
   - Interactive question flow
   - Job.yml creation logic

**Skill File Structure**:

The actual skill file `.claude/skills/deepwork_jobs.define.md` contains:

```markdown
---
description: Create the job.yml specification file by understanding workflow requirements
---

# deepwork_jobs.define

**Step 1 of 3** in the **deepwork_jobs** workflow

## Instructions

[Detailed instructions for Claude on how to run the interactive wizard...]

## Job Definition Schema

When creating job.yml, use this structure:
[YAML schema embedded here...]
```

### The `/deepwork_jobs.implement` Command

Generates step instruction files from job.yml and syncs skills:

```
User: /deepwork_jobs.implement

Claude: Reading job definition from .deepwork/jobs/competitive_research/job.yml...
        Generating step instruction files...
        ✓ Created steps/identify_competitors.md
        ✓ Created steps/primary_research.md
        ✓ Created steps/secondary_research.md
        ✓ Created steps/comparative_report.md
        ✓ Created steps/positioning.md

        Running deepwork sync...
        ✓ Generated 5 skill files in .claude/skills/

        New skills available:
        - /competitive_research.identify_competitors
        - /competitive_research.primary_research
        - /competitive_research.secondary_research
        - /competitive_research.comparative_report
        - /competitive_research.positioning
```

### The `/deepwork_jobs.refine` Command

Allows updating existing job definitions:

```
User: /deepwork_jobs.refine

Claude: Which job would you like to refine?
        Available jobs:
        - competitive_research
        - deepwork_jobs

User: competitive_research

Claude: Loading competitive_research job definition...
        What would you like to update?
        1. Add a new step
        2. Modify existing step
        3. Remove a step
        4. Update metadata

User: Add a new step between primary_research and secondary_research

Claude: [Interactive dialog...]
        ✓ Added step 'social_media_analysis'
        ✓ Updated dependencies in job.yml
        ✓ Updated changelog with version 1.1.0
        ✓ Please run /deepwork_jobs.implement to generate the new step file
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
Use unit tests for small pieces of functionality that don't depend on external systems.

#### 2. Integration Tests
Use integration tests for larger pieces of functionality that depend on external systems.

#### 3. End-to-End Tests
Use end-to-end tests to verify the entire workflow from start to finish.

#### 4. Mock AI Agents
Use mock AI agents to simulate AI agent responses.

#### 5. Fixtures
Use fixtures to provide test data.

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

Github Actions are used for all CI/CD tasks.

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

## Rules

Rules are automated enforcement mechanisms that trigger based on file changes during an AI agent session. They help ensure that:
- Documentation stays in sync with code changes
- Security reviews happen when sensitive code is modified
- Team guidelines are followed automatically
- File correspondences are maintained (e.g., source/test pairing)

### Rules System v2 (Frontmatter Markdown)

Rules are defined as individual markdown files in `.deepwork/rules/`:

```
.deepwork/rules/
├── source-test-pairing.md
├── format-python.md
└── api-docs.md
```

Each rule file uses YAML frontmatter with a markdown body for instructions:

```markdown
---
name: Source/Test Pairing
set:
  - src/{path}.py
  - tests/{path}_test.py
compare_to: base
---
When source files change, corresponding test files should also change.
Please create or update tests for the modified source files.
```

### Detection Modes

Rules support three detection modes:

**1. Trigger/Safety (default)** - Fire when trigger matches but safety doesn't:
```yaml
---
name: Update install guide
trigger: "app/config/**/*"
safety: "docs/install_guide.md"
compare_to: base
---
```

**2. Set (bidirectional)** - Enforce file correspondence in both directions:
```yaml
---
name: Source/Test Pairing
set:
  - src/{path}.py
  - tests/{path}_test.py
compare_to: base
---
```
Uses variable patterns like `{path}` (multi-segment) and `{name}` (single-segment) for matching.

**3. Pair (directional)** - Trigger requires corresponding files, but not vice versa:
```yaml
---
name: API Documentation
pair:
  trigger: src/api/{name}.py
  expects: docs/api/{name}.md
compare_to: base
---
```

### Action Types

**1. Prompt (default)** - Show instructions to the agent:
```yaml
---
name: Security Review
trigger: "src/auth/**/*"
compare_to: base
---
Please check for hardcoded credentials and validate input.
```

**2. Command** - Run an idempotent command:
```yaml
---
name: Format Python
trigger: "**/*.py"
action:
  command: "ruff format {file}"
  run_for: each_match  # or "all_matches"
compare_to: prompt
---
```

### Rule Evaluation Flow

1. **Session Start**: When a Claude Code session begins, the baseline git state is captured
2. **Agent Works**: The AI agent performs tasks, potentially modifying files
3. **Session Stop**: When the agent finishes (after_agent event):
   - Changed files are detected based on `compare_to` setting (base, default_tip, or prompt)
   - Each rule is evaluated based on its detection mode
   - Queue entries are created in `.deepwork/tmp/rules/queue/` for deduplication
   - For command actions: commands are executed, results tracked
   - For prompt actions: if rule fires and not already promised, agent is prompted
4. **Promise Tags**: Agents can mark rules as addressed by including `<promise>✓ Rule Name</promise>` in their response

### Queue System

Rule state is tracked in `.deepwork/tmp/rules/queue/` with files named `{hash}.{status}.json`:
- `queued` - Detected, awaiting evaluation
- `passed` - Rule satisfied (promise found or command succeeded)
- `failed` - Rule not satisfied
- `skipped` - Safety pattern matched

This prevents re-prompting for the same rule violation within a session.

### Hook Integration

The v2 rules system uses the cross-platform hook wrapper:

```
src/deepwork/hooks/
├── wrapper.py           # Cross-platform input/output normalization
├── rules_check.py       # Rule evaluation hook (v2)
├── claude_hook.sh       # Claude Code shell wrapper
└── gemini_hook.sh       # Gemini CLI shell wrapper
```

Hooks are called via the shell wrappers:
```bash
claude_hook.sh deepwork.hooks.rules_check
```

The hooks are installed to `.claude/settings.json` during `deepwork sync`:

```json
{
  "hooks": {
    "Stop": [
      {"matcher": "", "hooks": [{"type": "command", "command": "python -m deepwork.hooks.rules_check"}]}
    ]
  }
}
```

### Cross-Platform Hook Wrapper System

The `hooks/` module provides a wrapper system that allows writing hooks once in Python and running them on multiple platforms. This normalizes the differences between Claude Code and Gemini CLI hook systems.

**Architecture:**
```
┌─────────────────┐     ┌─────────────────┐
│  Claude Code    │     │   Gemini CLI    │
│  (Stop event)   │     │ (AfterAgent)    │
└────────┬────────┘     └────────┬────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│ claude_hook.sh  │     │ gemini_hook.sh  │
│ (shell wrapper) │     │ (shell wrapper) │
└────────┬────────┘     └────────┬────────┘
         │                       │
         └───────────┬───────────┘
                     ▼
           ┌─────────────────┐
           │   wrapper.py    │
           │ (normalization) │
           └────────┬────────┘
                    ▼
           ┌─────────────────┐
           │  Python Hook    │
           │ (common logic)  │
           └─────────────────┘
```

**Key normalizations:**
- Event names: `Stop` ↔ `AfterAgent`, `PreToolUse` ↔ `BeforeTool`, `UserPromptSubmit` ↔ `BeforeAgent`
- Tool names: `Write` ↔ `write_file`, `Bash` ↔ `shell`, `Read` ↔ `read_file`
- Decision values: `block` → `deny` for Gemini CLI
- Environment variables: `CLAUDE_PROJECT_DIR` ↔ `GEMINI_PROJECT_DIR`

**Usage:**
```python
from deepwork.hooks.wrapper import HookInput, HookOutput, run_hook, Platform

def my_hook(input: HookInput) -> HookOutput:
    if input.event == NormalizedEvent.AFTER_AGENT:
        return HookOutput(decision="block", reason="Complete X first")
    return HookOutput()

# Called via: claude_hook.sh mymodule or gemini_hook.sh mymodule
```

See `doc/platforms/` for detailed platform-specific hook documentation.

---

## Doc Specs (Document Specifications)

Doc specs formalize document specifications for job outputs. They enable consistent document structure and automated quality validation.

### Purpose

Doc specs solve a common problem with AI-generated documents: inconsistent quality and structure. By defining:
- Required quality criteria
- Target audience
- Document structure (via example)

Doc specs ensure that documents produced by job steps meet consistent standards.

### Doc Spec File Format

Doc specs are stored in `.deepwork/doc_specs/[doc_spec_name].md` using frontmatter markdown:

```markdown
---
name: "Monthly AWS Spending Report"
description: "A Markdown summary of AWS spend across accounts"
path_patterns:
  - "finance/aws-reports/*.md"
target_audience: "Finance team and Engineering leadership"
frequency: "Monthly, following AWS invoice arrival"
quality_criteria:
  - name: Visualization
    description: Must include Mermaid.js charts showing spend per service
  - name: Variance Analysis
    description: Must compare current month against previous with percentages
---

# Monthly AWS Spending Report: [Month, Year]

## Executive Summary
[Example content...]
```

### Using Doc Specs in Jobs

Reference doc specs in job.yml outputs:

```yaml
outputs:
  - file: reports/monthly_spending.md
    document_type: .deepwork/doc_specs/monthly_aws_report.md
```

### Generated Skills

When `deepwork sync` runs, skills with doc spec-referenced outputs include:
- Document name and description
- Target audience
- All quality criteria with descriptions
- Example document structure (collapsible)

### Doc Spec Schema

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Human-readable document name |
| `description` | Yes | Purpose of the document |
| `quality_criteria` | Yes | Array of `{name, description}` quality requirements |
| `path_patterns` | No | Where documents should be stored |
| `target_audience` | No | Who reads the document |
| `frequency` | No | How often produced |

### Workflow Integration

The `/deepwork_jobs.define` command:
1. Detects document-oriented workflows (keywords: "report", "summary", "monthly")
2. Guides users through doc spec creation
3. Links doc specs to job outputs

The `/deepwork_jobs.learn` command:
1. Identifies doc spec-related learnings (quality criteria issues, structure changes)
2. Updates doc spec files with improvements

See `doc/doc-specs.md` for complete documentation.

---

### Rule Schema

Rules are validated against a JSON Schema:

```yaml
- name: string          # Required: Friendly name for the rule
  trigger: string|array # Required: Glob pattern(s) for triggering files
  safety: string|array  # Optional: Glob pattern(s) for safety files
  instructions: string  # Required (unless instructions_file): What to do
  instructions_file: string  # Alternative: Path to instructions file
```

### Defining Rules

Use the `/deepwork_rules.define` command to interactively create rules:

```
User: /deepwork_rules.define

Claude: I'll help you define a new rule. What guideline or constraint
        should this rule enforce?

User: When API code changes, the API documentation should be updated

Claude: Got it. Let me ask a few questions...
        [Interactive dialog to define trigger, safety, and instructions]

Claude: Created rule "API documentation update" in .deepwork/rules/api-documentation.md
```

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

