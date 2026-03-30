# Shared Jobs

DeepWork includes a library of reusable jobs that any project can adopt. These are pre-built, multi-step workflows covering common tasks like research, repository setup, platform engineering, and spec-driven development.

## Enabling Shared Jobs

The fastest way to add shared jobs to your project is with the `/deepwork` skill:

```
/deepwork shared_jobs
```

This walks you through configuring `DEEPWORK_ADDITIONAL_JOBS_FOLDERS` so the DeepWork plugin discovers library jobs at runtime alongside your local jobs. By default, jobs are referenced in-place from a checkout of the DeepWork repo, so you always get the latest version, though you can still copy them into your project when you want to customize them.

## Available Jobs

| Job | Description |
|-----|-------------|
| [Engineer](./engineer) | Domain-agnostic engineering execution from product issue through PR merge and product sync, with TDD discipline |
| [Mech Engineer](./mech_engineer) | Design mechanical assemblies and parts with OTS sourcing, manufacturing method recommendations, BOM generation, and multi-scale production evaluation |
| [Research](./research) | Multi-workflow research suite — deep investigation, quick summaries, material ingestion, and reproduction planning |
| [Platform Engineer](./platform_engineer) | Incident response, observability, CI/CD, releases, security, cost management, and infrastructure |
| [Repo](./repo) | Audit and configure repositories — labels, branch protection, milestones, and boards |
| [Spec-Driven Development](./spec_driven_development) | Build features through executable specifications: constitution, specify, clarify, plan, tasks, implement |

## How It Works

Shared jobs are stored in the `library/jobs/` directory of the DeepWork repository. When you run the `shared_jobs` workflow, it:

1. **Detects your setup** — checks for an existing local DeepWork checkout or sparse clone
2. **Configures the source** — sets up a sparse checkout in `.deepwork/upstream/` or points to an existing local clone
3. **Sets the environment variable** — adds `DEEPWORK_ADDITIONAL_JOBS_FOLDERS` to your `flake.nix` shellHook (or shell profile)
4. **Discovers jobs** — library jobs appear in `/deepwork` alongside your local and standard jobs

## Creating Slash Commands for Jobs

You can ask Claude to turn any job workflow into a slash command for quicker access. The easiest way is a one-liner from your terminal:

```bash
claude "Create a /research slash command from the deepwork research job with subcommands for each workflow"
```

Claude will create skill files under `.claude/skills/` so you can invoke workflows directly:

```
/research              # runs research (deep) workflow
/research deep         # runs research (deep) workflow
/research quick        # runs research (quick) workflow
```

You can also use dot notation for the skill name — `/research.deep` and `/research.quick` — which creates separate skill files for each workflow.

### Why slash commands aren't created automatically

DeepWork does not auto-generate slash commands for every job and workflow. Each slash command becomes a **skill** that is loaded into the agent's context — both for the user and for any sub-agents that spawn during a session. Auto-generating commands for every workflow across every installed job would flood the skill list, increasing token usage and making it harder for agents to select the right tool. Instead, users create slash commands only for the workflows they actually use frequently, keeping the skill surface lean and intentional.

## Purpose

The job library provides:

- **Ready-to-use workflows**: Start using proven multi-step workflows immediately
- **Templates**: Copy and adapt jobs for your own use cases
- **Learning**: Understand the job definition format through real examples

## Structure

Each job in this library follows the same structure as the `.deepwork/jobs` subfolders in your local project:

```
library/jobs/
├── .deepreview              # Review rules for library job quality
├── README.md
├── engineer/                # Domain-agnostic engineering execution (TDD, PR lifecycle)
│   ├── job.yml
│   ├── AGENTS.md
│   ├── requirements.md
│   └── steps/
├── mech_engineer/           # Mechanical assembly and part design workflows
│   ├── job.yml
│   ├── AGENTS.md
│   └── steps/
├── platform_engineer/       # Platform engineering workflows
│   ├── job.yml
│   ├── AGENTS.md            # Agent context and learnings
│   ├── conventions.md       # RFC 2119 platform engineering standards
│   ├── readme.md
│   ├── steps/               # Step instruction files
│   └── templates/           # Output templates
├── repo/
│   ├── job.yml              # Job definition (name, steps, workflows)
│   ├── readme.md            # Job-specific documentation
│   └── steps/
│       ├── detect_platform.md
│       ├── ensure_labels.md
│       ├── check_branch_protection.md
│       ├── check_milestones.md
│       ├── check_boards.md
│       ├── setup_report.md
│       ├── audit_labels.md
│       ├── audit_branch_protection.md
│       ├── audit_milestones.md
│       ├── audit_boards.md
│       └── doctor_report.md
├── research/
│   ├── job.yml              # Job definition (name, steps, workflows)
│   ├── readme.md            # Job-specific documentation
│   ├── AGENTS.md            # Agent context and learnings
│   └── steps/
│       ├── scope.md
│       ├── choose_platforms.md
│       ├── gather.md
│       ├── gather_quick.md
│       ├── synthesize.md
│       ├── summarize.md
│       ├── report.md
│       ├── parse.md
│       ├── file.md
│       ├── ingest_material.md
│       ├── analyze.md
│       └── plan.md
└── spec_driven_development/
    ├── job.yml              # Job definition (name, steps, workflows)
    ├── readme.md            # Job-specific documentation
    └── steps/
        ├── constitution.md
        ├── specify.md
        ├── clarify.md
        ├── plan.md
        ├── tasks.md
        └── implement.md
```

### job.yml

The job definition file contains:

