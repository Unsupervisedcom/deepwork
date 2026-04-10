# DeepWork Architecture

## Overview

DeepWork is a framework for enabling AI agents to perform complex, multi-step work tasks across any domain. Inspired by spec-kit's approach to software development, DeepWork generalizes the pattern to support any job type—from competitive research to ad campaign design to monthly reporting.

**Key Insight**: DeepWork is delivered as a **plugin** for AI agent CLIs (Claude Code, Gemini CLI, etc.). The plugin provides a skill, MCP server configuration, and hooks. The MCP server (`deepwork serve`) is the core runtime. The `deepwork setup` command configures platform settings automatically.

## Core Design Principles

1. **Job-Agnostic**: The framework supports any multi-step workflow, not just software development
2. **Git-Native**: All work products are versioned in Git for collaboration, review, and context accumulation
3. **Step-Driven**: Jobs are decomposed into reviewable steps with clear inputs and outputs
4. **Plugin-Based**: Delivered as platform plugins (Claude Code plugin, Gemini extension)
5. **AI-Neutral**: Support for multiple AI platforms (Claude Code, Gemini, Copilot, etc.)
6. **Stateless Execution**: All state is stored in filesystem artifacts, enabling resumability and transparency
7. **MCP-Powered**: The MCP server is the core runtime — `deepwork setup` handles platform configuration

## Architecture Overview

This document is organized into four major sections:

1. **[DeepWork Tool Architecture](#part-1-deepwork-tool-architecture)** - The DeepWork repository/codebase itself and how it works
2. **[Target Project Architecture](#part-2-target-project-architecture)** - What a project looks like after DeepWork is installed
3. **[Runtime Execution Model](#part-3-runtime-execution-model)** - How AI agents execute jobs using the installed skills
4. **[MCP Server Architecture](#part-4-mcp-server-architecture)** - The MCP server for checkpoint-based workflow execution

---

# Part 1: DeepWork Tool Architecture

This section describes the DeepWork repository itself - the tool that users install globally and use to set up projects.

## DeepWork Repository Structure

```
deepwork/                       # DeepWork tool repository
├── src/
│   └── deepwork/
│       ├── cli/
│       │   ├── main.py         # CLI entry point
│       │   ├── serve.py        # MCP server command
│       │   ├── hook.py         # Hook runner command
│       │   ├── jobs.py         # Job inspection commands (get-stack)
│       │   ├── review.py       # Review command (CLI entry for reviews)
│       │   ├── setup.py        # Platform setup command
│       │   └── install.py      # Deprecated install/sync (back-compat)
│       ├── core/
│       │   └── doc_spec_parser.py   # Doc spec parsing
│       ├── jobs/               # Job discovery, parsing, and MCP server
│       │   ├── discovery.py    # Job discovery
│       │   ├── issues.py       # Job definition issue detection
│       │   ├── parser.py       # Job definition parsing
│       │   ├── schema.py       # Job schema validation
│       │   ├── job.schema.json # JSON schema for job definitions
│       │   └── mcp/            # MCP server module (the core runtime)
│       │       ├── server.py       # FastMCP server definition
│       │       ├── tools.py        # MCP tool implementations
│       │       ├── state.py        # Workflow session state management
│       │       ├── schemas.py      # Pydantic models for I/O
│       │       ├── quality_gate.py # Quality gate via DeepWork Reviews
│       │       ├── roots.py        # MCP root resolver
│       │       └── status.py       # Status file writer for external consumers
│       ├── setup/              # Platform setup helpers
│       │   ├── __init__.py
│       │   └── claude.py       # Claude Code settings configuration
│       ├── hooks/              # Hook system and cross-platform wrappers
│       │   ├── wrapper.py      # Cross-platform input/output normalization
│       │   ├── deepschema_write.py # DeepSchema write-time validation hook
│       │   ├── claude_hook.sh  # Shell wrapper for Claude Code
│       │   └── gemini_hook.sh  # Shell wrapper for Gemini CLI
│       ├── deepschema/         # DeepSchema subsystem
│       │   ├── config.py       # DeepSchema config parsing
│       │   ├── discovery.py    # Find DeepSchema files in project tree
│       │   ├── matcher.py      # Match files against DeepSchema rules
│       │   ├── resolver.py     # Resolve DeepSchema definitions
│       │   ├── review_bridge.py # Generate synthetic review rules from DeepSchemas
│       │   └── schema.py       # DeepSchema data models
│       ├── standard_jobs/      # Built-in job definitions
│       │   ├── deepwork_jobs/
│       │   ├── deepwork_reviews/
│       │   └── deepplan/
│       ├── standard_schemas/   # Built-in DeepSchema definitions
│       ├── review/             # DeepWork Reviews system
│       │   ├── config.py       # .deepreview config parsing + data models
│       │   ├── discovery.py    # Find .deepreview files in project tree
│       │   ├── matcher.py      # Git diff + glob matching + strategy grouping
│       │   ├── instructions.py # Generate review instruction files
│       │   ├── formatter.py    # Format output for Claude Code
│       │   ├── mcp.py          # MCP adapter for review pipeline
│       │   └── schema.py       # JSON schema loader
│       ├── schemas/            # Definition schemas
│       │   ├── deepreview_schema.json
│       │   ├── deepschema_schema.json
│       │   └── doc_spec_schema.py
│       └── utils/
│           ├── fs.py
│           ├── git.py
│           ├── validation.py
│           └── yaml_utils.py
├── platform/                   # Shared platform-agnostic content
│   └── skill-body.md           # Canonical skill body (source of truth)
├── plugins/
│   ├── claude/                 # Claude Code plugin
│   │   ├── .claude-plugin/plugin.json
│   │   ├── README_REVIEWS.md   # Review system documentation
│   │   ├── example_reviews/    # Example review instruction files
│   │   │   ├── prompt_best_practices.md
│   │   │   └── suggest_new_reviews.md
│   │   ├── skills/
│   │   │   ├── configure_reviews/SKILL.md
│   │   │   ├── deepplan/SKILL.md
│   │   │   ├── deepreviews/SKILL.md
│   │   │   ├── deepwork/SKILL.md
│   │   │   ├── deepschema/SKILL.md
│   │   │   ├── new_user/SKILL.md
│   │   │   ├── record/SKILL.md
│   │   │   └── review/SKILL.md
│   │   ├── hooks/              # hooks.json, post_commit_reminder.sh, post_compact.sh, startup_context.sh, deepschema_write.sh
│   │   └── .mcp.json           # MCP server config
│   └── gemini/                 # Gemini CLI extension
│       └── skills/deepwork/SKILL.md
├── library/jobs/               # Reusable example jobs
├── tests/                      # Test suite
├── doc/                        # Documentation
├── pyproject.toml
└── README.md
```

## DeepWork CLI Components

The CLI has five active commands: `serve`, `hook`, `review`, `jobs`, and `setup`. Deprecated back-compat commands `install` and `sync` are also registered (hidden) to guide users toward the plugin system.

### 1. Serve Command (`serve.py`)

Starts the MCP server for workflow management:

```bash
deepwork serve --path .
```

The serve command:
- Creates `.deepwork/tmp/` lazily for session state
- Launches the FastMCP server (stdio or SSE transport)
- No config file required — works out of the box

### 2. Hook Command (`hook.py`)

Runs hook scripts by name, used by platform hook wrappers:

```bash
deepwork hook my_hook
```

### 3. Review Command (`review.py`)

Generates review instructions for changed files based on `.deepreview` config files:

```bash
deepwork review --instructions-for claude
```

The review command:
- Discovers `.deepreview` files throughout the project tree
- Discovers DeepSchemas and generates synthetic review rules from them
- Detects changed files via `git diff` against the default branch, plus untracked files via `git ls-files`
- Matches changed files against rules using include/exclude glob patterns
- Groups files by review strategy (`individual`, `matches_together`, `all_changed_files`)
- Generates per-task instruction files in `.deepwork/tmp/review_instructions/`
- Outputs structured text for Claude Code to dispatch parallel review agents

### 4. Jobs Command (`jobs.py`)

Provides subcommands for inspecting active workflow sessions:

```bash
deepwork jobs get-stack --path .
```

The `get-stack` subcommand:
- Reads session files from `.deepwork/tmp/`
- Filters for active sessions only
- Enriches each session with job definition context (common info, step instructions, step position)
- Outputs JSON to stdout — used by the post-compaction hook to restore workflow context

### 5. Setup Command (`setup.py`)

Configures the current environment for DeepWork by detecting installed AI agent platforms and updating their settings:

```bash
deepwork setup
```

The setup command:
- Detects Claude Code by checking for `~/.claude` directory
- Configures `~/.claude/settings.json` with marketplace, plugin, MCP permissions, auto-update, and project-root-relative `Read`/`Write`/`Edit` permissions for `/.deepwork/**/*` (applies to every project)
- Idempotent — safe to run multiple times
- Preserves existing settings

### 6. Plugin System (replaces adapters/detector/generator)

Platform-specific delivery is now handled by plugins in `plugins/`:

- **Claude Code**: `plugins/claude/` — installed as a Claude Code plugin via marketplace
- **Gemini CLI**: `plugins/gemini/` — skill files copied to `.gemini/skills/`

Each plugin contains static files (skill, hooks, MCP config) rather than generated content. The shared skill body lives in `platform/skill-body.md` as the single source of truth.

---

# Part 2: Target Project Architecture

This section describes what a project looks like after the DeepWork plugin is installed.

## Target Project Structure

```
my-project/                     # User's project (target)
├── .git/
├── .deepwork/                  # DeepWork runtime data
│   ├── .gitignore              # Ignores tmp/ directory
│   ├── tmp/                    # Temporary session state (gitignored, created lazily)
│   └── jobs/                   # Job definitions
│       ├── deepwork_jobs/      # Core job (auto-discovered from package)
│       │   └── job.yml
│       ├── competitive_research/
│       │   └── job.yml         # Job definition (steps are inline)
│       └── ad_campaign/
│           └── job.yml
├── (rest of user's project files)
└── README.md
```

**Note**: The plugin provides the `/deepwork` skill, MCP server config, and hooks. No config.yml needed.

**Note**: Work outputs are created directly in the project on dedicated Git branches (e.g., `deepwork/competitive_research-acme-2026-01-11`). The branch naming convention is `deepwork/[job_name]-[instance]-[date]`.

## Job Definition Format

Job definitions use `step_arguments` to declare data that flows between steps, and `workflows` to define step sequences with inline instructions. There are no separate step instruction files, no root-level `steps[]`, and no `version`, `dependencies`, `hooks`, or `exposed/hidden` fields.

### Key Concepts

- **`step_arguments`**: Named data items (strings or file paths) passed between steps. Each argument has a `name`, `description`, `type` (`string` or `file_path`), optional `review` block, and optional `json_schema`.
- **`workflows`**: Named sequences of steps with inline instructions. Each workflow has a `summary`, optional `agent`, optional `common_job_info_provided_to_all_steps_at_runtime`, `steps`, and optional `post_workflow_instructions`.
- **Steps**: Each step has `inputs` and `outputs` that reference `step_arguments` by name. Step logic is defined via `instructions` (inline string) or `sub_workflow` (delegates to another workflow).
- **Reviews on outputs**: The `review` block on step arguments or step outputs uses the same format as `.deepreview` review rules. These are applied *in addition to* any `.deepreview` file-defined rules.
- **`process_requirements`**: Optional per-step object where keys are requirement names and values are requirement statements using RFC 2119 keywords (MUST, SHOULD, MAY, etc.). These review the *process and work* done (not individual output files).

### Example: `job.yml`

`.deepwork/jobs/competitive_research/job.yml`:

```yaml
name: competitive_research
summary: "Systematic competitive analysis workflow"

step_arguments:
  - name: market_segment
    description: "The market segment to analyze"
    type: string
  - name: competitors_list
    description: "List of competitors with descriptions"
    type: file_path
    review:
      instructions: "Verify at least 5 direct and 3 indirect competitors are listed with descriptions."
      strategy: individual
  - name: primary_findings
    description: "Primary research findings document"
    type: file_path
  - name: secondary_findings
    description: "Secondary research findings document"
    type: file_path
  - name: comparison_matrix
    description: "Detailed comparison matrix"
    type: file_path
  - name: positioning_strategy
    description: "Market positioning strategy"
    type: file_path

workflows:
  full_analysis:
    summary: "Complete competitive analysis from identification through positioning"
    common_job_info_provided_to_all_steps_at_runtime: |
      A comprehensive workflow for analyzing competitors in your market segment.
      Designed for product teams conducting quarterly competitive analysis.
    steps:
      - name: identify_competitors
        instructions: |
          Research and list direct and indirect competitors in the given market segment.
          Create a document listing 5-10 direct competitors and 3-5 indirect competitors,
          each with website, description, and value proposition.
        inputs:
          market_segment:
            required: true
        outputs:
          competitors_list:
            required: true
        process_requirements:
          research_thoroughness: "Research MUST use multiple sources (web search, analyst reports, review sites)"

      - name: primary_research
        instructions: |
          Analyze each competitor's self-presentation: website messaging, product pages,
          pricing, and positioning. Document findings for each competitor.
        inputs:
          competitors_list:
            required: true
        outputs:
          primary_findings:
            required: true

      - name: secondary_research
        instructions: |
          Research third-party perspectives on competitors: analyst reports, reviews,
          press coverage, and community sentiment.
        inputs:
          competitors_list:
            required: true
          primary_findings:
            required: true
        outputs:
          secondary_findings:
            required: true

      - name: comparative_report
        instructions: |
          Create a detailed comparison matrix and strengths/weaknesses analysis
          based on all research gathered.
        inputs:
          primary_findings:
            required: true
          secondary_findings:
            required: true
        outputs:
          comparison_matrix:
            required: true

      - name: positioning
        instructions: |
          Define a positioning strategy based on the competitive landscape analysis.
        inputs:
          comparison_matrix:
            required: true
        outputs:
          positioning_strategy:
            required: true

    post_workflow_instructions: |
      The competitive analysis is complete. Create a PR with all artifacts
      for team review.
```

### Sub-Workflow References

Steps can delegate to other workflows instead of providing inline instructions:

```yaml
steps:
  - name: run_deep_analysis
    sub_workflow:
      workflow_name: deep_analysis
      workflow_job: competitive_research  # optional, defaults to current job
    inputs:
      competitors_list:
        required: true
    outputs:
      primary_findings:
        required: true
```

## Workflow Execution via MCP

When a job is defined, the MCP server discovers it at runtime from `.deepwork/jobs/`. Steps are executed via MCP tool calls rather than individual skill files.


# Part 3: Runtime Execution Model

This section describes how AI agents (like Claude Code) actually execute jobs using the installed skills.

## Execution Flow

### User Workflow

1. **Install Plugin** (one-time):
   ```
   # In Claude Code
   claude plugin marketplace add Unsupervisedcom/deepwork
   claude plugin install deepwork@deepwork-plugins
   ```

2. **Define a Job** (once per job type):
   ```
   # In Claude Code
   User: /deepwork Make a competitive research workflow

   Claude: [Calls get_workflows, finds deepwork_jobs/new_job]
          [Calls start_workflow to begin the new_job workflow]
          [Guides through interactive dialog to define steps]

          ✓ Job 'competitive_research' created
          new_job workflow complete.
   ```

3. **Execute a Job Instance** (each time you need to do the work):
   ```
   # In Claude Code
   User: /deepwork competitive_research

   Claude: [Calls start_workflow for competitive_research]
          Starting competitive research job...
          Created branch: deepwork/competitive_research-acme-2026-01-11

          [Follows step instructions, creates output files]
          [Calls finished_step after each step]
          [Continues through all steps until workflow_complete]
   ```

4. **Complete and Merge**:
   ```
   User: Looks great! Create a PR for this work

   Claude: [Creates PR from deepwork/competitive_research-acme-2026-01-11 to main]
          PR created: https://github.com/user/project/pull/123
   ```

## How Agents Execute Workflows

Agents use the `/deepwork` skill which instructs them to interact with MCP tools:

1. **Workflow Discovery**: Agent calls `get_workflows` to list available jobs and workflows
2. **Workflow Start**: Agent calls `start_workflow` with goal, job name, workflow name, and optional inputs
3. **Step Execution**: Agent follows the inline instructions returned by the MCP server
4. **Checkpoint**: Agent calls `finished_step` with outputs and work summary
5. **Quality Gate**: MCP server runs DeepWork Reviews on outputs, returns feedback or advances
6. **Repeat**: Agent continues until `workflow_complete`

All state is managed by the MCP server in `.deepwork/tmp/sessions/`. The agent never reads session files directly.

## Context Passing Between Steps

### 1. Filesystem (Primary Mechanism)

On a work branch like `deepwork/competitive_research-acme-2026-01-11`, outputs are created in the project. Step arguments with `type: file_path` reference files on disk; `type: string` values are passed inline through the MCP server.

### 2. Step Instructions

Each step's instructions (inline in job.yml) describe what inputs to read and what outputs to produce. The MCP server automatically includes input values/references when returning step instructions.

### 3. Git History

When working on similar jobs, agents can read old branches from git history to use as templates for style, depth, and format.

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

DeepWork includes a built-in job called `deepwork_jobs` for managing jobs. It provides:

**Workflows** (multi-step sequences):
- **`new_job`** workflow: `define` → `implement` → `test` → `iterate`
  - Creates complete job definitions through interactive Q&A, implementation, testing, and refinement
- **`repair`** workflow: `fix_settings` → `fix_jobs` → `errata`
  - Cleans up and migrates DeepWork configurations from prior versions
- **`learn`** workflow: `learn`
  - Analyzes conversation history to improve job instructions, capture learnings, and create preventive automation (DeepSchemas and DeepReview rules)

These are auto-discovered at runtime by the MCP server from the Python package.

### Standard Job: `deepwork_reviews`

DeepWork includes a built-in job called `deepwork_reviews` for managing `.deepreview` rules. It provides:

**Workflows**:
- **`discover_rules`** workflow: `add_deepwork_native_reviews` → `migrate_existing_skills` → `add_documentation_rules` → `add_language_reviews`
  - Sets up a complete suite of `.deepreview` rules for a project
- **`add_document_update_rule`** workflow: `analyze_dependencies` → `apply_rule`
  - Adds a review rule to keep a specific documentation file up-to-date when related source files change

### Standard Job: `deepplan`

DeepWork includes a built-in job called `deepplan` for structured planning. This job is only used when the agent is in planning mode — the startup context hook injects a trigger that auto-starts the `create_deep_plan` workflow when plan mode begins. The workflow produces a validated, executable DeepWork job definition.

**Workflows**:
- **`create_deep_plan`** workflow: `initial_understanding` → `design_alternatives` → `review_and_synthesize` → `enrich_the_plan` → `present_plan`
  - Guides agents through structured planning: exploring the codebase, generating competing designs, synthesizing a plan, enriching it into an executable session job via `register_session_job`, and presenting for user approval

### Library Job: `engineer`

The `engineer` job lives in `library/jobs/engineer/` and is available for users to adopt. It provides domain-agnostic engineering execution:

**Workflows**:
- **`implement`** workflow: `translate_issue` → `initialize_branch` → `red_tests` → `green_implementation` → `finalize_pr` → `product_sync`
  - Drives engineering work from product issue through PR merge with TDD discipline, PR synchronization, and product traceability
- **`doctor`** workflow: `check_agent_md` → `check_context` → `doctor_report`
  - Validates that agent.md and domain context files are present, linked, and valid

The job is domain-agnostic — its `common_job_info` includes a domain adaptation table for software, hardware/CAD, firmware, and documentation projects that step instructions reference. An RFC 2119 requirements specification is bundled as `requirements.md`.

### MCP-Based Workflow Execution

Users invoke workflows through the `/deepwork` skill, which uses MCP tools:

1. `get_workflows` — discovers available workflows from all jobs
2. `start_workflow` — begins a workflow session, creates a git branch, returns first step instructions
3. `finished_step` — submits step outputs for quality review, returns next step or completion
4. `abort_workflow` — cancels the current workflow if it cannot be completed
5. `go_to_step` — navigates back to a prior step, clearing progress from that step onward

**Example: Creating a New Job**
```
User: /deepwork new_job

→ MCP: start_workflow(job_name="deepwork_jobs", workflow_name="new_job")
→ Step 1 (define): Interactive Q&A to create job.yml
→ Step 2 (implement): Generate step instruction files
→ Step 3 (test): Run the workflow on a real use case
→ Step 4 (iterate): Refine based on test results
```

### The `learn` Workflow

Analyzes conversation history to improve job instructions, capture learnings, and create preventive automation:

```
User: /deepwork_jobs.learn

Claude: I'll analyze this conversation for DeepWork job executions...
        Found: competitive_research job was executed

        Identified issues:
        1. Step 2 instructions unclear about source prioritization
        2. Output format for competitor_profiles/ not specified

        Improvements made:
        ✓ Updated job.yml step instructions with source prioritization guidance
        ✓ Added output format example to primary_research step instructions

        Bespoke learnings captured:
        ✓ Created AGENTS.md with project-specific notes about this competitive research instance

        Prevention opportunities evaluated:
        ✓ Created DeepSchema for competitor_profiles/ output format
        ✓ Added DeepReview rule to enforce source prioritization in research steps

        Job instructions updated in place. Changes take effect on next workflow run.
```

This standalone skill can be run anytime after executing a job to capture learnings, improve instructions, and create preventive automation (DeepSchemas and DeepReview rules).

### Step Instructions at Runtime

When `start_workflow` or `finished_step` returns step instructions to the agent, the MCP server assembles them from the job definition:

- **Common job info**: The `common_job_info_provided_to_all_steps_at_runtime` block from the workflow
- **Inline instructions**: The `instructions` string from the step definition
- **Inputs**: The values/file paths for all declared step inputs, resolved from previous step outputs
- **Expected outputs**: The list of outputs the step must produce, with descriptions from `step_arguments`

There is no separate template engine or Jinja2 rendering. Instructions are composed directly from the job.yml data at runtime.

---

## Testing Framework and Strategy

### Test Architecture

```
tests/
├── unit/                       # Unit tests for core components
│   ├── jobs/
│   │   ├── test_parser.py      # Job parser and dataclasses
│   │   ├── test_discovery.py   # Job folder discovery
│   │   ├── test_deepplan.py    # DeepPlan job definition tests
│   │   └── mcp/
│   │       ├── test_tools.py          # MCP tool implementations
│   │       ├── test_state.py          # State management
│   │       ├── test_quality_gate.py   # Quality gate (DeepWork Reviews)
│   │       ├── test_schemas.py        # Pydantic models
│   │       ├── test_server.py         # Server creation
│   │       ├── test_session_jobs.py   # Session job registration
│   │       └── test_async_interface.py
│   ├── cli/
│   │   └── test_jobs_get_stack.py
│   ├── review/                 # DeepWork Reviews tests
│   └── test_validation.py      # Schema validation
├── integration/                # Integration tests
│   └── test_quality_gate_integration.py
├── e2e/                        # End-to-end tests
│   └── test_claude_code_integration.py
└── fixtures/                   # Test data
    └── jobs/
        ├── simple_job/
        ├── complex_job/
        ├── fruits/
        └── job_with_doc_spec/
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

Reference doc specs in job.yml step arguments:

```yaml
step_arguments:
  - name: monthly_spending_report
    description: "Monthly AWS spending report"
    type: file_path
    json_schema: .deepwork/doc_specs/monthly_aws_report_schema.json
    review:
      instructions: "Verify the report meets the doc spec quality criteria."
```

### How Doc Specs Are Used at Runtime

When the MCP server loads a job with doc spec-referenced outputs, the step instructions include:
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
3. Evaluates prevention opportunities and creates DeepSchemas and DeepReview rules

See `doc/doc-specs.md` for complete documentation.

---

## Technical Decisions

### Language: Python 3.11+
- **Rationale**: Proven ecosystem for CLI tools (click) and MCP servers (FastMCP)
- **Alternatives**: TypeScript (more verbose), Go (less flexible)
- **Runtime Dependencies**: PyYAML (config), Click (CLI), FastMCP (MCP server), jsonschema (validation), Pydantic (data models), mcp (protocol), aiofiles (async file I/O)

### Distribution: uv/pipx
- **Rationale**: Modern Python tooling, fast, isolated environments
- **Alternatives**: pip (global pollution), Docker (heavyweight for CLI)

### State Storage: Filesystem + Git
- **Rationale**: Transparent, auditable, reviewable, collaborative
- **Alternatives**: Database (opaque), JSON files (no versioning)

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

---

# Part 4: MCP Server Architecture

DeepWork includes an MCP (Model Context Protocol) server that provides an alternative execution model. Instead of relying solely on skill files with embedded instructions, the MCP server guides agents through workflows via checkpoint calls with quality gate enforcement.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   Claude Code / AI Agent                     │
│  /deepwork skill → instructs to use MCP tools               │
└─────────────────────────────────────────────────────────────┘
                              │ MCP Protocol (stdio)
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   DeepWork MCP Server                        │
│  Tools: get_workflows | start_workflow | finished_step |    │
│         abort_workflow | go_to_step | review tools          │
│  State: session tracking, step progress, outputs            │
│  Quality Gate: invokes review agent for validation          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              .deepwork/jobs/[job_name]/job.yml              │
└─────────────────────────────────────────────────────────────┘
```

## MCP Server Components

All MCP server code lives in `src/deepwork/jobs/mcp/`.

### Server (`jobs/mcp/server.py`)

The FastMCP server definition that:
- Creates and configures the MCP server instance
- Registers the workflow tools, review tools (`get_review_instructions`, `get_configured_reviews`, `mark_review_as_passed`), DeepSchema tools (`get_named_schemas`), and session job tools (`register_session_job`, `get_session_job`)
- Detects job definition issues at startup via `issues.py` and appends warnings to tool responses
- Provides server instructions for agents

### Tools (`jobs/mcp/tools.py`)

Implements the workflow MCP tools:

#### 1. `get_workflows`
Lists all available workflows from `.deepwork/jobs/`.

**Parameters**: None

**Returns**: List of jobs with their workflows, steps, and summaries. Each `WorkflowInfo` includes a `how_to_invoke` field with invocation instructions: when the workflow's `agent` field is set in job.yml, it directs callers to delegate via the Task tool; otherwise, it directs callers to use the `start_workflow` MCP tool directly.

#### 2. `start_workflow`
Begins a new workflow session.

**Parameters**:
- `goal: str` - What the user wants to accomplish
- `job_name: str` - Name of the job
- `workflow_name: str` - Name of the workflow within the job
- `inputs: dict[str, str | list[str]] | None` - Inputs for the first step (file paths for `file_path` type, strings for `string` type)
- `session_id: str | None` - Session identifier. Required on Claude Code (`CLAUDE_CODE_SESSION_ID`); auto-generated on other platforms
- `agent_id: str | None` - Claude Code agent ID for sub-agent scoping

**Returns**: First step info (`ActiveStepInfo`) with resolved inputs, workflow stack

#### 3. `finished_step`
Reports step completion and gets next instructions.

**Parameters**:
- `outputs: dict[str, str | list[str]]` - Map of output names to file path(s) or string values
- `work_summary: str | None` - Summary of the work done in the step
- `quality_review_override_reason: str | None` - If provided, skips quality review
- `session_id: str` - Session identifier from `begin_step.session_id` returned by `start_workflow`
- `agent_id: str | None` - Claude Code agent ID for sub-agent scoping

**Returns**:
- `status: "needs_work" | "next_step" | "workflow_complete"`
- If `needs_work`: feedback from failed quality reviews with issues to fix
- If `next_step`: next step instructions (with resolved inputs)
- If `workflow_complete`: summary of all outputs, plus `post_workflow_instructions` from the workflow definition

#### 4. `abort_workflow`
Aborts the current workflow and returns to the parent (if nested).

**Parameters**:
- `explanation: str` - Why the workflow is being aborted
- `session_id: str` - Session identifier from `begin_step.session_id` returned by `start_workflow`
- `agent_id: str | None` - Claude Code agent ID for sub-agent scoping

**Returns**: Aborted workflow info, resumed parent info (if any), current stack

#### 5. `go_to_step`
Navigates back to a prior step, clearing progress from that step onward.

**Parameters**:
- `step_id: str` - ID of the step to navigate back to
- `session_id: str` - Session identifier from `begin_step.session_id` returned by `start_workflow`
- `agent_id: str | None` - Claude Code agent ID for sub-agent scoping

**Returns**: `begin_step` (step info for the target step), `invalidated_steps` (step IDs whose progress was cleared), `stack` (current workflow stack)

**Behavior**:
- Validates the target step exists in the workflow
- Rejects forward navigation (target step index > current step index)
- Clears session tracking state for all steps from target onward (files on disk are not deleted)
- Marks the target step as started

#### 6. `get_review_instructions`
Runs the `.deepreview`-based code review pipeline. Registered directly in `jobs/mcp/server.py` (not in `tools.py`) since it operates outside the workflow lifecycle.

**Parameters**:
- `files: list[str] | None` - Explicit files to review. When omitted, detects changes via git diff.

**Returns**: Formatted review task list or informational message.

The `--platform` CLI option on `serve` controls which formatter is used (defaults to `"claude"`).

#### 7. `get_configured_reviews`
Lists configured review rules from `.deepreview` files and DeepSchema-generated synthetic rules without running the pipeline. When `only_rules_matching_files` is provided, catch-all rules (include patterns composed solely of `*`/`/`, e.g. `**/*`) are excluded.

**Parameters**:
- `only_rules_matching_files: list[str] | None` - Filter to rules matching these files.

**Returns**: List of rule summaries (name, description, defining_file).

#### 8. `mark_review_as_passed`
Marks a review as passed so it is skipped on subsequent runs while the reviewed files remain unchanged. Part of the **review pass caching** mechanism.

**Parameters**:
- `review_id: str` - The deterministic review ID from the instruction file's "After Review" section.

**Returns**: Confirmation string or validation error.

#### 9. `get_named_schemas`
Lists all named DeepSchemas discovered across all schema sources (project-local, standard, and env var). Returns each schema's name, summary, and matcher patterns.

**Parameters**: None.

**Returns**: List of `{name, summary, matchers}` dicts.

#### 10. `register_session_job`
Register a transient job definition scoped to the current session. Validates against the job schema and stores it so `start_workflow` can discover it. Can be called multiple times to overwrite.

**Parameters**: `job_name` (string), `job_definition_yaml` (string), `session_id` (string).

**Returns**: `{status, job_name, job_dir, message}` on success, `{error}` on validation failure.

#### 11. `get_session_job`
Retrieve the YAML content of a session-scoped job definition previously registered with `register_session_job`.

**Parameters**: `job_name` (string), `session_id` (string).

**Returns**: `{job_name, job_definition_yaml}`.

### Review Pass Caching

Each review task is assigned a deterministic `review_id` encoding the rule name, file paths, and a SHA-256 content hash (first 12 hex chars). When `get_review_instructions` generates instruction files, it names them `{review_id}.md` and checks for a corresponding `{review_id}.passed` marker. If the marker exists, the review is skipped.

After a review passes, the reviewing agent calls `mark_review_as_passed` with the `review_id` (included in the instruction file's "After Review" section). This creates the `.passed` marker in `.deepwork/tmp/review_instructions/`. When file contents change, the content hash changes, producing a new `review_id` with no matching marker — so the review runs again automatically.

Cleanup between runs deletes stale `.md` files (those without a corresponding `.passed` marker), preserving both `.passed` markers and their associated `.md` files across runs.

### State Management (`jobs/mcp/state.py`)

Manages workflow session state persisted to `.deepwork/tmp/sessions/<platform>/session-<id>/state.json`. Sub-agents get isolated stacks in `agent_<agent_id>.json` alongside the main state file.

```python
class StateManager:
    def __init__(self, project_root: Path, platform: str)
    async def create_session(session_id, ..., agent_id=None) -> WorkflowSession
    def resolve_session(session_id, agent_id=None) -> WorkflowSession
    async def start_step(session_id, step_id, agent_id=None) -> None
    async def complete_step(session_id, step_id, outputs, work_summary, agent_id=None) -> None
    async def advance_to_step(session_id, step_id, step_index, agent_id=None) -> None
    async def go_to_step(session_id, step_id, step_index, invalidate_step_ids, agent_id=None) -> None
    async def complete_workflow(session_id, agent_id=None) -> None
    async def abort_workflow(session_id, explanation, agent_id=None) -> tuple
    async def record_quality_attempt(session_id, step_id, agent_id=None) -> int
    def get_all_outputs(session_id, agent_id=None) -> dict
    def get_stack(session_id, agent_id=None) -> list[StackEntry]
    def get_stack_depth(session_id, agent_id=None) -> int
    def get_all_session_data(session_id) -> dict[agent_id, (active_stack, completed_workflows)]
```

Session state includes:
- Session ID and timestamps
- Job/workflow/instance identification
- Current step and step index
- Per-step progress (started_at, completed_at, outputs, work_summary, quality_attempts)

### Quality Gate (`jobs/mcp/quality_gate.py`)

The quality gate integrates with the DeepWork Reviews infrastructure rather than invoking a separate Claude CLI subprocess. When `finished_step` is called:

1. **JSON schema validation**: If a `json_schema` is defined for any file argument, the output file is validated against it first. Validation errors cause immediate failure before any reviews run.

2. **Build dynamic review rules**: For each `review` block defined on step outputs (either inline on the step or on the `step_argument`), a `ReviewRule` object is constructed dynamically. The `common_job_info_provided_to_all_steps_at_runtime` is included in review instructions for context.

3. **Process requirements**: If the step defines `process_requirements`, a review is created that evaluates the `work_summary` against those requirements using RFC 2119 semantics. MUST/SHALL violations cause failure; SHOULD/RECOMMENDED violations fail only if easily achievable; other requirements produce feedback without failure.

4. **Merge with `.deepreview` rules**: `.deepreview` file-defined rules and DeepSchema-generated synthetic rules are matched against output files that are *actually changed* (via git diff). Output files that were provided as unchanged references are excluded from `.deepreview` matching. Dynamic rules (from step output `review` blocks) still run against all output files regardless of git status.

5. **Apply review strategies**: Review strategies (`individual`, `matches_together`, etc.) work normally on the merged rule set.

6. **Honor pass caching**: Reviews that have already passed (via `mark_review_as_passed`) are skipped.

7. **Return review instructions**: If there are reviews to run, they are returned to the agent in the same format as the `/review` skill, along with instructions on how to run them and call `mark_review_as_passed` or fix issues. The agent then runs reviews itself until all pass.

### Status Writer (`jobs/mcp/status.py`)

Writes file-based status projections for external consumers (UIs, dashboards, monitoring). Status files are written to `.deepwork/tmp/status/v1/` and are a **stable external interface** — the file format must not change without versioning.

```python
class StatusWriter:
    def __init__(self, project_root: Path)

    def write_manifest(self, jobs: list[JobDefinition]) -> None
        """Write job_manifest.yml with all available jobs, workflows, and steps."""

    def write_session_status(self, session_id: str, state_manager: StateManager, job_loader: Callable) -> None
        """Write sessions/<session_id>.yml from current state."""
```

**Output files:**
- `job_manifest.yml` — catalog of all jobs/workflows/steps, sorted alphabetically
- `sessions/<session_id>.yml` — per-session workflow execution status including active workflow, step history, and completed/aborted workflows

**Write triggers:**
- Manifest: MCP server startup, `get_workflows`
- Session status: `start_workflow`, `finished_step`, `go_to_step`, `abort_workflow`

Status writes are fire-and-forget: failures are logged as warnings and never fail the MCP tool call.

### Schemas (`jobs/mcp/schemas.py`)

Pydantic models for all tool inputs and outputs:
- `StartWorkflowInput`, `FinishedStepInput`, `AbortWorkflowInput`, `GoToStepInput`, `RegisterSessionJobInput`, `GetSessionJobInput`
- `GetWorkflowsResponse`, `StartWorkflowResponse`, `FinishedStepResponse`, `AbortWorkflowResponse`, `GoToStepResponse`
- `ActiveStepInfo`, `StepInputInfo`, `ExpectedOutput`, `StackEntry`
- `JobInfo`, `WorkflowInfo`, `JobLoadErrorInfo`
- `WorkflowSession`, `StepProgress`, `StepHistoryEntry`

### Parser Dataclasses (`jobs/parser.py`)

The parser produces these dataclasses from `job.yml`:
- `ReviewBlock` - Review instructions (same format as `.deepreview` rules)
- `StepArgument` - Named data item with type, description, optional review and json_schema
- `StepInputRef` - Reference to a step argument as an input (with `required` flag)
- `StepOutputRef` - Reference to a step argument as an output (with `required` flag, optional `review`)
- `SubWorkflowRef` - Reference to another workflow (with `workflow_name`, optional `workflow_job`)
- `WorkflowStep` - A step within a workflow (name, instructions or sub_workflow, inputs, outputs, process_requirements)

## MCP Server Registration

The plugin's `.mcp.json` registers the MCP server automatically:

```json
{
  "mcpServers": {
    "deepwork": {
      "command": "uvx",
      "args": ["deepwork", "serve", "--path", ".", "--platform", "claude"]
    }
  }
}
```

## The `/deepwork` Skill

The plugin provides a skill (`plugins/claude/skills/deepwork/SKILL.md`) that instructs agents to use MCP tools:

```markdown
# DeepWork Workflow Manager

Execute multi-step workflows with quality gate checkpoints.

## Quick Start
1. Discover workflows: Call `get_workflows`
2. Start a workflow: Call `start_workflow` with your goal
3. Execute steps: Follow the instructions returned
4. Checkpoint: Call `finished_step` with your outputs
5. Iterate or continue: Handle needs_work, next_step, or workflow_complete
```

## MCP Execution Flow

1. **User invokes `/deepwork`**
   - Agent calls `get_workflows` to discover available workflows
   - Parses user intent to identify target workflow

2. **Agent calls `start_workflow`**
   - MCP server creates session, generates branch name
   - Returns first step instructions with resolved inputs and expected outputs

3. **Agent executes step**
   - Follows inline step instructions
   - Creates output files / produces string values

4. **Agent calls `finished_step`**
   - MCP server validates outputs, runs json_schema checks, then runs DeepWork Reviews
   - If `needs_work`: returns feedback from failed quality reviews with issues to fix
   - If `next_step`: returns next step instructions with resolved inputs
   - If `workflow_complete`: returns summary and `post_workflow_instructions`

5. **Loop continues until workflow complete**

## Serve Command

Start the MCP server manually:

```bash
# Basic usage
deepwork serve

# For a specific project
deepwork serve --path /path/to/project

# SSE transport (for remote)
deepwork serve --transport sse --port 8000
```

## Benefits of MCP Approach

1. **Centralized state**: Session state persisted and visible in `.deepwork/tmp/`
2. **Quality gates**: Automated validation before proceeding
3. **Structured checkpoints**: Clear handoff points between steps
4. **Resumability**: Sessions can be loaded and resumed
5. **Observability**: All state changes logged and inspectable

---

## References

- [Spec-Kit Repository](https://github.com/github/spec-kit)
- [Spec-Driven Development Methodology](https://github.com/github/spec-kit/blob/main/spec-driven.md)
- [Claude Code Documentation](https://claude.com/claude-code)
- [Git Workflows](https://www.atlassian.com/git/tutorials/comparing-workflows)
- [JSON Schema](https://json-schema.org/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)

