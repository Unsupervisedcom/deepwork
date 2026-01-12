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
│       │   ├── policy_parser.py # Policy definition parsing
│       │   └── hooks_syncer.py # Hook syncing to platforms
│       ├── hooks/              # Hook evaluation modules
│       │   ├── __init__.py
│       │   └── evaluate_policies.py  # Policy evaluation CLI
│       ├── templates/          # Command templates for each platform
│       │   ├── claude/
│       │   │   └── command-job-step.md.jinja
│       │   ├── gemini/
│       │   └── copilot/
│       ├── standard_jobs/      # Built-in job definitions
│       │   ├── deepwork_jobs/
│       │   │   ├── job.yml
│       │   │   └── steps/
│       │   └── deepwork_policy/   # Policy management job
│       │       ├── job.yml
│       │       ├── steps/
│       │       │   └── define.md
│       │       └── hooks/         # Hook scripts
│       │           ├── global_hooks.yml
│       │           ├── user_prompt_submit.sh
│       │           ├── capture_work_tree.sh
│       │           ├── get_changed_files.sh
│       │           └── policy_stop_hook.sh
│       ├── schemas/            # Definition schemas
│       │   ├── job_schema.py
│       │   └── policy_schema.py
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

    # Update config (supports multiple platforms)
    config = load_yaml(".deepwork/config.yml") or {}
    config["version"] = "1.0.0"
    config["platforms"] = config.get("platforms", [])

    if platform not in config["platforms"]:
        config["platforms"].append(platform)

    write_yaml(".deepwork/config.yml", config)

    # Run sync to generate commands
    sync_commands()

    print(f"✓ DeepWork installed for {platform}")
    print(f"  Run /deepwork_jobs.define to create your first job")
```

### 2. Agent Adapters (`adapters.py`)

Defines the modular adapter architecture for AI platforms. Each adapter encapsulates platform-specific configuration and behavior.

**Adapter Architecture**:
```python
class CommandLifecycleHook(str, Enum):
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
    commands_dir: ClassVar[str] = "commands"

    # Mapping from generic hook names to platform-specific names
    hook_name_mapping: ClassVar[dict[CommandLifecycleHook, str]] = {}

    def detect(self, project_root: Path) -> bool:
        """Check if this platform is available in the project."""

    def get_platform_hook_name(self, hook: CommandLifecycleHook) -> str | None:
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
        CommandLifecycleHook.AFTER_AGENT: "Stop",
        CommandLifecycleHook.BEFORE_TOOL: "PreToolUse",
        CommandLifecycleHook.BEFORE_PROMPT: "UserPromptSubmit",
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

### 4. Command Generator (`generator.py`)

Generates AI-platform-specific command files from job definitions.

This component is called by the `sync` command to regenerate all commands:
1. Reads the job definition from `.deepwork/jobs/[job-name]/job.yml`
2. Loads platform-specific templates
3. Generates command files for each step in the job
4. Writes commands to the AI platform's commands directory

**Example Generation Flow**:
```python
class CommandGenerator:
    def generate_all_commands(self, job: JobDefinition,
                            platform: PlatformConfig,
                            output_dir: Path) -> list[Path]:
        """Generate command files for all steps in a job."""
        command_paths = []

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
            }

            # Render template
            template = env.get_template("command-job-step.md.jinja")
            rendered = template.render(**context)

            # Write to platform's commands directory
            command_path = output_dir / platform.config_dir / platform.commands_dir / f"{job.name}.{step.id}.md"
            write_file(command_path, rendered)
            command_paths.append(command_path)

        return command_paths
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
│   └── commands/               # Command files
│       ├── deepwork_jobs.define.md         # Core DeepWork commands
│       ├── deepwork_jobs.implement.md
│       ├── deepwork_jobs.refine.md
│       ├── deepwork_policy.define.md       # Policy management
│       ├── competitive_research.identify_competitors.md
│       └── ...
├── .deepwork/                  # DeepWork configuration
│   ├── config.yml              # Platform config
│   ├── .gitignore              # Ignores .last_work_tree
│   └── jobs/                   # Job definitions
│       ├── deepwork_jobs/      # Core job for managing jobs
│       │   ├── job.yml
│       │   └── steps/
│       ├── deepwork_policy/    # Policy management job
│       │   ├── job.yml
│       │   ├── steps/
│       │   │   └── define.md
│       │   └── hooks/          # Hook scripts (installed from standard_jobs)
│       │       ├── global_hooks.yml
│       │       ├── user_prompt_submit.sh
│       │       ├── capture_work_tree.sh
│       │       ├── get_changed_files.sh
│       │       └── policy_stop_hook.sh
│       ├── competitive_research/
│       │   ├── job.yml         # Job metadata
│       │   └── steps/
│       └── ad_campaign/
│           └── ...
├── .deepwork.policy.yml        # Policy definitions (project root)
├── deepwork/                   # Work products (Git branches)
│   ├── competitive_research-acme-2026-01-11/
│   │   └── ...
│   └── ad_campaign-q1-2026-01-11/
│       └── ...
├── (rest of user's project files)
└── README.md
```

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