- `name`: Unique identifier for the job
- `version`: Semantic version (e.g., "1.0.0")
- `summary`: Brief description (under 200 characters)
- `common_job_info_provided_to_all_steps_at_runtime`: Detailed context provided to all steps at runtime
- `workflows`: Named sequences of steps (optional)
  - `name`: Workflow identifier
  - `summary`: What the workflow accomplishes
  - `steps`: Ordered list of step IDs to execute
- `steps`: Array of step definitions with:
  - `id`: Step identifier
  - `name`: Human-readable step name
  - `description`: What this step accomplishes
  - `hidden`: Whether the step is hidden from direct invocation (optional, default false)
  - `instructions_file`: Path to the step's markdown instructions
  - `inputs`: What the step requires — each input has `name`/`description`, or `file`/`from_step` to reference outputs from prior steps
  - `outputs`: Map of output names to objects with `type` (`file` or `files`), `description`, and `required` fields
  - `dependencies`: Other step IDs that must complete first
  - `reviews`: Quality reviews to run when step completes — array of objects with `run_each` (output name or `step`), `quality_criteria` (map of criterion name to expected state), and optional `additional_review_guidance` (context for the reviewer)

### steps/

Each step has a markdown file with detailed instructions that guide the AI agent through executing that step. These files include:

- Context and goals for the step
- Specific actions to take
- Expected outputs and quality criteria
- Examples of good output

## Using a Job from the Library

1. Browse the jobs in this directory
2. Copy the job folder to your project's `.deepwork/jobs/` directory
3. Run `/deepwork` to start the job — the MCP server will discover it automatically

## Using Library Jobs via Nix Dev Shell

Instead of copying jobs into your project, you can keep them live and up-to-date by cloning the DeepWork repo and pointing your dev shell at its library. This lets you receive upstream improvements and contribute back.

### Setup

1. Clone the DeepWork repo (or a sparse subset — see below) into `.deepwork/upstream/` in your project:

```bash
git clone https://github.com/Unsupervisedcom/deepwork.git .deepwork/upstream
```

2. Add `.deepwork/upstream/` to your `.gitignore`:

```
.deepwork/upstream/
```

3. Set `DEEPWORK_ADDITIONAL_JOBS_FOLDERS` in your `flake.nix` shellHook:

```nix
shellHook = ''
  export REPO_ROOT=$(git rev-parse --show-toplevel)

  # Prefer local deepwork checkout, fall back to existing sparse checkout
  if [ -d "$REPO_ROOT/../deepwork/library/jobs" ]; then
    export DEEPWORK_ADDITIONAL_JOBS_FOLDERS="''${DEEPWORK_ADDITIONAL_JOBS_FOLDERS:+$DEEPWORK_ADDITIONAL_JOBS_FOLDERS:}$REPO_ROOT/../deepwork/library/jobs"
  elif [ -d "$REPO_ROOT/.deepwork/upstream/library/jobs" ]; then
    export DEEPWORK_ADDITIONAL_JOBS_FOLDERS="''${DEEPWORK_ADDITIONAL_JOBS_FOLDERS:+$DEEPWORK_ADDITIONAL_JOBS_FOLDERS:}$REPO_ROOT/.deepwork/upstream/library/jobs"
  else
    echo "DeepWork library jobs not found. Run '/deepwork shared_jobs' to set them up." >&2
  fi
'';
```

Library jobs now appear in `/deepwork` alongside your local and standard jobs.

To initially set up or update the sparse checkout:

```bash
REPO_ROOT="$(git rev-parse --show-toplevel)"
if [ ! -d "$REPO_ROOT/.deepwork/upstream" ]; then
  git clone --sparse --filter=blob:none \
    https://github.com/Unsupervisedcom/deepwork.git \
    "$REPO_ROOT/.deepwork/upstream"
  git -C "$REPO_ROOT/.deepwork/upstream" sparse-checkout set --cone library/jobs/
else
  git -C "$REPO_ROOT/.deepwork/upstream" pull --ff-only
fi
```

### Sparse Checkout (Specific Jobs Only)

If you only need certain library jobs, use a sparse checkout to minimize disk usage:

```bash
# Clone with sparse checkout enabled (downloads minimal data)
git clone --sparse --filter=blob:none \
  https://github.com/Unsupervisedcom/deepwork.git \
  .deepwork/upstream

cd .deepwork/upstream

# Check out only the jobs you need
git sparse-checkout set --cone library/jobs/repo/

# Add more jobs later as needed
git sparse-checkout add library/jobs/spec_driven_development/
```

To update your checkout with the latest upstream changes:

```bash
git -C .deepwork/upstream pull
```

## Contributing Improvements Back

When you use a library job and discover improvements, you can contribute them back upstream.

### The Learn Flow

1. Run the library job in your project as normal
2. Run `/deepwork learn` — the learn step classifies improvements as:
   - **Generalizable**: Improvements that benefit all users (update the library job)
   - **Bespoke**: Improvements specific to your project (update your local `AGENTS.md`)

### Submitting Generalizable Improvements

For improvements classified as generalizable:

1. Create a branch in the upstream checkout:

```bash
cd .deepwork/upstream
git checkout -b improve/repo-job-step-name
```

2. Make your changes to the library job files

3. Run the portability review to ensure your changes are portable:

```bash
# From the upstream checkout
/deepwork:review
```

The `library_job_portability` review rule checks for hardcoded paths, personal information, platform-specific assumptions, and schema compliance. All library job changes must pass this review before submitting a PR.

4. Commit, push, and open a PR:

```bash
git add library/jobs/
git commit -m "feat(library): improve repo job step description"
git push -u origin improve/repo-job-step-name
gh pr create --title "feat(library): improve repo job step description" \
  --body "Description of the improvement and why it benefits all users"
```

## Contributing

To add a job to the library, ensure it follows the structure above and includes clear, actionable instructions in each step file.