`.claude/commands/competitive_research.identify_competitors.md`:

```markdown
---
description: Research and identify direct and indirect competitors
---

# competitive_research.identify_competitors

**Step 1 of 5** in the **competitive_research** workflow

**Summary**: Systematic competitive analysis workflow

## Job Overview

[Job description and context...]

## Instructions

You are performing the "Identify Competitors" step of competitive research.

### Prerequisites
This step has no dependencies (it's the first step).

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
2. If not, create a new branch: `deepwork/competitive_research-[instance]-[date]`
3. All outputs should be created in the `deepwork/[branch-name]/` directory

### Output Requirements
Create the following file in the work directory:
- `deepwork/[branch-name]/competitors.md`

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
   User: /deepwork_jobs.define

   Claude: I'll help you define a new job. What type of work do you want to define?

   User: Competitive research

   [Interactive dialog to define all the steps]

   Claude: ✓ Job 'competitive_research' created with 5 steps
          Run /deepwork_jobs.implement to generate command files
          Then run 'deepwork sync' to install commands

   User: /deepwork_jobs.implement

   Claude: [Generates step instruction files]
          [Runs deepwork sync]
          ✓ Commands installed to .claude/commands/
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
          ✓ Created deepwork/competitive_research-acme-2026-01-11/competitors.md

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

## How Claude Code Executes Commands

When user types `/competitive_research.identify_competitors`:

1. **Command Discovery**:
   - Claude Code scans `.claude/commands/` directory
   - Finds `competitive_research.identify_competitors.md`
   - Loads the command definition

2. **Context Loading**:
   - Command file contains embedded instructions
   - References to job definition and step files
   - Claude reads these files to understand the full context

3. **Execution**:
   - Claude follows the instructions in the command
   - Uses its tools (Read, Write, WebSearch, WebFetch, etc.)
   - Creates outputs in the specified format

4. **State Management** (via filesystem):
   - Work branch name encodes the job instance
   - Output files track progress
   - Git provides version control and resumability

5. **No DeepWork Runtime**:
   - DeepWork CLI is NOT running during execution
   - Everything happens through Claude Code's native execution
   - Commands are just markdown instruction files that Claude interprets

## Context Passing Between Steps

Since there's no DeepWork runtime process, context is passed through:

### 1. Filesystem (Primary Mechanism)

```
deepwork/competitive_research-acme-2026-01-11/
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
- All within the same work directory

### 2. Command Instructions

Each command file explicitly states its dependencies:

```markdown
### Prerequisites
This step requires outputs from:
- Step 1 (identify_competitors): competitors.md
- Step 2 (primary_research): primary_research.md

### Your Task
1. Read `deepwork/[branch]/competitors.md`
2. Read `deepwork/[branch]/primary_research.md`
3. [Perform analysis]
4. Write `deepwork/[branch]/secondary_research.md`
```

### 3. Git History

When working on similar jobs:
- User: "Do competitive research for Acme Corp, similar to our Widget Corp analysis"
- Claude can read `deepwork/competitive_research-widget-corp-2026-01-05/` from git history
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

### Command Behavior

Commands should:
1. Check if we're already on a work branch for this job
2. If not, ask user for instance name or auto-generate from timestamp
3. Create branch: `git checkout -b deepwork/[job_name]-[instance]-[date]`
4. Create work directory: `mkdir -p deepwork/[job_name]-[instance]-[date]`
5. Perform work in that directory

### Completion and Merge

When all steps are done:
1. User reviews all outputs in `work/[branch-name]/`
2. Commits the work
3. Creates PR to main branch
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

**Command File Structure**:

The actual command file `.claude/commands/deepwork_jobs.define.md` contains:

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

Generates step instruction files from job.yml and syncs commands:

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
        ✓ Generated 5 command files in .claude/commands/

        New commands available:
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

## Policies

Policies are automated enforcement rules that trigger based on file changes during an AI agent session. They help ensure that:
- Documentation stays in sync with code changes
- Security reviews happen when sensitive code is modified
- Team guidelines are followed automatically

### Policy Configuration File

Policies are defined in `.deepwork.policy.yml` at the project root:

```yaml
- name: "Update install guide on config changes"
  trigger: "app/config/**/*"
  safety: "docs/install_guide.md"
  instructions: |
    Configuration files have been modified. Please review docs/install_guide.md
    and update it if any installation instructions need to change.

- name: "Security review for auth changes"
  trigger:
    - "src/auth/**/*"
    - "src/security/**/*"
  safety:
    - "SECURITY.md"
    - "docs/security_audit.md"
  instructions: |
    Authentication or security code has been changed. Please:
    1. Check for hardcoded credentials
    2. Verify input validation
    3. Review access control logic
```

### Policy Evaluation Flow

1. **Session Start**: When a Claude Code session begins, the baseline git state is captured
2. **Agent Works**: The AI agent performs tasks, potentially modifying files
3. **Session Stop**: When the agent finishes:
   - Changed files are detected by comparing against the baseline
   - Each policy is evaluated:
     - If any changed file matches a `trigger` pattern AND
     - No changed file matches a `safety` pattern AND
     - The agent hasn't marked it with a `<promise>` tag
     - → The policy fires
   - If policies fire, Claude is prompted to address them
4. **Promise Tags**: Agents can mark policies as addressed by including `<promise policy="Policy Name">addressed</promise>` in their response

### Hook Integration

Policies are implemented using Claude Code's hooks system. The `deepwork_policy` standard job includes:

```
.deepwork/jobs/deepwork_policy/hooks/
├── global_hooks.yml           # Maps lifecycle events to scripts
├── user_prompt_submit.sh      # Captures baseline on first prompt
├── capture_work_tree.sh       # Creates git state snapshot
├── get_changed_files.sh       # Computes changed files
└── policy_stop_hook.sh        # Evaluates policies on stop
```

The hooks are installed to `.claude/settings.json` during `deepwork sync`:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {"matcher": "", "hooks": [{"type": "command", "command": ".deepwork/jobs/deepwork_policy/hooks/user_prompt_submit.sh"}]}
    ],
    "Stop": [
      {"matcher": "", "hooks": [{"type": "command", "command": ".deepwork/jobs/deepwork_policy/hooks/policy_stop_hook.sh"}]}
    ]
  }
}
```

### Policy Schema

Policies are validated against a JSON Schema:

```yaml
- name: string          # Required: Friendly name for the policy
  trigger: string|array # Required: Glob pattern(s) for triggering files
  safety: string|array  # Optional: Glob pattern(s) for safety files
  instructions: string  # Required (unless instructions_file): What to do
  instructions_file: string  # Alternative: Path to instructions file
```

### Defining Policies

Use the `/deepwork_policy.define` command to interactively create policies:

```
User: /deepwork_policy.define

Claude: I'll help you define a new policy. What guideline or constraint
        should this policy enforce?

User: When API code changes, the API documentation should be updated

Claude: Got it. Let me ask a few questions...
        [Interactive dialog to define trigger, safety, and instructions]

Claude: ✓ Created policy "API documentation update" in .deepwork.policy.yml
```

---

## Implementation Status

**Completed**: Phases 1 & 2 are complete. The core runtime, CLI, installation, and command generation systems are fully functional.

### Current Focus: Phase 5 - Job Ecosystem
- ✅ Standard job `deepwork_jobs` with define, implement, refine commands
- 📋 Reference job library (competitive research, ad campaigns, etc.)
- 📋 Job sharing via Git repositories

### Future Work

**Phase 3: Runtime Engine** (Optional enhancements)
- Step execution tracking and monitoring
- Output validation system
- Advanced state management

**Phase 4: Multi-Platform Support**
- Gemini command generation
- GitHub Copilot integration
- Multi-platform testing

**Phase 6: Polish and Release**
- Performance optimization
- Enhanced error handling
- Comprehensive user documentation
- Tutorial content
- Beta and public release

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
